"""Shared API views."""

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .frontend import build_frontend_payload


def _is_local_frontend_url(url):
    return url.startswith(("http://127.0.0.1", "http://localhost", "https://localhost"))


def frontend_home_redirect(request):
    """Send browser visits at the backend root to the configured frontend."""
    if not settings.DEBUG and _is_local_frontend_url(settings.FRONTEND_DEFAULT_URL):
        return JsonResponse(
            {
                "name": "The Creator's Bulwark API",
                "status": "ok",
                "api_base_url": request.build_absolute_uri("/api/").rstrip("/"),
                "frontend_config_url": request.build_absolute_uri(
                    "/api/frontend-config/"
                ),
            }
        )
    return redirect(settings.FRONTEND_DEFAULT_URL)


class FrontendConfigView(APIView):
    """Expose frontend URLs used by this backend."""

    permission_classes = [AllowAny]

    def get(self, request):
        frontend = build_frontend_payload()
        frontend["api_base_url"] = request.build_absolute_uri("/api/").rstrip("/")
        return Response({"frontend": frontend})
