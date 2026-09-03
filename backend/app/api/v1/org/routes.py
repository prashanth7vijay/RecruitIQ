from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required

from app.api.v1.org.schemas import (
    CreateDepartmentSchema,
    RenameDepartmentSchema,
    DepartmentSchema,
    CreateTeamSchema,
    UpdateTeamSchema,
    TeamSchema,
    CreateLocationSchema,
    UpdateLocationSchema,
    LocationSchema,
    UpdateUserOrgPlacementSchema,
)
from app.api.v1.admin.schemas import AdminUserSchema
from app.exceptions.base import UnauthenticatedError, ValidationError
from app.extensions import db
from app.repositories.department_repository import DepartmentRepository, TeamRepository, LocationRepository
from app.repositories.user_repository import UserRepository
from app.services.org_structure_service import OrgStructureService
from app.utils.permissions import require_permission

org_bp = Blueprint("org", __name__, url_prefix="/api/v1")


def _build_service() -> OrgStructureService:
    return OrgStructureService(
        department_repo=DepartmentRepository(db.session),
        team_repo=TeamRepository(db.session),
        location_repo=LocationRepository(db.session),
    )


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@org_bp.route("/departments", methods=["GET"])
@jwt_required()
@require_permission("org.manage_structure", "admin.manage_users")
def list_departments():
    service = _build_service()
    departments = service.list_departments(_tenant_id())
    return jsonify({"success": True, "data": DepartmentSchema(many=True).dump(departments), "meta": {}})


@org_bp.route("/departments", methods=["POST"])
@jwt_required()
@require_permission("org.manage_structure")
def create_department():
    dto = CreateDepartmentSchema().load(request.get_json() or {})
    service = _build_service()
    department = service.create_department(
        tenant_id=_tenant_id(), name=dto["name"], parent_id=dto.get("parent_id")
    )
    return jsonify({"success": True, "data": DepartmentSchema().dump(department), "meta": {}}), 201


@org_bp.route("/departments/<uuid:department_id>", methods=["GET"])
@jwt_required()
@require_permission("org.manage_structure", "admin.manage_users")
def get_department(department_id):
    service = _build_service()
    department = service.get_department(_tenant_id(), department_id)
    return jsonify({"success": True, "data": DepartmentSchema().dump(department), "meta": {}})


@org_bp.route("/departments/<uuid:department_id>", methods=["PATCH"])
@jwt_required()
@require_permission("org.manage_structure")
def rename_department(department_id):
    dto = RenameDepartmentSchema().load(request.get_json() or {})
    service = _build_service()
    department = service.rename_department(_tenant_id(), department_id, dto["name"])
    return jsonify({"success": True, "data": DepartmentSchema().dump(department), "meta": {}})


@org_bp.route("/departments/<uuid:department_id>", methods=["DELETE"])
@jwt_required()
@require_permission("org.manage_structure")
def delete_department(department_id):
    service = _build_service()
    service.delete_department(_tenant_id(), department_id)

    return jsonify({"success": True, "data": None, "meta": {}})


@org_bp.route("/teams", methods=["GET"])
@jwt_required()
@require_permission("org.manage_structure", "admin.manage_users")
def list_teams():
    department_id = request.args.get("department_id")
    service = _build_service()
    teams = service.list_teams(_tenant_id(), department_id=department_id)
    return jsonify({"success": True, "data": TeamSchema(many=True).dump(teams), "meta": {}})


@org_bp.route("/teams", methods=["POST"])
@jwt_required()
@require_permission("org.manage_structure")
def create_team():
    dto = CreateTeamSchema().load(request.get_json() or {})
    service = _build_service()
    team = service.create_team(
        tenant_id=_tenant_id(), name=dto["name"], department_id=dto.get("department_id")
    )
    return jsonify({"success": True, "data": TeamSchema().dump(team), "meta": {}}), 201


@org_bp.route("/teams/<uuid:team_id>", methods=["GET"])
@jwt_required()
@require_permission("org.manage_structure", "admin.manage_users")
def get_team(team_id):
    service = _build_service()
    team = service.get_team(_tenant_id(), team_id)
    return jsonify({"success": True, "data": TeamSchema().dump(team), "meta": {}})


@org_bp.route("/teams/<uuid:team_id>", methods=["PATCH"])
@jwt_required()
@require_permission("org.manage_structure")
def update_team(team_id):
    dto = UpdateTeamSchema().load(request.get_json() or {})
    service = _build_service()
    tenant_id = _tenant_id()
    team = service.get_team(tenant_id, team_id)
    if "name" in dto:
        team = service.rename_team(tenant_id, team_id, dto["name"])
    if "department_id" in dto:
        team = service.move_team(tenant_id, team_id, dto["department_id"])
    return jsonify({"success": True, "data": TeamSchema().dump(team), "meta": {}})


@org_bp.route("/teams/<uuid:team_id>", methods=["DELETE"])
@jwt_required()
@require_permission("org.manage_structure")
def delete_team(team_id):
    service = _build_service()
    service.delete_team(_tenant_id(), team_id)
    return jsonify({"success": True, "data": None, "meta": {}})


@org_bp.route("/locations", methods=["GET"])
@jwt_required()
@require_permission("org.manage_structure", "admin.manage_users")
def list_locations():
    service = _build_service()
    locations = service.list_locations(_tenant_id())
    return jsonify({"success": True, "data": LocationSchema(many=True).dump(locations), "meta": {}})


@org_bp.route("/locations", methods=["POST"])
@jwt_required()
@require_permission("org.manage_structure")
def create_location():
    dto = CreateLocationSchema().load(request.get_json() or {})
    service = _build_service()
    location = service.create_location(_tenant_id(), **dto)
    return jsonify({"success": True, "data": LocationSchema().dump(location), "meta": {}}), 201


@org_bp.route("/locations/<uuid:location_id>", methods=["PATCH"])
@jwt_required()
@require_permission("org.manage_structure")
def update_location(location_id):
    dto = UpdateLocationSchema().load(request.get_json() or {})
    service = _build_service()
    location = service.update_location(_tenant_id(), location_id, **dto)
    return jsonify({"success": True, "data": LocationSchema().dump(location), "meta": {}})


@org_bp.route("/locations/<uuid:location_id>", methods=["DELETE"])
@jwt_required()
@require_permission("org.manage_structure")
def delete_location(location_id):
    service = _build_service()
    service.delete_location(_tenant_id(), location_id)
    return jsonify({"success": True, "data": None, "meta": {}})


@org_bp.route("/users/<uuid:user_id>/org-placement", methods=["PATCH"])
@jwt_required()
@require_permission("org.manage_structure")
def update_user_org_placement(user_id):

    dto = UpdateUserOrgPlacementSchema().load(request.get_json() or {})
    tenant_id = _tenant_id()
    user_repo = UserRepository(db.session)
    user = user_repo.get_or_404(user_id, tenant_id)

    if "manager_id" in dto and dto["manager_id"] is not None:
        if dto["manager_id"] == user.id:
            raise ValidationError("A user cannot be their own manager")
        # Manager must be a real user in this tenant — get_or_404 enforces
        # both existence and tenant ownership, same reasoning as validating
        # parent_id when creating a department.
        user_repo.get_or_404(dto["manager_id"], tenant_id)

    if "department_id" in dto and dto["department_id"] is not None:
        DepartmentRepository(db.session).get_or_404(dto["department_id"], tenant_id)
    if "team_id" in dto and dto["team_id"] is not None:
        TeamRepository(db.session).get_or_404(dto["team_id"], tenant_id)
    if "location_id" in dto and dto["location_id"] is not None:
        LocationRepository(db.session).get_or_404(dto["location_id"], tenant_id)

    for field in ("department_id", "team_id", "manager_id", "location_id"):
        if field in dto:
            setattr(user, field, dto[field])
    user_repo.commit()

    return jsonify({"success": True, "data": AdminUserSchema().dump(user), "meta": {}})
