from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1.interviews.schemas import (
    ScheduleInterviewSchema,
    RescheduleInterviewSchema,
    SubmitFeedbackSchema,
    InterviewSchema,
    InterviewFeedbackSchema,
)
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
from app.repositories.application_repository import ApplicationRepository
from app.repositories.interview_repository import InterviewRepository, InterviewFeedbackRepository
from app.services.event_bus import EventBus
from app.services.interview_service import InterviewService
from app.utils.permissions import require_permission

interviews_bp = Blueprint("interviews", __name__, url_prefix="/api/v1/interviews")


def _build_service() -> InterviewService:
    return InterviewService(
        interview_repo=InterviewRepository(db.session),
        feedback_repo=InterviewFeedbackRepository(db.session),
        application_repo=ApplicationRepository(db.session),
        event_bus=EventBus(),
    )


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@interviews_bp.route("", methods=["POST"])
@jwt_required()
@require_permission("interview.schedule")
def schedule_interview():
    dto = ScheduleInterviewSchema().load(request.get_json() or {})
    service = _build_service()
    interview = service.schedule(
        tenant_id=_tenant_id(),
        application_id=dto["application_id"],
        round_name=dto["round_name"],
        created_by=get_jwt_identity(),
        panelist_user_ids=dto["panelist_user_ids"],
        scheduled_at=dto.get("scheduled_at"),
        duration_minutes=dto.get("duration_minutes"),
        meeting_link=dto.get("meeting_link"),
    )
    return jsonify({"success": True, "data": InterviewSchema().dump(interview), "meta": {}}), 201


@interviews_bp.route("", methods=["GET"])
@jwt_required()
def list_interviews():
    application_id = request.args.get("application_id")
    service = _build_service()
    interviews = service.list_for_application(_tenant_id(), application_id) if application_id else []
    return jsonify({"success": True, "data": InterviewSchema(many=True).dump(interviews), "meta": {}})


@interviews_bp.route("/mine", methods=["GET"])
@jwt_required()
def my_interviews():
    service = _build_service()
    interviews = service.list_for_interviewer(_tenant_id(), get_jwt_identity())
    return jsonify({"success": True, "data": InterviewSchema(many=True).dump(interviews), "meta": {}})


@interviews_bp.route("/<uuid:interview_id>/reschedule", methods=["PATCH"])
@jwt_required()
@require_permission("interview.schedule")
def reschedule_interview(interview_id):
    dto = RescheduleInterviewSchema().load(request.get_json() or {})
    service = _build_service()
    interview = service.reschedule(_tenant_id(), interview_id, dto["scheduled_at"])
    return jsonify({"success": True, "data": InterviewSchema().dump(interview), "meta": {}})


@interviews_bp.route("/<uuid:interview_id>/cancel", methods=["PATCH"])
@jwt_required()
@require_permission("interview.schedule")
def cancel_interview(interview_id):
    service = _build_service()
    interview = service.cancel(_tenant_id(), interview_id)
    return jsonify({"success": True, "data": InterviewSchema().dump(interview), "meta": {}})


@interviews_bp.route("/<uuid:interview_id>/feedback", methods=["POST"])
@jwt_required()
@require_permission("interview.feedback.submit")
def submit_feedback(interview_id):
    dto = SubmitFeedbackSchema().load(request.get_json() or {})
    service = _build_service()
    feedback = service.submit_feedback(
        _tenant_id(), interview_id, get_jwt_identity(),
        rubric_scores=dto["rubric_scores"], overall_rating=dto.get("overall_rating"),
        recommendation=dto.get("recommendation"), notes=dto.get("notes"),
    )
    return jsonify({"success": True, "data": InterviewFeedbackSchema().dump(feedback), "meta": {}}), 201
