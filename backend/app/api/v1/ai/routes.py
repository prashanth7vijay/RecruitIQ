from flask import Blueprint, request, jsonify, g, current_app
from flask_jwt_extended import jwt_required

from app.api.v1.ai.schemas import JDSuggestionSchema, ApplyJDSuggestionSchema, MatchScoreSchema
from app.api.v1.applications.schemas import ApplicationSchema
from app.exceptions.base import UnauthenticatedError
from app.extensions import cache, db
from app.observability import record_ranking_metrics
from app.repositories.ai_request_repository import AIRequestRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.candidate_repository import CandidateProfileRepository
from app.repositories.job_repository import JobRepository
from app.services.ai.ai_client import build_ai_client
from app.services.ai.jd_improvement_service import JDImprovementService
from app.services.ai.match_score_service import MatchScoreService
from app.utils.permissions import require_permission

ai_bp = Blueprint("ai", __name__, url_prefix="/api/v1/ai")


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


def _build_jd_service() -> JDImprovementService:
    return JDImprovementService(
        ai_client=build_ai_client(current_app.config),
        ai_request_repo=AIRequestRepository(db.session),
        job_repo=JobRepository(db.session),
    )


def _build_match_score_service() -> MatchScoreService:
    return MatchScoreService(
        ai_client=build_ai_client(current_app.config),
        ai_request_repo=AIRequestRepository(db.session),
        application_repo=ApplicationRepository(db.session),
        job_repo=JobRepository(db.session),
        profile_repo=CandidateProfileRepository(db.session),
        cache=cache,
    )


@ai_bp.route("/jobs/<uuid:job_id>/improve-description", methods=["POST"])
@jwt_required()
@require_permission("job.create")
def improve_job_description(job_id):
    service = _build_jd_service()
    result = service.get_suggestion(_tenant_id(), job_id)
    return jsonify({"success": True, "data": JDSuggestionSchema().dump(result), "meta": {}})


@ai_bp.route("/jobs/<uuid:job_id>/apply-description", methods=["POST"])
@jwt_required()
@require_permission("job.create")
def apply_job_description(job_id):
    dto = ApplyJDSuggestionSchema().load(request.get_json() or {})
    service = _build_jd_service()
    job = service.apply_suggestion(_tenant_id(), job_id, dto["ai_request_id"], dto["new_description"])
    return jsonify({"success": True, "data": {"id": str(job.id), "description": job.description}, "meta": {}})


@ai_bp.route("/applications/<uuid:application_id>/match-score", methods=["POST"])
@jwt_required()
@require_permission("candidate.view_all")
def compute_match_score(application_id):
    # POST, not GET — this computes an AI call, logs an AIRequest row,
    # and mutates application.match_score, so it's a side-effecting
    # operation, not a safe/idempotent read. (Was GET; fixed as part of
    # AI Candidate Matching module — see ranking below, which is the
    # same underlying operation run in bulk.)
    service = _build_match_score_service()
    result = service.compute(_tenant_id(), application_id)
    return jsonify({"success": True, "data": MatchScoreSchema().dump(result), "meta": {}})


@ai_bp.route("/jobs/<uuid:job_id>/rank-candidates", methods=["POST"])
@jwt_required()
@require_permission("candidate.view_all")
def rank_candidates(job_id):
    """
    Candidate Ranking (AI Center) — deterministically pre-filters, then
    scores, every active applicant on a job that doesn't already have a
    score, then returns all of them sorted by match score descending.
    Pass ?force=true to rescore everyone who still passes the filter
    (e.g. after the job's required_skills changed).

    Synchronous — fine for the sizes a single job's applicant pool
    normally reaches. For a bulk/large-pool run, use the async variant
    below instead of blocking the request.
    """
    force = request.args.get("force", "false").lower() == "true"
    service = _build_match_score_service()
    applications, metrics = service.rank_candidates_for_job(_tenant_id(), job_id, force=force)
    record_ranking_metrics(metrics)
    return jsonify(
        {
            "success": True,
            "data": ApplicationSchema(many=True).dump(applications),
            "meta": {"ranking": metrics.to_dict()},
        }
    )


@ai_bp.route("/jobs/<uuid:job_id>/rank-candidates/async", methods=["POST"])
@jwt_required()
@require_permission("candidate.view_all")
def rank_candidates_async(job_id):
    """
    Same operation as POST /rank-candidates, but dispatched to Celery
    (queue: batch — see workers/celery_app.py's routing table) instead
    of running inline. Returns immediately with a job_id to poll via
    GET /ai/ranking-jobs/<job_id>.

    This is the endpoint an applicant pool large enough to matter
    should use — see docs/ranking-engine.md for why a synchronous HTTP
    request is the wrong shape for scoring hundreds/thousands of
    candidates.
    """
    from app.workers.ranking_tasks import rank_candidates_task

    force = request.args.get("force", "false").lower() == "true"
    # 404s here (via the tenant-scoped get_or_404 inside the task) would
    # otherwise surface deep inside a worker process with no HTTP
    # request to report to — so validate tenant ownership synchronously
    # before ever queuing the job, the same guard rank_candidates()
    # above gets for free from its own service call.
    JobRepository(db.session).get_or_404(job_id, _tenant_id())

    async_result = rank_candidates_task.delay(str(_tenant_id()), str(job_id), force)
    return (
        jsonify(
            {
                "success": True,
                "data": {"job_id": async_result.id, "status": "QUEUED"},
                "meta": {},
            }
        ),
        202,
    )


@ai_bp.route("/ranking-jobs/<task_id>", methods=["GET"])
@jwt_required()
@require_permission("candidate.view_all")
def get_ranking_job_status(task_id):
    """
    Polls a Celery AsyncResult and maps its native state vocabulary
    (PENDING/STARTED/SUCCESS/FAILURE/RETRY) onto the QUEUED/PROCESSING/
    COMPLETED/FAILED vocabulary the ranking pipeline's job-status
    contract uses elsewhere. No tenant check on task_id itself — it's
    an opaque Celery-generated UUID, not a guessable/enumerable
    resource, and the result payload it resolves to was already scoped
    to the tenant that queued it (see rank_candidates_task).
    """
    from app.workers.celery_app import celery_app

    async_result = celery_app.AsyncResult(task_id)

    state_map = {
        "PENDING": "QUEUED",
        "STARTED": "PROCESSING",
        "RETRY": "PROCESSING",
        "SUCCESS": "COMPLETED",
        "FAILURE": "FAILED",
    }
    status = state_map.get(async_result.state, async_result.state)

    data = {"job_id": task_id, "status": status}
    if status == "COMPLETED":
        data["result"] = async_result.result
    elif status == "FAILED":
        data["error"] = str(async_result.result) if async_result.result else "Ranking task failed"

    return jsonify({"success": True, "data": data, "meta": {}})
