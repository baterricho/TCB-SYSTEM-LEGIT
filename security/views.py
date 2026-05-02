"""
Views for security module: audit logs and encryption key management.
All endpoints are admin-only.
"""

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from core.permissions import IsAdmin
from .models import AuditLog, EncryptionKey
from .serializers import (
    AuditLogSerializer,
    EncryptionKeySerializer,
    EncryptionKeyListSerializer,
)


class AuditLogListView(generics.ListAPIView):
    """GET /api/security/audit-logs/ — List all audit logs (admin only)."""

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("user")
    filterset_fields = ["action"]
    search_fields = ["action", "entity", "user__full_name"]
    ordering_fields = ["timestamp", "action"]


class EncryptionKeyListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/security/encryption-keys/ — List all encryption keys (admin only).
    POST /api/security/encryption-keys/ — Create a new encryption key (admin only).
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EncryptionKeySerializer
        return EncryptionKeyListSerializer

    def get_queryset(self):
        return EncryptionKey.objects.select_related("created_by")

    def perform_create(self, serializer):
        key = serializer.save(created_by=self.request.user)

        from services.audit_service import log_audit
        log_audit(
            user=self.request.user,
            action="CREATE_ENCRYPTION_KEY",
            entity=f"EncryptionKey:{key.id}",
        )


class EncryptionKeyDetailView(APIView):
    """
    GET    /api/security/encryption-keys/<id>/ — Get key metadata (admin only).
    PUT    /api/security/encryption-keys/<id>/ — Update key (admin only).
    DELETE /api/security/encryption-keys/<id>/ — Delete key (admin only).
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, pk):
        key = get_object_or_404(EncryptionKey, pk=pk)
        return Response(EncryptionKeyListSerializer(key).data)

    def put(self, request, pk):
        key = get_object_or_404(EncryptionKey, pk=pk)
        serializer = EncryptionKeySerializer(key, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        from services.audit_service import log_audit
        log_audit(
            user=request.user,
            action="UPDATE_ENCRYPTION_KEY",
            entity=f"EncryptionKey:{key.id}",
        )

        return Response(EncryptionKeyListSerializer(key).data)

    def delete(self, request, pk):
        key = get_object_or_404(EncryptionKey, pk=pk)

        from services.audit_service import log_audit
        log_audit(
            user=request.user,
            action="DELETE_ENCRYPTION_KEY",
            entity=f"EncryptionKey:{key.id}",
        )

        key.delete()
        return Response(
            {"message": "Encryption key deleted."},
            status=status.HTTP_200_OK,
        )
