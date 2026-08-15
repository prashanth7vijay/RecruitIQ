from flask import Blueprint, request, jsonify, g, current_app
from flask_jwt_extended import jwt_required

from app.api.v1.admin.schemas import (
    AdminUserSchema,
    UpdateUserStatusSchema,
    UpdateUserRoleSchema,
    AuditLogEntrySchema,
    SystemHealthSchema,
    CreateUserSchema,
    CreatedUserSchema,
)
from app.exceptions.base import UnauthenticatedError, ValidationError
from app.extensions import db, limiter
from app.models.job import Job
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository, RefreshTokenRepository, LoginHistoryRepository
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.utils.permissions import require_permission

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@require_permission("admin.manage_users")
def list_users():
    repo = UserRepository(db.session)
    users = repo.list(_tenant_id()).all()
    return jsonify({"success": True, "data": AdminUserSchema(many=True).dump(users), "meta": {}})


@admin_bp.route("/users", methods=["POST"])
@jwt_required()
@require_permission("admin.manage_users")
@limiter.limit("30 per hour")  # bulk-inviting a team shouldn't be throttled tightly, but mass account creation is still worth capping
def create_user():
    """
    The replacement for the old open self-registration endpoint: an
    org_admin picks the email + role, the system generates the
    credential. See AuthService.admin_create_user for why (no client-
    supplied password on this path, no email dependency).
    """
    dto = CreateUserSchema().load(request.get_json() or {})
    tenant_id = _tenant_id()

    auth_service = AuthService(
        user_repo=UserRepository(db.session),
        refresh_token_repo=RefreshTokenRepository(db.session),
        login_history_repo=LoginHistoryRepository(db.session),
        company_repo=CompanyRepository(db.session),
        role_repo=RoleRepository(db.session),
        config=current_app.config,
    )
    user, raw_temp_password = auth_service.admin_create_user(
        tenant_id=tenant_id,
        email=dto["email"],
        first_name=dto["first_name"],
        last_name=dto["last_name"],
        role_id=dto["role_id"],
    )

    audit_service = AuditService(AuditLogRepository(db.session))
    audit_service.log(
        company_id=tenant_id, entity_type="User", entity_id=user.id, action="created", actor_id=g.actor_id
    )

    payload = CreatedUserSchema().dump(user)
    # The ONLY place this value ever appears — not stored, not logged,
    # not retrievable again after this response. The admin UI must show
    # it immediately and make clear it won't be shown again.
    payload["temp_password"] = raw_temp_password
    return jsonify({"success": True, "data": payload, "meta": {}}), 201


@admin_bp.route("/users/<uuid:user_id>/status", methods=["PATCH"])
@jwt_required()
@require_permission("admin.manage_users")
def update_user_status(user_id):
    dto = UpdateUserStatusSchema().load(request.get_json() or {})
    repo = UserRepository(db.session)
    tenant_id = _tenant_id()
    user = repo.get_or_404(user_id, tenant_id)

    old_status = user.status
    user.status = dto["status"]
    repo.commit()

    audit_service = AuditService(AuditLogRepository(db.session))
    audit_service.log(
        company_id=tenant_id, entity_type="User", entity_id=user.id, action="status_changed",
        old_value={"status": old_status}, new_value={"status": user.status},
    )
    return jsonify({"success": True, "data": AdminUserSchema().dump(user), "meta": {}})


@admin_bp.route("/users/<uuid:user_id>/role", methods=["PATCH"])
@jwt_required()
@require_permission("admin.manage_users")
def update_user_role(user_id):
    dto = UpdateUserRoleSchema().load(request.get_json() or {})
    tenant_id = _tenant_id()

    user_repo = UserRepository(db.session)
    user = user_repo.get_or_404(user_id, tenant_id)

    # A role must be visible to this tenant (system role, or one of its
    # own custom roles) to be assignable — get_visible_or_404 enforces
    # that instead of trusting the role_id came from this tenant's own
    # dropdown.
    role = RoleRepository(db.session).get_visible_or_404(dto["role_id"], tenant_id)

    old_role_name = user.role.name if user.role else None
    user.role_id = role.id
    user_repo.commit()

    audit_service = AuditService(AuditLogRepository(db.session))
    audit_service.log(
        company_id=tenant_id, entity_type="User", entity_id=user.id, action="role_changed",
        old_value={"role_name": old_role_name}, new_value={"role_name": role.name},
    )
    return jsonify({"success": True, "data": AdminUserSchema().dump(user), "meta": {}})


@admin_bp.route("/audit-logs", methods=["GET"])
@jwt_required()
@require_permission("admin.manage_users")
def list_audit_logs():
    from app.utils.pagination import paginate_query

    entity_type = request.args.get("entity_type")
    audit_service = AuditService(AuditLogRepository(db.session))
    query = audit_service.list_for_company(_tenant_id(), entity_type=entity_type)
    logs, pagination_meta = paginate_query(query)
    return jsonify({"success": True, "data": AuditLogEntrySchema(many=True).dump(logs), "meta": pagination_meta})


@admin_bp.route("/system-health", methods=["GET"])
@jwt_required()
@require_permission("admin.manage_users")
def system_health():
    tenant_id = _tenant_id()
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unreachable"

    user_count = UserRepository(db.session).list(tenant_id).count()
    active_job_count = db.session.query(Job).filter(
        Job.company_id == tenant_id, Job.status == "published"
    ).count()

    return jsonify({
        "success": True,
        "data": SystemHealthSchema().dump({
            "status": "ok" if db_status == "ok" else "degraded",
            "database": db_status,
            "user_count": user_count,
            "active_job_count": active_job_count,
        }),
        "meta": {},
    })
