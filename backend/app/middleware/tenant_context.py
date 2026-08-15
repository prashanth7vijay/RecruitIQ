import uuid

from flask import g, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError

MUST_CHANGE_PASSWORD_ALLOWED_PATHS = {
    "/api/v1/auth/change-password",
    "/api/v1/auth/logout",
    "/api/v1/auth/logout-all",
    "/api/v1/auth/refresh",
}


def register_middleware(app):
    @app.before_request
    def load_request_context():
        g.request_id = str(uuid.uuid4())
        g.actor_id = None
        g.tenant_id = None
        g.role_id = None
        g.must_change_password = False

        if request.method == "OPTIONS":
            return  # CORS preflight — never blocked, carries no auth anyway

        try:
            verify_jwt_in_request(optional=True)
        except NoAuthorizationError:
            return  # public/unauthenticated route — leave context empty

        identity = get_jwt_identity()
        if identity is not None:
            claims = get_jwt()
            g.actor_id = identity
            g.tenant_id = claims.get("tenant_id")
            g.role_id = claims.get("role_id")
            g.must_change_password = bool(claims.get("must_change_password", False))

            if g.must_change_password and request.path not in MUST_CHANGE_PASSWORD_ALLOWED_PATHS:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": {
                                "code": "password_change_required",
                                "message": "You must change your temporary password before continuing.",
                                "details": None,
                            },
                            "meta": {"request_id": g.request_id},
                        }
                    ),
                    403,
                )

    @app.after_request
    def attach_request_id(response):
        response.headers["X-Request-ID"] = g.get("request_id", "")
        return response

    @app.after_request
    def set_secure_headers(response):
        # Per Phase 21.2 — explicit, not left as an unstated assumption.
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not app.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
