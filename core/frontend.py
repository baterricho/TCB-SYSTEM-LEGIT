"""Frontend route helpers shared by API views."""

from django.conf import settings


ROLE_FRONTEND_KEYS = {
    "admin": "admin",
    "evaluator": "evaluator",
    "applicant": "applicant",
}


def get_frontend_url_for_role(role):
    """Return the configured frontend URL for a backend user role."""
    key = ROLE_FRONTEND_KEYS.get(role, "general_viewer")
    return settings.FRONTEND_URLS.get(key, settings.FRONTEND_URLS["general_viewer"])


def build_frontend_payload(role=None):
    """Return frontend connection metadata for API clients."""
    redirect_url = (
        get_frontend_url_for_role(role)
        if role
        else settings.FRONTEND_URLS["general_viewer"]
    )
    return {
        "base_url": settings.FRONTEND_DEFAULT_URL,
        "redirect_url": redirect_url,
        "urls": settings.FRONTEND_URLS,
    }
