"""
Deterministic pre-filtering for the candidate ranking pipeline.

Runs before MatchScoreService ever touches the AI client. The whole
point is to keep the expensive step (an AI explanation call) off the
critical path for candidates who were never going to be shortlisted
anyway — a candidate missing every required skill, or clearly outside
the job's stated experience band, doesn't need a scoring pass at all.

Deliberately simple and dependency-free (plain functions over plain
values, no DB/AI access) so it's fully unit-testable on its own, the
same way compute_skill_overlap_score in match_score_service.py is.

Nothing here rejects a candidate outright from the applicant list —
Application.status stays whatever it already was. This only decides
who gets a scoring pass in THIS ranking run; a filtered-out candidate
is still a real, visible applicant, just reported with score None and
a stated reason instead of an AI call.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FilterResult:
    passed: bool
    reason: Optional[str] = None  # set only when passed is False


def _has_skill_overlap(required_skills: list, candidate_skills: list) -> bool:
    """No required skills listed on the job = nothing to filter on, so
    every candidate passes this check. Otherwise at least one overlap
    is required — full-overlap is what scoring itself measures; this
    step only needs to establish "not obviously irrelevant."""
    if not required_skills:
        return True
    required_set = {s.lower() for s in required_skills}
    candidate_set = {s.lower() for s in candidate_skills}
    return bool(required_set & candidate_set)


def _within_experience_band(
    experience_min, experience_max, candidate_experience_years
) -> bool:
    """Missing data never filters a candidate out — an unset job bound
    or an unset candidate experience figure means there's nothing to
    check, not an automatic rejection. Only an explicit, known mismatch
    filters someone out."""
    if candidate_experience_years is None:
        return True
    if experience_min is not None and candidate_experience_years < experience_min:
        return False
    if experience_max is not None and candidate_experience_years > experience_max:
        return False
    return True


def evaluate_candidate(job, profile) -> FilterResult:
    """
    job: app.models.job.Job
    profile: app.models.candidate.CandidateProfile

    Two checks only, deliberately — required-skill overlap and
    experience band. Location/salary/notice-period exist on the
    profile but are recruiter judgment calls, not hard eligibility
    gates, so they're left out of an automatic filter rather than
    silently rejecting a candidate a recruiter would have wanted to
    see.
    """
    if not _has_skill_overlap(job.required_skills or [], profile.skills or []):
        return FilterResult(passed=False, reason="no_required_skill_overlap")

    if not _within_experience_band(
        job.experience_min, job.experience_max, profile.experience_years
    ):
        return FilterResult(passed=False, reason="outside_experience_band")

    return FilterResult(passed=True)
