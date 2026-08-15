from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required

from app.api.v1.talent_pools.schemas import (
    CreateTalentPoolSchema,
    AddCandidateToPoolSchema,
    TalentPoolSchema,
    PoolMemberSchema,
)
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
from app.repositories.candidate_repository import CandidateProfileRepository
from app.repositories.talent_pool_repository import TalentPoolRepository, TalentPoolMembershipRepository
from app.services.talent_pool_service import TalentPoolService
from app.utils.permissions import require_permission

talent_pools_bp = Blueprint("talent_pools", __name__, url_prefix="/api/v1/talent-pools")


def _build_service() -> TalentPoolService:
    return TalentPoolService(
        pool_repo=TalentPoolRepository(db.session),
        membership_repo=TalentPoolMembershipRepository(db.session),
        profile_repo=CandidateProfileRepository(db.session),
    )


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@talent_pools_bp.route("", methods=["GET"])
@jwt_required()
def list_pools():
    service = _build_service()
    pools = service.list(_tenant_id())
    return jsonify({"success": True, "data": TalentPoolSchema(many=True).dump(pools), "meta": {}})


@talent_pools_bp.route("", methods=["POST"])
@jwt_required()
@require_permission("candidate.manage")
def create_pool():
    dto = CreateTalentPoolSchema().load(request.get_json() or {})
    service = _build_service()
    pool = service.create(_tenant_id(), **dto)
    return jsonify({"success": True, "data": TalentPoolSchema().dump(pool), "meta": {}}), 201


@talent_pools_bp.route("/<uuid:pool_id>/members", methods=["GET"])
@jwt_required()
def list_members(pool_id):
    service = _build_service()
    members = service.list_members(_tenant_id(), pool_id)
    return jsonify({"success": True, "data": PoolMemberSchema(many=True).dump(members), "meta": {}})


@talent_pools_bp.route("/<uuid:pool_id>/members", methods=["POST"])
@jwt_required()
@require_permission("candidate.manage")
def add_member(pool_id):
    dto = AddCandidateToPoolSchema().load(request.get_json() or {})
    service = _build_service()
    service.add_candidate(_tenant_id(), pool_id, dto["candidate_profile_id"])
    return jsonify({"success": True, "data": None, "meta": {}}), 201


@talent_pools_bp.route("/<uuid:pool_id>/members/<uuid:candidate_profile_id>", methods=["DELETE"])
@jwt_required()
@require_permission("candidate.manage")
def remove_member(pool_id, candidate_profile_id):
    service = _build_service()
    service.remove_candidate(_tenant_id(), pool_id, candidate_profile_id)
    return jsonify({"success": True, "data": None, "meta": {}}), 204
