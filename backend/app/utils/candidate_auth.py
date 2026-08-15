from functools import wraps

from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity

from app.exceptions.base import UnauthenticatedError


def require_candidate_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("actor_type") != "candidate":
            raise UnauthenticatedError("This endpoint requires a candidate account")
        g.candidate_id = get_jwt_identity()
        return fn(*args, **kwargs)

    return wrapper
