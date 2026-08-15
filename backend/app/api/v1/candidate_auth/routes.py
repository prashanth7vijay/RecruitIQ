from flask import Blueprint, request, jsonify

from app.api.v1.candidate_auth.schemas import CandidateSignupSchema, CandidateLoginSchema
from app.extensions import db, limiter
from app.repositories.candidate_repository import CandidateRepository
from app.services.candidate_auth_service import CandidateAuthService

candidate_auth_bp = Blueprint("candidate_auth", __name__, url_prefix="/api/v1/candidate-auth")


def _build_service() -> CandidateAuthService:
    return CandidateAuthService(candidate_repo=CandidateRepository(db.session))


@candidate_auth_bp.route("/signup", methods=["POST"])
@limiter.limit("10 per hour")
def signup():
    dto = CandidateSignupSchema().load(request.get_json() or {})
    service = _build_service()
    result = service.signup(
        email=dto["email"],
        password=dto["password"],
        first_name=dto["first_name"],
        last_name=dto["last_name"],
        phone=dto.get("phone"),
    )
    return jsonify({"success": True, "data": result, "meta": {}}), 201


@candidate_auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    dto = CandidateLoginSchema().load(request.get_json() or {})
    service = _build_service()
    result = service.login(email=dto["email"], password=dto["password"])
    return jsonify({"success": True, "data": result, "meta": {}})
