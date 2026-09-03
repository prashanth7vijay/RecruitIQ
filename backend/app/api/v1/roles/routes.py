from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required

from app.api.v1.roles.schemas import RoleSchema, PermissionSchema, CreateRoleSchema, UpdateRoleSchema
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
from app.repositories.role_repository import RoleRepository, PermissionRepository
from app.repositories.user_repository import UserRepository
from app.services.role_service import RoleService
from app.utils.permissions import require_permission

roles_bp = Blueprint("roles", __name__, url_prefix="/api/v1/roles")


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


def _build_service():
    return RoleService(
        role_repo=RoleRepository(db.session),
        permission_repo=PermissionRepository(db.session),
        user_repo=UserRepository(db.session),
    )


@roles_bp.route("", methods=["GET"])
@jwt_required()
@require_permission("admin.manage_users", "role.manage", "approval.manage_chains")
def list_roles():
    service = _build_service()
    roles = service.list_roles(_tenant_id())
    return jsonify({"success": True, "data": RoleSchema(many=True).dump(roles), "meta": {}})


@roles_bp.route("/<uuid:role_id>", methods=["GET"])
@jwt_required()
@require_permission("admin.manage_users", "role.manage", "approval.manage_chains")
def get_role(role_id):
    service = _build_service()
    role = service.get_role(_tenant_id(), role_id)
    return jsonify({"success": True, "data": RoleSchema().dump(role), "meta": {}})


@roles_bp.route("", methods=["POST"])
@jwt_required()
@require_permission("role.manage")
def create_role():
    dto = CreateRoleSchema().load(request.get_json() or {})
    service = _build_service()
    role = service.create_role(_tenant_id(), dto["name"], dto["permission_codes"])
    return jsonify({"success": True, "data": RoleSchema().dump(role), "meta": {}}), 201


@roles_bp.route("/<uuid:role_id>", methods=["PATCH"])
@jwt_required()
@require_permission("role.manage")
def update_role(role_id):
    dto = UpdateRoleSchema().load(request.get_json() or {})
    service = _build_service()
    role = service.update_role(
        _tenant_id(), role_id, name=dto.get("name"), permission_codes=dto.get("permission_codes")
    )
    return jsonify({"success": True, "data": RoleSchema().dump(role), "meta": {}})


@roles_bp.route("/<uuid:role_id>", methods=["DELETE"])
@jwt_required()
@require_permission("role.manage")
def delete_role(role_id):
    service = _build_service()
    service.delete_role(_tenant_id(), role_id)
    return jsonify({"success": True, "data": None, "meta": {}})


@roles_bp.route("/permissions", methods=["GET"])
@jwt_required()
@require_permission("admin.manage_users", "role.manage", "approval.manage_chains")
def list_permissions():
    # Same reasoning as list_roles: reading the catalog is safe for any
    # authenticated user, only creating/editing roles is gated.
    service = _build_service()
    permissions = service.list_permissions()
    return jsonify({"success": True, "data": PermissionSchema(many=True).dump(permissions), "meta": {}})
