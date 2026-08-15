from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.api.v1.onboarding.schemas import AssignOnboardingSchema, OnboardingChecklistSchema, OnboardingTaskSchema
from app.exceptions.base import NotFoundError
from app.extensions import db
from app.repositories.onboarding_repository import OnboardingRepository
from app.services.onboarding_service import OnboardingService
from app.utils.permissions import require_permission

onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/api/v1/onboarding")


def _build_service() -> OnboardingService:
    return OnboardingService(onboarding_repo=OnboardingRepository(db.session))


@onboarding_bp.route("/by-application/<uuid:application_id>", methods=["GET"])
@jwt_required()
def get_by_application(application_id):
    service = _build_service()
    checklist = service.get_by_application(application_id)
    if checklist is None:
        raise NotFoundError("No onboarding checklist exists for this application yet")
    return jsonify({"success": True, "data": OnboardingChecklistSchema().dump(checklist), "meta": {}})


@onboarding_bp.route("/<uuid:checklist_id>", methods=["PATCH"])
@jwt_required()
@require_permission("onboarding.manage")
def assign(checklist_id):
    dto = AssignOnboardingSchema().load(request.get_json() or {})
    service = _build_service()
    checklist = service.assign(checklist_id, **dto)
    return jsonify({"success": True, "data": OnboardingChecklistSchema().dump(checklist), "meta": {}})


@onboarding_bp.route("/tasks/<uuid:task_id>/complete", methods=["PATCH"])
@jwt_required()
@require_permission("onboarding.manage")
def complete_task(task_id):
    service = _build_service()
    task = service.complete_task(task_id)
    return jsonify({"success": True, "data": OnboardingTaskSchema().dump(task), "meta": {}})
