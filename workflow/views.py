"""
Views for workflow status management and notifications.
Thin controllers — all status transition logic is in services.

New endpoints:
  POST /api/workflow/applications/<id>/forward-to-ipophl/
    — Admin forwards a Certified application to IPOPHL.
  POST /api/workflow/applications/<id>/update-ipophl-status/
    — Admin manually updates the IPOPHL milestone status.
"""

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from core.permissions import IsAdmin, IsAdminOrEvaluator
from core.pagination import SmallResultsPagination
from applications.models import IPApplication
from .models import ApplicationStatusLog, Notification, CaseMessage, Announcement
from .serializers import (
    ApplicationStatusLogSerializer,
    NotificationSerializer,
    UpdateStatusRequestSerializer,
    CaseMessageSerializer,
    AnnouncementSerializer,
)


def _can_access_application(user, application):
    return (
        user.role == "admin"
        or application.created_by_id == user.id
        or application.assigned_evaluator_id == user.id
    )


class StatusLogListView(generics.ListAPIView):
    """GET /api/workflow/applications/<id>/logs/ — Get full status history for an application."""

    permission_classes = [IsAuthenticated]
    serializer_class = ApplicationStatusLogSerializer

    def get_queryset(self):
        application = get_object_or_404(
            IPApplication.objects.select_related("created_by", "assigned_evaluator"),
            pk=self.kwargs["pk"],
        )
        if not _can_access_application(self.request.user, application):
            raise PermissionDenied("You cannot view this application's status history.")
        return ApplicationStatusLog.objects.filter(
            application=application
        ).select_related("updated_by")


class UpdateStatusView(APIView):
    """
    POST /api/workflow/applications/<id>/update-status/
    Evaluator or admin updates application status (IPTTO stage only).
    Enforces strict state machine transitions via the service layer.
    """

    permission_classes = [IsAuthenticated, IsAdminOrEvaluator]

    def post(self, request, pk):
        application = get_object_or_404(
            IPApplication.objects.select_related("created_by", "assigned_evaluator"),
            pk=pk,
        )

        if request.user.role == "evaluator" and application.assigned_evaluator != request.user:
            return Response(
                {"error": "You are not the assigned evaluator for this application."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UpdateStatusRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]

        # Guard: evaluators cannot forward to IPOPHL directly (admin only)
        from services.workflow_service import IPOPHL_STAGE_STATUSES
        if new_status in IPOPHL_STAGE_STATUSES and request.user.role != "admin":
            return Response(
                {"error": "Only admins can update IPOPHL stage statuses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        from services.workflow_service import update_application_status
        update_application_status(
            application=application,
            user=request.user,
            new_status=new_status,
            remarks=serializer.validated_data.get("remarks", ""),
        )

        return Response(
            {"message": f"Status updated to '{new_status}'."},
            status=status.HTTP_200_OK,
        )


class ForwardToIPOPHLView(APIView):
    """
    POST /api/workflow/applications/<id>/forward-to-ipophl/
    Admin forwards a Certified application to IPOPHL.
    Transitions: Certified → Forwarded to IPOPHL.
    Body: { "remarks": "..." } (optional)
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        application = get_object_or_404(
            IPApplication.objects.select_related("created_by"),
            pk=pk,
        )

        if application.status != "Certified":
            return Response(
                {
                    "error": (
                        "Only applications with 'Certified' status can be forwarded to IPOPHL. "
                        f"Current status: '{application.status}'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        remarks = request.data.get("remarks", "Application forwarded to IPOPHL for national registration.")

        from services.workflow_service import update_application_status
        update_application_status(
            application=application,
            user=request.user,
            new_status="Forwarded to IPOPHL",
            remarks=remarks,
        )

        return Response(
            {
                "message": (
                    f"Application '{application.title}' has been forwarded to IPOPHL. "
                    f"The applicant has been notified."
                )
            },
            status=status.HTTP_200_OK,
        )


class UpdateIPOPHLStatusView(APIView):
    """
    POST /api/workflow/applications/<id>/update-ipophl-status/
    Admin manually records an IPOPHL milestone update received via email.
    Valid IPOPHL statuses: 'IPOPHL Under Review', 'IPOPHL Deficient', 'Registered'.
    Body: { "status": "...", "remarks": "..." }
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    VALID_IPOPHL_STATUSES = [
        "IPOPHL Under Review",
        "IPOPHL Deficient",
        "Registered",
    ]

    def post(self, request, pk):
        application = get_object_or_404(
            IPApplication.objects.select_related("created_by"),
            pk=pk,
        )

        new_status = request.data.get("status", "").strip()
        remarks = request.data.get("remarks", "")

        if new_status not in self.VALID_IPOPHL_STATUSES:
            return Response(
                {
                    "error": (
                        f"'{new_status}' is not a valid IPOPHL status. "
                        f"Valid options: {self.VALID_IPOPHL_STATUSES}"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from services.workflow_service import update_application_status
        update_application_status(
            application=application,
            user=request.user,
            new_status=new_status,
            remarks=remarks,
        )

        return Response(
            {"message": f"IPOPHL status updated to '{new_status}'."},
            status=status.HTTP_200_OK,
        )


# Case Messaging

class CaseMessageListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/workflow/applications/<id>/messages/ - Conversation for a case.
    POST /api/workflow/applications/<id>/messages/ - Applicant/evaluator sends a message.
    Admins can monitor messages but cannot send them.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CaseMessageSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_application(self):
        application = get_object_or_404(
            IPApplication.objects.select_related("created_by", "assigned_evaluator"),
            pk=self.kwargs["pk"],
        )
        if not _can_access_application(self.request.user, application):
            raise PermissionDenied("You cannot access this conversation.")
        return application

    def get_queryset(self):
        application = self.get_application()
        return CaseMessage.objects.filter(application=application).select_related("sender")

    def perform_create(self, serializer):
        application = self.get_application()
        user = self.request.user

        if user.role == "admin":
            raise PermissionDenied("Admins can monitor messages but cannot send them.")
        if user.role == "evaluator" and application.assigned_evaluator != user:
            raise PermissionDenied("You are not the assigned evaluator for this case.")
        if user.role == "applicant" and application.created_by != user:
            raise PermissionDenied("You can only message on your own case.")

        message = serializer.save(application=application, sender=user)

        from services.notification_service import send_notification
        recipients = []
        if user == application.created_by and application.assigned_evaluator:
            recipients.append(application.assigned_evaluator)
        elif application.created_by:
            recipients.append(application.created_by)

        for recipient in recipients:
            send_notification(
                user=recipient,
                message=(
                    f"New message for '{application.title}' "
                    f"from {user.full_name}."
                ),
            )

        from services.audit_service import log_audit
        log_audit(
            user=user,
            action="SEND_CASE_MESSAGE",
            entity=f"CaseMessage:{message.id}",
        )


# Announcements

class PublicAnnouncementListView(generics.ListAPIView):
    """GET /api/workflow/announcements/ - Public news/events/alerts feed."""

    permission_classes = [AllowAny]
    serializer_class = AnnouncementSerializer
    filterset_fields = ["category"]
    search_fields = ["title", "body"]
    ordering_fields = ["created_at", "title"]

    def get_queryset(self):
        return Announcement.objects.filter(is_published=True).select_related("created_by")


class AnnouncementManageListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/workflow/announcements/manage/ - Admin announcement manager."""

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AnnouncementSerializer
    filterset_fields = ["category", "is_published"]
    search_fields = ["title", "body"]
    ordering_fields = ["created_at", "title"]

    def get_queryset(self):
        return Announcement.objects.select_related("created_by")

    def perform_create(self, serializer):
        announcement = serializer.save(created_by=self.request.user)

        from services.audit_service import log_audit
        log_audit(
            user=self.request.user,
            action="CREATE_ANNOUNCEMENT",
            entity=f"Announcement:{announcement.id}",
        )


class AnnouncementManageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/workflow/announcements/manage/<id>/."""

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.select_related("created_by")


# ─── Notification Views ───────────────────────────────────────────────────────

class NotificationListView(generics.ListAPIView):
    """GET /api/workflow/notifications/ — List current user's notifications."""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = SmallResultsPagination

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class UnreadNotificationCountView(APIView):
    """GET /api/workflow/notifications/unread-count/ — Get unread notification count."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread_count": count})


class MarkNotificationReadView(APIView):
    """PATCH /api/workflow/notifications/<id>/read/ — Mark a single notification as read."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notification = get_object_or_404(
            Notification, pk=pk, user=request.user
        )
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read."})


class MarkAllNotificationsReadView(APIView):
    """POST /api/workflow/notifications/read-all/ — Mark all notifications as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        return Response({"message": f"{updated} notifications marked as read."})
