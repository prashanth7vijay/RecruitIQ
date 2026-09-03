from flask import Blueprint, request, jsonify, g, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1.candidates.schemas import (
    UpdateProfileSchema,
    CandidateProfileSchema,
    ResumeSchema,
    AddNoteSchema,
    NoteSchema,
    AddTagSchema,
    TagSchema,
)
from app.exceptions.base import NotFoundError, UnauthenticatedError
from app.extensions import db
from app.repositories.candidate_repository import (
    CandidateRepository,
    CandidateProfileRepository,
    ResumeRepository,
)
from app.repositories.talent_pool_repository import CandidateNoteRepository, CandidateTagRepository
from app.services.candidate_service import CandidateService
from app.services.event_bus import EventBus
from app.storage.factory import build_storage
from app.utils.permissions import require_permission

candidates_bp = Blueprint("candidates", __name__, url_prefix="/api/v1/candidates")


def _build_service() -> CandidateService:
    return CandidateService(
        candidate_repo=CandidateRepository(db.session),
        profile_repo=CandidateProfileRepository(db.session),
        resume_repo=ResumeRepository(db.session),
        event_bus=EventBus(),
        note_repo=CandidateNoteRepository(db.session),
        tag_repo=CandidateTagRepository(db.session),
    )


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@candidates_bp.route("", methods=["GET"])
@jwt_required()
@require_permission("candidate.view_all")
def list_candidates():
    from app.utils.pagination import paginate_query

    query = CandidateProfileRepository(db.session).list_with_candidate(_tenant_id())
    profiles, pagination_meta = paginate_query(query)
    return jsonify({"success": True, "data": CandidateProfileSchema(many=True).dump(profiles), "meta": pagination_meta})


@candidates_bp.route("/<uuid:profile_id>", methods=["GET"])
@jwt_required()
@require_permission("candidate.view_all")
def get_candidate(profile_id):
    service = _build_service()
    profile = service.get_profile(_tenant_id(), profile_id)
    return jsonify({"success": True, "data": CandidateProfileSchema().dump(profile), "meta": {}})


@candidates_bp.route("/<uuid:profile_id>/resume", methods=["GET"])
@jwt_required()
@require_permission("candidate.view_all")
def get_candidate_resume(profile_id):
    # The signed URL is generated fresh per request (short expiry — see
    # LocalStorage.get_url) rather than stored/cached, so it can't be
    # copied out and shared past its expiry window.
    service = _build_service()
    resume = service.get_resume(_tenant_id(), profile_id)
    if resume is None:
        raise NotFoundError("This candidate hasn't provided a resume")

    storage = build_storage(current_app.config)
    data = ResumeSchema().dump(resume)
    data["url"] = storage.get_url(resume.storage_key)
    return jsonify({"success": True, "data": data, "meta": {}})


@candidates_bp.route("/<uuid:profile_id>", methods=["PATCH"])
@jwt_required()
@require_permission("candidate.manage")
def update_candidate(profile_id):
    dto = UpdateProfileSchema().load(request.get_json() or {})
    service = _build_service()
    profile = service.update_profile(_tenant_id(), profile_id, **dto)
    return jsonify({"success": True, "data": CandidateProfileSchema().dump(profile), "meta": {}})


@candidates_bp.route("/<uuid:profile_id>/notes", methods=["GET"])
@jwt_required()
@require_permission("candidate.view_all")
def list_notes(profile_id):
    service = _build_service()
    notes = service.list_notes(_tenant_id(), profile_id)
    return jsonify({"success": True, "data": NoteSchema(many=True).dump(notes), "meta": {}})


@candidates_bp.route("/<uuid:profile_id>/notes", methods=["POST"])
@jwt_required()
@require_permission("candidate.manage")
def add_note(profile_id):
    dto = AddNoteSchema().load(request.get_json() or {})
    service = _build_service()
    note = service.add_note(_tenant_id(), profile_id, get_jwt_identity(), dto["body"])
    return jsonify({"success": True, "data": NoteSchema().dump(note), "meta": {}}), 201


@candidates_bp.route("/<uuid:profile_id>/tags", methods=["GET"])
@jwt_required()
@require_permission("candidate.view_all")
def list_tags(profile_id):
    service = _build_service()
    tags = service.list_tags(_tenant_id(), profile_id)
    return jsonify({"success": True, "data": TagSchema(many=True).dump(tags), "meta": {}})


@candidates_bp.route("/<uuid:profile_id>/tags", methods=["POST"])
@jwt_required()
@require_permission("candidate.manage")
def add_tag(profile_id):
    dto = AddTagSchema().load(request.get_json() or {})
    service = _build_service()
    tag = service.add_tag(_tenant_id(), profile_id, dto["label"])
    return jsonify({"success": True, "data": TagSchema().dump(tag), "meta": {}}), 201