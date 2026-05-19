from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAdmin

from .models import EncryptionKey, KeyActivityLog
from .serializers import (
    EncryptionKeySerializer,
    GenerateEncryptionKeySerializer,
    KeyActivityLogSerializer,
    RotateEncryptionKeySerializer,
)
from .services import EncryptionKeyService


class EncryptionKeyViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = EncryptionKeySerializer
    queryset = EncryptionKey.objects.select_related("created_by").all()
    filterset_fields = ("status", "is_primary", "is_backup")
    search_fields = ("key_id", "key_name", "algorithm")

    @action(detail=False, methods=["post"], url_path="generate")
    def generate_key(self, request):
        serializer = GenerateEncryptionKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = EncryptionKeyService.generate_key(user=request.user, request=request, **serializer.validated_data)
        return Response(EncryptionKeySerializer(key).data, status=201)

    @action(detail=False, methods=["post"], url_path="rotate")
    def rotate_key(self, request):
        serializer = RotateEncryptionKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = EncryptionKeyService.rotate_primary_key(user=request.user, request=request, **serializer.validated_data)
        return Response(EncryptionKeySerializer(key).data)

    @action(detail=True, methods=["post"], url_path="disable")
    def disable_key(self, request, pk=None):
        key = self.get_object()
        key = EncryptionKeyService.disable_key(key=key, user=request.user, request=request)
        return Response(EncryptionKeySerializer(key).data)

    @action(detail=False, methods=["get"], url_path="escrow-report")
    def escrow_report(self, request):
        keys = EncryptionKey.objects.all()
        return Response({
            "total_keys": keys.count(),
            "active_primary": keys.filter(status=EncryptionKey.Status.ACTIVE, is_primary=True).values("key_code", "key_name", "created_at").first(),
            "active_backup_count": keys.filter(status=EncryptionKey.Status.ACTIVE, is_backup=True).count(),
            "rotated_count": keys.filter(status=EncryptionKey.Status.ROTATED).count(),
            "disabled_count": keys.filter(status=EncryptionKey.Status.DISABLED).count(),
        })

    @action(detail=False, methods=["get"], url_path="activity-logs")
    def activity_logs(self, request):
        logs = KeyActivityLog.objects.select_related("key", "performed_by").all()
        return Response(KeyActivityLogSerializer(logs, many=True).data)
