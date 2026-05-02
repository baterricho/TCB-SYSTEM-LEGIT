"""
Views for the marketplace module.
Public endpoints require no authentication.
Management endpoints require admin access.
"""

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from core.permissions import IsAdmin
from core.exceptions import NotCertified
from applications.models import IPApplication
from .models import MarketplaceItem, InterestRequest
from .serializers import (
    PublicMarketplaceSerializer,
    MarketplaceItemSerializer,
    PublishToMarketplaceSerializer,
    InterestRequestSerializer,
)


class PublicMarketplaceListView(generics.ListAPIView):
    """GET /api/marketplace/ — Public marketplace listing (no auth required)."""

    permission_classes = [AllowAny]
    serializer_class = PublicMarketplaceSerializer
    search_fields = ["title", "abstract"]
    ordering_fields = ["created_at", "title"]

    def get_queryset(self):
        return (
            MarketplaceItem.objects
            .filter(is_public=True, is_archived=False)
            .select_related("application", "application__created_by")
            .prefetch_related("application__coinventors")
        )


class PublicMarketplaceDetailView(generics.RetrieveAPIView):
    """GET /api/marketplace/<id>/ — Public marketplace item detail (no auth)."""

    permission_classes = [AllowAny]
    serializer_class = PublicMarketplaceSerializer

    def get_queryset(self):
        return (
            MarketplaceItem.objects
            .filter(is_public=True, is_archived=False)
            .select_related("application", "application__created_by")
            .prefetch_related("application__coinventors")
        )


class SubmitInterestView(APIView):
    """POST /api/marketplace/<id>/interest/ — Submit interest (no auth required)."""

    permission_classes = [AllowAny]

    def post(self, request, pk):
        marketplace_item = get_object_or_404(
            MarketplaceItem, pk=pk, is_public=True
        )

        serializer = InterestRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interest = serializer.save(marketplace_item=marketplace_item)

        # Notify the IP owner about the interest
        from services.notification_service import send_notification
        send_notification(
            user=marketplace_item.application.created_by,
            message=(
                f"New interest received for '{marketplace_item.title}' "
                f"from {interest.requester_name} ({interest.requester_email})."
            ),
        )

        # Notify admins
        from accounts.models import User
        admins = User.objects.filter(role="admin", is_active=True)
        for admin in admins:
            send_notification(
                user=admin,
                message=(
                    f"Marketplace interest: {interest.requester_name} is interested "
                    f"in '{marketplace_item.title}'."
                ),
            )

        return Response(
            {"message": "Interest submitted successfully."},
            status=status.HTTP_201_CREATED,
        )


class PublishToMarketplaceView(APIView):
    """POST /api/marketplace/publish/ — Publish certified application to marketplace (admin only)."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = PublishToMarketplaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        application = get_object_or_404(IPApplication, pk=data["application_id"])

        # STRICT: Only certified applications can be published
        if application.status != "Certified":
            raise NotCertified()

        if not application.marketplace_consent:
            return Response(
                {
                    "error": (
                        "This application cannot be published until the applicant "
                        "grants marketplace consent."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if already published
        if hasattr(application, "marketplace_item"):
            return Response(
                {"error": "This application is already published."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        marketplace_item = MarketplaceItem.objects.create(
            application=application,
            title=data["title"],
            abstract=data["abstract"],
            is_public=data.get("is_public", True),
        )

        # Notify applicant
        from services.notification_service import send_notification
        send_notification(
            user=application.created_by,
            message=f"Your application '{application.title}' has been published to the marketplace!",
        )

        from services.audit_service import log_audit
        log_audit(
            user=request.user,
            action="PUBLISH_MARKETPLACE",
            entity=f"MarketplaceItem:{marketplace_item.id}",
        )

        return Response(
            {
                "message": "Published to marketplace successfully.",
                "item": MarketplaceItemSerializer(marketplace_item).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ManageMarketplaceListView(generics.ListAPIView):
    """GET /api/marketplace/manage/ — Admin view of all marketplace items."""

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = MarketplaceItemSerializer

    def get_queryset(self):
        return MarketplaceItem.objects.select_related(
            "application", "application__created_by"
        ).prefetch_related("interest_requests", "application__coinventors")


class InterestRequestListView(generics.ListAPIView):
    """GET /api/marketplace/<id>/interests/ — View interests for a marketplace item (admin/owner)."""

    permission_classes = [IsAuthenticated]
    serializer_class = InterestRequestSerializer

    def get_queryset(self):
        marketplace_item = get_object_or_404(MarketplaceItem, pk=self.kwargs["pk"])

        # Only admin or the IP owner can view interests
        user = self.request.user
        if user.role != "admin" and marketplace_item.application.created_by != user:
            return InterestRequest.objects.none()

        return InterestRequest.objects.filter(marketplace_item=marketplace_item)
