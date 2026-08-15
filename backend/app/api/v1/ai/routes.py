from flask import Blueprint, request, jsonify, g, current_app
from flask_jwt_extended import jwt_required

from app.api.v1.ai.schemas import JDSuggestionSchema, ApplyJDSuggestionSchema, MatchScoreSchema
from app.api.v1.applications.schemas import ApplicationSchema
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
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
    service = _build_match_score_service()
    result = service.compute(_tenant_id(), application_id)
    return jsonify({"success": True, "data": MatchScoreSchema().dump(result), "meta": {}})


@ai_bp.route("/jobs/<uuid:job_id>/rank-candidates", methods=["POST"])
@jwt_required()
@require_permission("candidate.view_all")
def rank_candidates(job_id):
    force = request.args.get("force", "false").lower() == "true"
    service = _build_match_score_service()
    applications = service.rank_candidates_for_job(_tenant_id(), job_id, force=force)
    return jsonify(
        {"success": True, "data": ApplicationSchema(many=True).dump(applications), "meta": {}}
    )
