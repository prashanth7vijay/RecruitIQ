from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1.employee_portal.schemas import OpenJobSchema, SubmitReferralSchema, MyReferralSchema
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
from app.repositories.application_repository import ApplicationRepository, ApplicationStageHistoryRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateRepository, CandidateProfileRepository, ResumeRepository
from app.repositories.job_repository import JobRepository, PipelineStageRepository
from app.repositories.referral_repository import ReferralRepository
from app.services.application_service import ApplicationService
from app.services.audit_service import AuditService
from app.services.candidate_service import CandidateService
from app.services.event_bus import EventBus
from app.services.referral_service import ReferralService
from app.utils.permissions import require_permission

employee_portal_bp = Blueprint("employee_portal", __name__, url_prefix="/api/v1/employee-portal")


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


def _build_service() -> ReferralService:
    candidate_service = CandidateService(
        candidate_repo=CandidateRepository(db.session),
        profile_repo=CandidateProfileRepository(db.session),
        resume_repo=ResumeRepository(db.session),
        event_bus=EventBus(),
    )
    application_service = ApplicationService(
        application_repo=ApplicationRepository(db.session),
        history_repo=ApplicationStageHistoryRepository(db.session),
        job_repo=JobRepository(db.session),
        candidate_service=candidate_service,
        stage_repo=PipelineStageRepository(db.session),
        event_bus=EventBus(),
        audit_service=AuditService(AuditLogRepository(db.session)),
    )
    return ReferralService(
        session=db.session,
        referral_repo=ReferralRepository(db.session),
        application_service=application_service,
        job_repo=JobRepository(db.session),
    )


@employee_portal_bp.route("/jobs", methods=["GET"])
@jwt_required()
def list_open_jobs():
    service = _build_service()
    jobs = service.list_open_jobs(_tenant_id())
    return jsonify({"success": True, "data": OpenJobSchema(many=True).dump(jobs), "meta": {}})


@employee_portal_bp.route("/referrals", methods=["GET"])
@jwt_required()
@require_permission("referral.submit")
def list_my_referrals():
    service = _build_service()
    rows = service.list_my_referrals(_tenant_id(), get_jwt_identity())
    return jsonify({"success": True, "data": MyReferralSchema(many=True).dump(rows), "meta": {}})


@employee_portal_bp.route("/referrals", methods=["POST"])
@jwt_required()
@require_permission("referral.submit")
def submit_referral():
    dto = SubmitReferralSchema().load(request.get_json() or {})
    service = _build_service()
    referral, application = service.submit_referral(
        _tenant_id(),
        get_jwt_identity(),
        job_id=dto["job_id"],
        email=dto["email"],
        first_name=dto["first_name"],
        last_name=dto["last_name"],
        phone=dto.get("phone"),
    )
    return jsonify(
        {"success": True, "data": {"id": str(referral.id), "application_id": str(application.id)}, "meta": {}}
    ), 201
