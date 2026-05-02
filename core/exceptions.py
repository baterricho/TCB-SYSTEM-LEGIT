"""
Custom exception classes for consistent API error responses.
"""

from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidStatusTransition(APIException):
    """Raised when an invalid workflow status transition is attempted."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid status transition."
    default_code = "invalid_status_transition"


class ApplicationNotSubmittable(APIException):
    """Raised when an application cannot be submitted (e.g., missing required fields)."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Application cannot be submitted in its current state."
    default_code = "application_not_submittable"


class NotCertified(APIException):
    """Raised when trying to publish a non-certified application to marketplace."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Only certified applications can be published to the marketplace."
    default_code = "not_certified"


class FileValidationError(APIException):
    """Raised when uploaded file fails validation."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "File validation failed."
    default_code = "file_validation_error"
