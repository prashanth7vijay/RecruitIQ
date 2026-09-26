"""
Async candidate ranking — the same MatchScoreService.rank_candidates_for_job()
pipeline the synchronous /ai/jobs/:id/rank-candidates endpoint uses, just
run through Celery instead of inline in the request.

Routed to the 'batch' queue (see celery_app.py's task_routes) — this is
bulk/report-shaped work, not a transactional email or a resume upload
someone's actively waiting on, so it shouldn't compete with 'critical'
or 'cpu_intensive' for worker capacity.

The task result (Celery's result backend, already configured via
CELERY_RESULT_BACKEND=REDIS_URL) is what GET /ai/ranking-jobs/<task_id>
reads back — kept deliberately small and JSON-plain (str ids, not UUID
objects; no ORM instances) since it has to survive a round trip through
Redis as JSON.
"""

from flask import current_app

from app.extensions import cache, db
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def rank_candidates_task(self, tenant_id: str, job_id: str, force: bool = False):
    from app.repositories.ai_request_repository import AIRequestRepository
    from app.repositories.application_repository import ApplicationRepository
    from app.repositories.candidate_repository import CandidateProfileRepository
    from app.repositories.job_repository import JobRepository
    from app.services.ai.ai_client import build_ai_client
    from app.services.ai.match_score_service import MatchScoreService

    service = MatchScoreService(
        ai_client=build_ai_client(current_app.config),
        ai_request_repo=AIRequestRepository(db.session),
        application_repo=ApplicationRepository(db.session),
        job_repo=JobRepository(db.session),
        profile_repo=CandidateProfileRepository(db.session),
        cache=cache,
    )

    try:
        applications, metrics = service.rank_candidates_for_job(tenant_id, job_id, force=force)
    except Exception as exc:  # noqa: BLE001 — deliberately broad: any failure here
        # (AI provider unreachable, a transient DB error) should retry a
        # bounded number of times rather than leave the job stuck in
        # PENDING forever or silently vanish. See Section 21 (reliability)
        # of the V2 brief — bounded retries, not a retry storm.
        raise self.retry(exc=exc)

    from app.observability import record_ranking_metrics

    record_ranking_metrics(metrics)

    return {
        "job_id": job_id,
        "candidates": [
            {
                "application_id": str(a.id),
                "candidate_id": str(a.candidate_id),
                "match_score": float(a.match_score) if a.match_score is not None else None,
            }
            for a in applications
        ],
        "metrics": metrics.to_dict(),
    }
