"""Shared exceptions for backend services."""


class BoldSignServiceError(Exception):
    """BoldSign or validation error surfaced to API clients."""

    def __init__(self, message: str, *, code: str = "boldsign_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code
