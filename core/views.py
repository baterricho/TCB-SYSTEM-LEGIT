from django.conf import settings
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import CustomUser
from accounts.serializers import UserSerializer
from applications.models import IPApplication
from applications.serializers import IPApplicationSerializer
from core.permissions import IsAdmin
from messaging.models import Conversation
from messaging.serializers import ConversationSerializer


class AdminSubmissionsView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = IPApplicationSerializer

    def get_queryset(self):
        return IPApplication.objects.select_related("applicant").all()


class AdminUsersView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = UserSerializer

    def get_queryset(self):
        return CustomUser.objects.all().order_by("-created_at")


class AdminConversationsView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.select_related("case", "applicant", "evaluator").all()


class SystemConfigView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        admin_email = ""
        admins = getattr(settings, "ADMINS", ())
        if admins:
            admin_email = admins[0][1] if isinstance(admins[0], (list, tuple)) and len(admins[0]) > 1 else ""
        notification_email_enabled = bool(getattr(settings, "EMAIL_HOST", "") and getattr(settings, "DEFAULT_FROM_EMAIL", ""))
        return Response(
            {
                "system_name": "The Creator's Bulwark",
                "institution": getattr(settings, "TCB_INSTITUTION", ""),
                "admin_email": getattr(settings, "TCB_ADMIN_EMAIL", admin_email),
                "notification_email_enabled": notification_email_enabled,
                "timezone": settings.TIME_ZONE,
                "max_upload_size": settings.MAX_UPLOAD_SIZE,
                "allowed_document_extensions": ["pdf", "doc", "docx", "jpg", "jpeg", "png"],
                "allowed_payment_extensions": ["pdf", "docx", "jpg", "jpeg", "png"],
                "authentication": {
                    "access_token_minutes": int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds() // 60),
                    "refresh_token_days": settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].days,
                    "roles": ["admin", "evaluator", "applicant"],
                },
            }
        )
