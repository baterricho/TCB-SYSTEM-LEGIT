"""Shared API views."""

from django.conf import settings
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .frontend import build_frontend_payload


def frontend_home_redirect(request):
    """Send browser visits at the backend root to the configured frontend."""
    return redirect(settings.FRONTEND_DEFAULT_URL)


class FrontendConfigView(APIView):
    """Expose frontend URLs used by this backend."""

    permission_classes = [AllowAny]

    def get(self, request):
        frontend = build_frontend_payload()
        frontend["api_base_url"] = request.build_absolute_uri("/api/").rstrip("/")
        return Response({"frontend": frontend})
