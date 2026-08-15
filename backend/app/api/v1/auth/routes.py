from flask import Blueprint, request, jsonify, make_response, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.api.v1.auth.schemas import SignupCompanySchema, LoginSchema, UserSchema, CompanySchema, ChangePasswordSchema
from app.extensions import db, limiter
from app.repositories.company_repository import CompanyRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import (
    UserRepository,
    RefreshTokenRepository,
    LoginHistoryRepository,
)
from app.services.audit_service import AuditService
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.auth_service import AuthService
from app.utils.permissions import require_permission

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

REFRESH_COOKIE_NAME = "refresh_token"


def _build_auth_service() -> AuthService:
    return AuthService(
        user_repo=UserRepository(db.session),
        refresh_token_repo=RefreshTokenRepository(db.session),
        login_history_repo=LoginHistoryRepository(db.session),
        company_repo=CompanyRepository(db.session),
        role_repo=RoleRepository(db.session),
        config=current_app.config,
    )


def _set_refresh_cookie(response, raw_token):
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        raw_token,
        httponly=True,
        secure=not current_app.debug,
        samesite="Strict",
        max_age=60 * 60 * 24 * 30,
        path="/api/v1/auth",
    )


@auth_bp.route("/signup", methods=["POST"])
@limiter.limit("5 per hour")  # the highest-value target for abuse (mass company creation) gets the tightest limit
def signup():

    dto = SignupCompanySchema().load(request.get_json() or {})
    auth_service = _build_auth_service()
    company, user = auth_service.signup_company(
        company_name=dto["company_name"],
        company_slug=dto["company_slug"],
        email=dto["email"],
        password=dto["password"],
        first_name=dto["first_name"],
        last_name=dto["last_name"],
    )

    audit_service = AuditService(AuditLogRepository(db.session))
    audit_service.log(
        company_id=company.id, entity_type="Company", entity_id=company.id,
        action="created", actor_id=user.id,
    )

    return jsonify({
        "success": True,
        "data": {"company": CompanySchema().dump(company), "user": UserSchema().dump(user)},
        "meta": {},
    }), 201


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
@limiter.limit("10 per hour")
def change_password():
    
    dto = ChangePasswordSchema().load(request.get_json() or {})
    user_id = get_jwt_identity()

    auth_service = _build_auth_service()
    result = auth_service.change_password(
        user_id,
        current_password=dto["current_password"],
        new_password=dto["new_password"],
        ip_address=request.remote_addr,
        device_info={"user_agent": request.headers.get("User-Agent")},
    )

    response = make_response(
        jsonify({"success": True, "data": {"access_token": result["access_token"]}, "meta": {}})
    )
    _set_refresh_cookie(response, result["refresh_token"])
    return response


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")  # brute-force mitigation at the route layer, on top of account lockout
def login():
    dto = LoginSchema().load(request.get_json() or {})

    auth_service = _build_auth_service()
    result = auth_service.login(
        company_slug=dto["company_slug"],
        email=dto["email"],
        password=dto["password"],
        ip_address=request.remote_addr,
        device_info={"user_agent": request.headers.get("User-Agent")},
        remember_me=dto["remember_me"],
    )

    response = make_response(
        jsonify(
            {
                "success": True,
                "data": {
                    "access_token": result["access_token"],
                    "must_change_password": result["must_change_password"],
                },
                "meta": {},
            }
        )
    )
    _set_refresh_cookie(response, result["refresh_token"])
    return response


@auth_bp.route("/refresh", methods=["POST"])
@limiter.limit("30 per minute")
def refresh():

    raw_token = request.cookies.get(REFRESH_COOKIE_NAME) or (request.get_json(silent=True) or {}).get(
        "refresh_token"
    )
    auth_service = _build_auth_service()
    result = auth_service.refresh(
        raw_token,
        ip_address=request.remote_addr,
        device_info={"user_agent": request.headers.get("User-Agent")},
    )
    response = make_response(
        jsonify({"success": True, "data": {"access_token": result["access_token"]}, "meta": {}})
    )
    _set_refresh_cookie(response, result["refresh_token"])
    return response


@auth_bp.route("/logout", methods=["POST"])
def logout():
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    auth_service = _build_auth_service()
    if raw_token:
        auth_service.logout(raw_token)
    response = make_response(jsonify({"success": True, "data": None, "meta": {}}))
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth")
    return response


@auth_bp.route("/logout-all", methods=["POST"])
@jwt_required()
def logout_all():
    user_id = get_jwt_identity()
    auth_service = _build_auth_service()
    auth_service.logout_all(user_id)
    response = make_response(jsonify({"success": True, "data": None, "meta": {}}))
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth")
    return response


@auth_bp.route("/permissions", methods=["GET"])
@jwt_required()
def my_permissions():
    from app.models.role import Role

    claims = get_jwt()
    role_id = claims.get("role_id")
    role = db.session.query(Role).filter_by(id=role_id).first()
    codes = sorted(p.code for p in role.permissions) if role else []
    return jsonify({"success": True, "data": {"permissions": codes}, "meta": {}})
