from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1.notifications.schemas import NotificationSchema
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/v1/notifications")


def _build_service() -> NotificationService:
    return NotificationService(notification_repo=NotificationRepository(db.session))


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@notifications_bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    from app.utils.pagination import paginate_query

    unread_only = request.args.get("unread") == "true"
    query = NotificationRepository(db.session).list_for_user(_tenant_id(), get_jwt_identity(), unread_only=unread_only)
    notifications, pagination_meta = paginate_query(query)
    return jsonify({"success": True, "data": NotificationSchema(many=True).dump(notifications), "meta": pagination_meta})


@notifications_bp.route("/<uuid:notification_id>/read", methods=["PATCH"])
@jwt_required()
def mark_read(notification_id):
    service = _build_service()
    notification = service.mark_read(_tenant_id(), notification_id)
    return jsonify({"success": True, "data": NotificationSchema().dump(notification), "meta": {}})
