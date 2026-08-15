from flask import Blueprint, jsonify, g
from flask_jwt_extended import jwt_required

from app.api.v1.users.schemas import UserDirectoryEntrySchema
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
from app.repositories.user_repository import UserRepository

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@users_bp.route("", methods=["GET"])
@jwt_required()
def list_users():
    repo = UserRepository(db.session)
    users = repo.list(_tenant_id(), status="active").all()
    return jsonify({"success": True, "data": UserDirectoryEntrySchema(many=True).dump(users), "meta": {}})
