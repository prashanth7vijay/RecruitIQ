from flask import jsonify, g
from marshmallow import ValidationError as MarshmallowValidationError
from werkzeug.exceptions import HTTPException

from app.exceptions.base import AppError


def _envelope(error_code: str, message: str, details=None):
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details,
        },
        "meta": {
            "request_id": getattr(g, "request_id", None),
        },
    }


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        response = jsonify(_envelope(err.error_code, err.message, err.details))
        response.status_code = err.status_code
        return response

    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_error(err: MarshmallowValidationError):
        details = [
            {"field": field, "message": messages[0] if messages else "Invalid value"}
            for field, messages in err.messages.items()
        ]
        response = jsonify(_envelope("validation_error", "Request validation failed", details))
        response.status_code = 400
        return response

    @app.errorhandler(404)
    def handle_404(_err):
        response = jsonify(_envelope("not_found", "The requested resource was not found"))
        response.status_code = 404
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        code = (err.name or "http_error").lower().replace(" ", "_")
        response = jsonify(_envelope(code, err.description or err.name or "Request failed"))
        response.status_code = err.code or 500
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        app.logger.exception("Unhandled exception", exc_info=err)
        response = jsonify(_envelope("internal_error", "An unexpected error occurred"))
        response.status_code = 500
        return response
