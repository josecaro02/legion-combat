"""Custom application exceptions."""


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 500, code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code

    def to_dict(self) -> dict:
        """Convert error to dictionary."""
        return {
            'error': self.code,
            'message': self.message,
        }


class AuthenticationError(AppError):
    """Authentication error."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401, code="AUTHENTICATION_ERROR")


class AuthorizationError(AppError):
    """Authorization error."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403, code="AUTHORIZATION_ERROR")


class NotFoundError(AppError):
    """Resource not found error."""

    def __init__(self, resource: str = "Resource"):
        super().__init__(
            f"{resource} not found",
            status_code=404,
            code="NOT_FOUND"
        )
        self.resource = resource


class ValidationError(AppError):
    """Validation error."""

    def __init__(self, message: str = "Validation failed", errors: dict = None):
        super().__init__(message, status_code=400, code="VALIDATION_ERROR")
        self.errors = errors or {}

    def to_dict(self) -> dict:
        """Convert error to dictionary with validation details."""
        result = super().to_dict()
        if self.errors:
            result['errors'] = self.errors
        return result


class BusinessError(AppError):
    """Business logic error."""

    def __init__(self, message: str = "Business rule violation"):
        super().__init__(message, status_code=409, code="BUSINESS_ERROR")


class ConflictError(AppError):
    """Conflict error."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409, code="CONFLICT")


class RateLimitError(AppError):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429, code="RATE_LIMIT")
