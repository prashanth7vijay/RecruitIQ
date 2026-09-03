from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1.employee_portal.schemas import OpenJobSchema, SubmitReferralSchema, MyReferralSchema
from app.exceptions.base import UnauthenticatedError
from app.extensions import db, limiter
from app.repositories.candidate_repository import CandidateRepository, CandidateProfileRepository, ResumeRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.job_repository import JobRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.referral_repository import ReferralRepository
from app.repositories.user_repository import UserRepository
from app.services.candidate_service import CandidateService
from app.services.event_bus import EventBus
from app.services.notification_service import NotificationService
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
    return ReferralService(
        session=db.session,
        referral_repo=ReferralRepository(db.session),
        job_repo=JobRepository(db.session),
        candidate_service=candidate_service,
        notification_service=NotificationService(NotificationRepository(db.session)),
        user_repo=UserRepository(db.session),
        company=CompanyRepository(db.session).get_or_404(_tenant_id()),
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
@limiter.limit("20 per day")  

def submit_referral():
    dto = SubmitReferralSchema().load(request.get_json() or {})
    service = _build_service()
    referral = service.submit_referral(
        _tenant_id(),
        get_jwt_identity(),
        job_id=dto["job_id"],
        email=dto["email"],
    )
    return jsonify({"success": True, "data": {"id": str(referral.id)}, "meta": {}}), 201