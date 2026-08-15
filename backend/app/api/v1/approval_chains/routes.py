from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required

from app.api.v1.approval_chains.schemas import ApprovalChainSchema, SetApprovalChainSchema
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
from app.repositories.approval_chain_repository import ApprovalChainRepository
from app.repositories.role_repository import RoleRepository
from app.services.approval_chain_service import ApprovalChainService
from app.utils.permissions import require_permission

approval_chains_bp = Blueprint("approval_chains", __name__, url_prefix="/api/v1/approval-chains")


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


def _build_service() -> ApprovalChainService:
    return ApprovalChainService(
        chain_repo=ApprovalChainRepository(db.session), role_repo=RoleRepository(db.session)
    )


@approval_chains_bp.route("/<string:entity_type>", methods=["GET"])
@jwt_required()
def get_chain(entity_type):
    service = _build_service()
    chain = service.get_chain(_tenant_id(), entity_type)
    return jsonify({"success": True, "data": ApprovalChainSchema().dump(chain) if chain else None, "meta": {}})


@approval_chains_bp.route("/<string:entity_type>", methods=["PUT"])
@jwt_required()
@require_permission("approval.manage_chains")
def set_chain(entity_type):
    dto = SetApprovalChainSchema().load(request.get_json() or {})
    service = _build_service()
    chain = service.set_chain(_tenant_id(), entity_type, dto["role_ids"])
    return jsonify({"success": True, "data": ApprovalChainSchema().dump(chain), "meta": {}})
