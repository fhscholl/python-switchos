"""Custom exceptions for python-switchos library."""
from typing import List


class SaveError(Exception):
    """Raised when a POST request to save endpoint data fails.

    Attributes:
        status_code: HTTP status code from the response.
        response_text: Response body text (may be truncated in message).
        url: The URL that was requested.
        endpoint_name: Name of the endpoint class (e.g., "LinkEndpoint").
    """

    def __init__(
        self,
        status_code: int,
        response_text: str,
        url: str,
        endpoint_name: str = "",
    ) -> None:
        self.status_code = status_code
        self.response_text = response_text
        self.url = url
        self.endpoint_name = endpoint_name
        message = f"Save to {endpoint_name} failed ({status_code}): {response_text[:200]}"
        super().__init__(message)


class ValidationError(Exception):
    """Raised when field validation fails before POST.

    Attributes:
        errors: List of validation error strings describing each failure.
    """

    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        suffix = "..." if len(errors) > 3 else ""
        message = f"Validation failed with {len(errors)} error(s): {'; '.join(errors[:3])}{suffix}"
        super().__init__(message)
