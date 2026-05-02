"""
Audit Logging Middleware.
Automatically logs critical HTTP actions (POST, PUT, PATCH, DELETE)
to the AuditLog for full traceability.
"""

import logging

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware:
    """
    Middleware that automatically logs mutating requests (POST, PUT, PATCH, DELETE)
    to the audit log. Combined with the service-level audit_service for granular control.
    """

    # Paths to skip (avoid logging auth token refreshes, etc.)
    SKIP_PATHS = {
        "/api/accounts/token/refresh/",
        "/admin/jsi18n/",
    }

    # Only log mutating methods
    LOGGED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only log mutating requests that succeeded
        if (
            request.method in self.LOGGED_METHODS
            and request.path not in self.SKIP_PATHS
            and hasattr(request, "user")
            and request.user.is_authenticated
            and 200 <= response.status_code < 400
        ):
            try:
                from security.models import AuditLog

                AuditLog.objects.create(
                    user=request.user,
                    action=f"HTTP_{request.method}",
                    entity=request.path,
                )
            except Exception as e:
                # Never let audit logging break the request
                logger.warning(f"Audit middleware failed: {e}")

        return response
