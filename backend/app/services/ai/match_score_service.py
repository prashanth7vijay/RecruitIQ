"""
The numeric score itself is a deterministic skill-overlap heuristic
computed in plain Python — not an LLM call — specifically so it's
unit-testable without touching ai_client at all. The AI layer only
adds a short natural-language explanation on top. This mirrors how a
real implementation would likely work: a cheap, fast, reliable
signal for ranking, with AI reserved for the harder-to-automate
"why" a recruiter actually reads.

V2 additions (candidate ranking pipeline):

- A deterministic pre-filter (app/services/ai/candidate_filter.py) runs
  ahead of any scoring, so a candidate with zero required-skill overlap
  or clearly outside the job's experience band never costs an AI call.
- The AI explanation is cached per (tenant, required-skills,
  candidate-skills) signature — two candidates with identical skill
  sets on the same job reuse one AI call instead of paying for it
  twice. `cache` is optional (defaults to None, meaning "no caching")
  so this class stays constructible without a Flask app context, same
  as before.
- compute() still writes exactly one AIRequest row per call, whether
  or not the explanation came from cache — an AIRequest row means
  "this application was scored," not "a network call was made." What
  the cache actually saves is the real outbound call to ai_client,
  which is what ai_calls_made/ai_calls_cached in RankingRunMetrics
  measure.
"""

import hashlib
import time

from app.models.ai_request import AIRequest
from app.services.ai.candidate_filter import evaluate_candidate
from app.services.ai.ranking_metrics import RankingRunMetrics


def compute_skill_overlap_score(required_skills: list, candidate_skills: list) -> float:
    if not required_skills:
        return 0.0
    required_set = {s.lower() for s in required_skills}
    candidate_set = {s.lower() for s in candidate_skills}
    overlap = required_set & candidate_set
    return round(100 * len(overlap) / len(required_set), 1)


def _explanation_cache_key(tenant_id, required_skills: list, candidate_skills: list) -> str:
    """Namespaced by tenant_id first and foremost — this project treats
    cross-tenant data leakage as the one mistake never to make (see
    BaseRepository's docstring), and a shared cache is exactly the kind
    of place that guarantee is easy to forget in. Skill lists are
    lower-cased and sorted so ['SQL','Python'] and ['python','sql']
    hit the same entry."""
    required_sig = "|".join(sorted((s or "").lower() for s in required_skills))
    candidate_sig = "|".join(sorted((s or "").lower() for s in candidate_skills))
    digest = hashlib.sha256(f"{required_sig}::{candidate_sig}".encode()).hexdigest()
    return f"match_explanation:{tenant_id}:{digest}"


class MatchScoreService:
    def __init__(self, ai_client, ai_request_repo, application_repo, job_repo, profile_repo, cache=None):
        self.ai_client = ai_client
        self.ai_request_repo = ai_request_repo
        self.application_repo = application_repo
        self.job_repo = job_repo
        self.profile_repo = profile_repo
        self.cache = cache  # Flask-Caching Cache instance, or None to disable caching entirely

    def _get_explanation(self, tenant_id, required_skills: list, candidate_skills: list, metrics=None):
        """Returns (text, input_tokens, output_tokens). Checks cache
        first; only calls the real AI client on a miss (or when caching
        is disabled). metrics, if given, is incremented in place —
        ai_calls_cached on a hit, ai_calls_made on a real call."""
        cache_key = _explanation_cache_key(tenant_id, required_skills, candidate_skills)

        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                if metrics is not None:
                    metrics.ai_calls_cached += 1
                return cached["text"], cached.get("input_tokens"), cached.get("output_tokens")

        prompt = (
            f"A candidate has skills: {', '.join(candidate_skills) or 'none listed'}. "
            f"The job requires: {', '.join(required_skills) or 'none listed'}. "
            f"In one sentence, explain the fit."
        )
        result = self.ai_client.complete(prompt)
        if metrics is not None:
            metrics.ai_calls_made += 1

        if self.cache is not None:
            self.cache.set(cache_key, result, timeout=3600)

        return result["text"], result.get("input_tokens"), result.get("output_tokens")

    def compute(self, tenant_id, application_id, metrics=None):
        application = self.application_repo.get_or_404(application_id, tenant_id)
        job = self.job_repo.get_or_404(application.job_id, tenant_id)
        profile = self.profile_repo.get_or_404(application.candidate_profile_id, tenant_id)

        score = compute_skill_overlap_score(job.required_skills, profile.skills)
        explanation, input_tokens, output_tokens = self._get_explanation(
            tenant_id, job.required_skills, profile.skills, metrics=metrics
        )

        ai_request = AIRequest(
            company_id=tenant_id,
            feature="match_score",
            entity_type="application",
            entity_id=application_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            status="suggested",
        )
        self.ai_request_repo.add(ai_request)
        self.ai_request_repo.commit()

        application.match_score = score
        self.application_repo.commit()

        return {"score": score, "explanation": explanation, "ai_request_id": ai_request.id}

    def rank_candidates_for_job(self, tenant_id, job_id, force=False):
        """
        Candidate ranking pipeline:

            active applications -> deterministic pre-filter -> scoring
            (cached where possible) -> sorted results + run metrics

        Every active application is still returned (a filtered-out
        candidate is a real applicant, not a dropped row) — the filter
        only decides who gets a scoring pass *in this run*. A filtered
        candidate keeps whatever match_score it already had (None if
        never scored), which the existing null-safe sort key already
        handles.

        force=True re-scores everyone who passes the filter, same
        meaning as before; it does not override the filter itself —
        someone with zero required-skill overlap still isn't worth an
        AI call even on a forced re-run.

        Returns (results, metrics) — a tuple, not just the applications
        list, so callers (the sync API route, the async Celery task,
        the benchmark script) all see the same RankingRunMetrics shape.
        """
        start = time.monotonic()
        job = self.job_repo.get_or_404(job_id, tenant_id)  # 404s if the job isn't this tenant's
        applications = self.application_repo.list_active_for_job(tenant_id, job_id)

        metrics = RankingRunMetrics(job_id=str(job_id), candidates_considered=len(applications))

        results = []
        for application in applications:
            profile = self.profile_repo.get_or_404(application.candidate_profile_id, tenant_id)
            filter_result = evaluate_candidate(job, profile)

            if not filter_result.passed:
                metrics.candidates_filtered_out += 1
                results.append(application)
                continue

            if force or application.match_score is None:
                self.compute(tenant_id, application.id, metrics=metrics)
                metrics.candidates_scored += 1
            results.append(application)

        metrics.duration_seconds = round(time.monotonic() - start, 4)

        results.sort(key=lambda a: (-(a.match_score or 0), a.applied_at))
        return results, metrics
