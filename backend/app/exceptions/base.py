class AppError(Exception):
    status_code = 500
    error_code = "internal_error"

    def __init__(self, message: str, details: list | None = None):
        super().__init__(message)
        self.message = message
        self.details = details

class ValidationError(AppError):
    status_code = 400
    error_code = "validation_error"


class UnauthenticatedError(AppError):
    status_code = 401
    error_code = "unauthenticated"


class PermissionDeniedError(AppError):
    status_code = 403
    error_code = "permission_denied"


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class InvalidTransitionError(AppError):
    """Raised when a state-machine transition is not permitted."""

    status_code = 409
    error_code = "invalid_transition"


class ConflictError(AppError):

    status_code = 409
    error_code = "conflict"


class BusinessRuleViolationError(AppError):
    status_code = 422
    error_code = "business_rule_violation"


class RateLimitedError(AppError):
    status_code = 429
    error_code = "rate_limited"
