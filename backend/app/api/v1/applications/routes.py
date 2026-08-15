from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1.applications.schemas import (
    MoveStageSchema,
    RejectApplicationSchema,
    ApplicationSchema,
    StageHistoryEntrySchema,
)
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
from app.repositories.application_repository import ApplicationRepository, ApplicationStageHistoryRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import (
    CandidateRepository,
    CandidateProfileRepository,
    ResumeRepository,
)
from app.repositories.job_repository import JobRepository, PipelineStageRepository
from app.services.application_service import ApplicationService
from app.services.audit_service import AuditService
from app.services.candidate_service import CandidateService
from app.services.event_bus import EventBus
from app.utils.permissions import require_permission

applications_bp = Blueprint("applications", __name__, url_prefix="/api/v1/applications")


def _build_service() -> ApplicationService:
    candidate_service = CandidateService(
        candidate_repo=CandidateRepository(db.session),
        profile_repo=CandidateProfileRepository(db.session),
        resume_repo=ResumeRepository(db.session),
        event_bus=EventBus(),
    )
    return ApplicationService(
        application_repo=ApplicationRepository(db.session),
        history_repo=ApplicationStageHistoryRepository(db.session),
        job_repo=JobRepository(db.session),
        candidate_service=candidate_service,
        stage_repo=PipelineStageRepository(db.session),
        event_bus=EventBus(),
        audit_service=AuditService(AuditLogRepository(db.session)),
    )


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@applications_bp.route("", methods=["GET"])
@jwt_required()
@require_permission("candidate.view_all")
def list_applications():
    job_id = request.args.get("job_id")
    service = _build_service()
    applications = service.list_for_job(_tenant_id(), job_id) if job_id else []
    return jsonify({"success": True, "data": ApplicationSchema(many=True).dump(applications), "meta": {}})


@applications_bp.route("/<uuid:application_id>", methods=["GET"])
@jwt_required()
@require_permission("candidate.view_all")
def get_application(application_id):
    service = _build_service()
    application = service.get(_tenant_id(), application_id)
    return jsonify({"success": True, "data": ApplicationSchema().dump(application), "meta": {}})


@applications_bp.route("/<uuid:application_id>/stage", methods=["PATCH"])
@jwt_required()
@require_permission("application.manage")
def move_stage(application_id):
    dto = MoveStageSchema().load(request.get_json() or {})
    service = _build_service()
    application = service.move_stage(
        _tenant_id(), application_id, dto["target_stage_id"],
        moved_by=get_jwt_identity(), note=dto.get("note"),
    )
    return jsonify({"success": True, "data": ApplicationSchema().dump(application), "meta": {}})


@applications_bp.route("/<uuid:application_id>/reject", methods=["POST"])
@jwt_required()
@require_permission("candidate.reject")
def reject_application(application_id):
    dto = RejectApplicationSchema().load(request.get_json() or {})
    service = _build_service()
    application = service.reject(_tenant_id(), application_id, reason=dto.get("reason"), acted_by=get_jwt_identity())
    return jsonify({"success": True, "data": ApplicationSchema().dump(application), "meta": {}})


@applications_bp.route("/<uuid:application_id>/timeline", methods=["GET"])
@jwt_required()
@require_permission("candidate.view_all")
def get_timeline(application_id):
    service = _build_service()
    history = service.get_timeline(_tenant_id(), application_id)
    return jsonify({"success": True, "data": StageHistoryEntrySchema(many=True).dump(history), "meta": {}})
