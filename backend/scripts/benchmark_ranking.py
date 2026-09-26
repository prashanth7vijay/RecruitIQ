"""
Reproducible candidate-ranking benchmark.

Compares two runs over the IDENTICAL seeded dataset, at each requested
scale:

  BASELINE  — the pre-V2 behavior: every active application gets an AI
              explanation call, unconditionally, with no pre-filter and
              no cache (a MatchScoreService constructed with cache=None,
              scored candidate-by-candidate exactly like the original
              rank_candidates_for_job loop used to).

  OPTIMIZED — the current pipeline: deterministic pre-filter first,
              then scoring with the (Redis- or Simple-backed, per
              CACHE_TYPE) explanation cache live, via
              MatchScoreService.rank_candidates_for_job().

Every number below comes from an actual run against a real database in
this environment — nothing here is hand-typed. Re-run this yourself
(`python scripts/benchmark_ranking.py`) any time the pipeline changes;
the report is only ever as trustworthy as its last real execution.

Usage:
    python scripts/benchmark_ranking.py                 # default sizes
    python scripts/benchmark_ranking.py --sizes 100,500,1000,2000
    python scripts/benchmark_ranking.py --ai-provider ollama

Notes on interpreting the numbers:
  - With AI_PROVIDER=stub (this script's default, and the only provider
    that doesn't need a real Ollama server reachable), each AI "call"
    is a fast in-process function — so latency deltas here mostly show
    pipeline/DB overhead, and ai_calls_made/ai_calls_cached is the more
    meaningful number. Re-run with --ai-provider ollama against a real
    local Ollama server for real AI-latency numbers; the gap between
    baseline and optimized duration will be far larger there, since a
    real AI call, not a Python function call, is what's being skipped.
  - ~40% of seeded candidates are deliberately given a non-overlapping
    skill set (pre-filter should catch these) and skill sets are drawn
    from a small fixed pool (so genuine cache hits occur) — see
    _seed_dataset() below for the exact generation rule.
"""

import argparse
import os
import statistics
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random

from app import create_app
from app.extensions import cache as flask_cache, db
from app.models.candidate import Candidate, CandidateProfile
from app.models.application import Application
from app.models.company import Company
from app.models.job import Job
from app.models.pipeline import PipelineStage, PipelineTemplate
from app.models.role import Role
from app.repositories.ai_request_repository import AIRequestRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.candidate_repository import CandidateProfileRepository
from app.repositories.job_repository import JobRepository
from app.services.ai.ai_client import build_ai_client
from app.services.ai.match_score_service import MatchScoreService
from app.services.ai.ranking_metrics import percentile

REQUIRED_SKILLS = ["python", "sql", "docker", "aws"]
# A small fixed pool of candidate skill-sets, reused across many
# candidates on purpose — this is what makes explanation caching do
# anything at all. A real applicant pool has exactly this shape: lots
# of candidates list an overlapping handful of common stack skills.
SKILL_POOL_MATCHING = [
    ["python", "sql"],
    ["python", "sql", "docker"],
    ["python", "sql", "docker", "aws"],
    ["python", "aws"],
    ["sql", "docker"],
]
SKILL_POOL_NON_MATCHING = [
    ["java", "spring"],
    ["ruby", "rails"],
    ["php", "laravel"],
]


def _seed_dataset(tenant_id, user_id, size, tag):
    template = PipelineTemplate(company_id=tenant_id, name=f"bench-{tag}")
    db.session.add(template)
    db.session.commit()
    stage = PipelineStage(pipeline_template_id=template.id, name="Screen", stage_order=0, stage_type="screening")
    db.session.add(stage)
    db.session.commit()

    job = Job(
        company_id=tenant_id,
        title=f"Benchmark Job {tag} ({size})",
        pipeline_template_id=template.id,
        required_skills=REQUIRED_SKILLS,
        created_by=user_id,
    )
    db.session.add(job)
    db.session.commit()

    rng = random.Random(42)  # fixed seed: identical dataset shape every run
    applications = []
    for i in range(size):
        non_matching = rng.random() < 0.4  # ~40% deliberately filtered out
        skills = rng.choice(SKILL_POOL_NON_MATCHING if non_matching else SKILL_POOL_MATCHING)

        candidate = Candidate(email=f"bench-{tag}-{i}-{uuid.uuid4().hex[:8]}@example.com", first_name="Bench", last_name=str(i))
        db.session.add(candidate)
        db.session.flush()
        profile = CandidateProfile(company_id=tenant_id, candidate_id=candidate.id, skills=skills)
        db.session.add(profile)
        db.session.flush()
        application = Application(
            company_id=tenant_id, job_id=job.id, candidate_id=candidate.id,
            candidate_profile_id=profile.id, current_stage_id=stage.id, status="active",
        )
        db.session.add(application)
        applications.append(application)

    db.session.commit()
    return job, applications


def _build_service(cache_enabled: bool) -> MatchScoreService:
    return MatchScoreService(
        ai_client=build_ai_client(app_config),
        ai_request_repo=AIRequestRepository(db.session),
        application_repo=ApplicationRepository(db.session),
        job_repo=JobRepository(db.session),
        profile_repo=CandidateProfileRepository(db.session),
        cache=flask_cache if cache_enabled else None,
    )


def _run_baseline(tenant_id, job_id, applications):
    """Every active application scored unconditionally — no pre-filter,
    no cache — same as rank_candidates_for_job() before the V2 pipeline
    change. Calls compute() directly, one per application, bypassing
    the current filtered/cached rank_candidates_for_job entirely."""
    service = _build_service(cache_enabled=False)
    start = time.monotonic()
    durations = []
    for application in applications:
        call_start = time.monotonic()
        service.compute(tenant_id, application.id)
        durations.append(time.monotonic() - call_start)
    total = time.monotonic() - start
    return {
        "candidates": len(applications),
        "duration_seconds": round(total, 4),
        "candidates_per_second": round(len(applications) / total, 2) if total > 0 else 0.0,
        "ai_calls": len(applications),
        "p50_ms": round(percentile(durations, 50) * 1000, 3),
        "p95_ms": round(percentile(durations, 95) * 1000, 3),
        "p99_ms": round(percentile(durations, 99) * 1000, 3),
    }


def _reset_scores(applications):
    for a in applications:
        a.match_score = None
    db.session.commit()


def _run_optimized(tenant_id, job_id):
    service = _build_service(cache_enabled=True)
    _, metrics = service.rank_candidates_for_job(tenant_id, job_id, force=True)
    return metrics


def main():
    parser = argparse.ArgumentParser(description="RecruitIQ candidate-ranking benchmark")
    parser.add_argument("--sizes", default="100,500,1000", help="Comma-separated candidate counts")
    parser.add_argument("--ai-provider", default=os.environ.get("AI_PROVIDER", "stub"), choices=["stub", "ollama"])
    args = parser.parse_args()

    global app_config
    flask_app = create_app("development")
    flask_app.config["AI_PROVIDER"] = args.ai_provider
    app_config = flask_app.config

    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]

    print("=" * 60)
    print("RecruitIQ Candidate Ranking Benchmark")
    print("=" * 60)
    print(f"AI provider: {args.ai_provider}")
    print(f"Dataset sizes: {sizes}")
    print()

    with flask_app.app_context():
        bench_company = Company(name="Benchmark Co", slug=f"benchmark-{uuid.uuid4().hex[:8]}")
        db.session.add(bench_company)
        db.session.commit()

        bench_role = Role(company_id=bench_company.id, name="bench-role")
        db.session.add(bench_role)
        db.session.commit()

        from app.models.user import User
        from app.services.auth_service import _hash_password

        bench_user = User(
            company_id=bench_company.id, role_id=bench_role.id, email="bench@example.com",
            password_hash=_hash_password("not-used"), first_name="Bench", last_name="User", status="active",
        )
        db.session.add(bench_user)
        db.session.commit()

        for size in sizes:
            print("-" * 60)
            print(f"Dataset size: {size} candidates")
            print("-" * 60)

            job, applications = _seed_dataset(bench_company.id, bench_user.id, size, tag=str(size))

            baseline = _run_baseline(bench_company.id, job.id, applications)
            print("Baseline (no pre-filter, no cache):")
            print(f"  Duration:      {baseline['duration_seconds']} sec")
            print(f"  Throughput:    {baseline['candidates_per_second']} candidates/sec")
            print(f"  AI calls:      {baseline['ai_calls']}")
            print(f"  p50 / p95 / p99 per-candidate: {baseline['p50_ms']} / {baseline['p95_ms']} / {baseline['p99_ms']} ms")

            _reset_scores(applications)
            flask_cache.clear()

            optimized = _run_optimized(bench_company.id, job.id)
            m = optimized.to_dict()
            print("Optimized (pre-filter + cache):")
            print(f"  Duration:      {m['duration_seconds']} sec")
            print(f"  Throughput:    {m['candidates_per_second']} candidates/sec")
            print(f"  Candidates filtered out: {m['candidates_filtered_out']} / {m['candidates_considered']}")
            print(f"  AI calls made: {m['ai_calls_made']}  |  AI calls cached: {m['ai_calls_cached']}  |  cache hit rate: {m['cache_hit_rate']}")

            ai_calls_avoided_pct = round(100 * (1 - (m["ai_calls_made"] / baseline["ai_calls"])), 1) if baseline["ai_calls"] else 0.0
            duration_change_pct = (
                round(100 * (1 - (m["duration_seconds"] / baseline["duration_seconds"])), 1)
                if baseline["duration_seconds"] > 0 else 0.0
            )
            print("Improvement:")
            print(f"  AI calls avoided:  {ai_calls_avoided_pct}%")
            print(f"  Duration change:   {duration_change_pct}%")
            print()

        db.session.query(Application).filter(Application.company_id == bench_company.id).delete()
        db.session.query(CandidateProfile).filter(CandidateProfile.company_id == bench_company.id).delete()
        db.session.query(Job).filter(Job.company_id == bench_company.id).delete()
        db.session.query(PipelineStage).filter(
            PipelineStage.pipeline_template_id.in_(
                db.session.query(PipelineTemplate.id).filter(PipelineTemplate.company_id == bench_company.id)
            )
        ).delete(synchronize_session=False)
        db.session.query(PipelineTemplate).filter(PipelineTemplate.company_id == bench_company.id).delete()
        db.session.query(User).filter(User.company_id == bench_company.id).delete()
        db.session.query(Role).filter(Role.company_id == bench_company.id).delete()
        db.session.query(Company).filter(Company.id == bench_company.id).delete()
        db.session.commit()
        print("Benchmark data cleaned up.")


if __name__ == "__main__":
    main()
