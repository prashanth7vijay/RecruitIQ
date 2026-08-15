from functools import wraps

from flask import g

from app.exceptions.base import UnauthenticatedError, PermissionDeniedError
from app.extensions import db
from app.models.role import Role


def require_permission(permission_code: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if g.get("actor_id") is None:
                raise UnauthenticatedError("Authentication required")

            role = db.session.query(Role).filter(Role.id == g.role_id).first()
            role_permission_codes = {p.code for p in role.permissions} if role else set()

            if permission_code not in role_permission_codes:
                raise PermissionDeniedError(f"Missing required permission: {permission_code}")

            return view_func(*args, **kwargs)

        return wrapper

    return decorator
