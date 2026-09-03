from functools import wraps

from flask import g

from app.exceptions.base import UnauthenticatedError, PermissionDeniedError
from app.extensions import db
from app.models.role import Role


def require_permission(*permission_codes: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if g.get("actor_id") is None:
                raise UnauthenticatedError("Authentication required")

            role = db.session.query(Role).filter(Role.id == g.role_id).first()
            role_permission_codes = {p.code for p in role.permissions} if role else set()

            if not role_permission_codes.intersection(permission_codes):
                if len(permission_codes) == 1:
                    raise PermissionDeniedError(f"Missing required permission: {permission_codes[0]}")
                raise PermissionDeniedError(
                    f"Missing required permission (any of): {', '.join(permission_codes)}"
                )

            return view_func(*args, **kwargs)

        return wrapper

    return decorator
