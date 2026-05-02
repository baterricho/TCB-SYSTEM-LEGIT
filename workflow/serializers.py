"""Serializers for status logs, notifications, messages, and announcements."""

from rest_framework import serializers
from .models import ApplicationStatusLog, Notification, CaseMessage, Announcement


class ApplicationStatusLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for status log timeline."""

    updated_by_name = serializers.CharField(
        source="updated_by.full_name",
        read_only=True,
        default="System",
    )

    class Meta:
        model = ApplicationStatusLog
        fields = [
            "id", "application", "status", "remarks",
            "updated_by", "updated_by_name", "timestamp",
        ]
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notification listing and read status updates."""

    class Meta:
        model = Notification
        fields = [
            "id", "message", "notification_type",
            "is_read", "created_at",
        ]
        read_only_fields = ["id", "message", "notification_type", "created_at"]


class UpdateStatusRequestSerializer(serializers.Serializer):
    """Validates status update requests (supports both IPTTO and IPOPHL stage statuses)."""

    status = serializers.CharField(max_length=30)
    remarks = serializers.CharField(required=False, default="", allow_blank=True)


class CaseMessageSerializer(serializers.ModelSerializer):
    """Serializer for applicant/evaluator case conversations."""

    sender_name = serializers.CharField(source="sender.full_name", read_only=True, default=None)
    sender_role = serializers.CharField(source="sender.role", read_only=True, default=None)

    class Meta:
        model = CaseMessage
        fields = [
            "id", "application", "sender", "sender_name", "sender_role",
            "body", "attachment", "is_read", "created_at",
        ]
        read_only_fields = [
            "id", "application", "sender", "sender_name",
            "sender_role", "is_read", "created_at",
        ]

    def validate(self, attrs):
        if not attrs.get("body") and not attrs.get("attachment"):
            raise serializers.ValidationError(
                "A message must include text or an attachment."
            )
        return attrs


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for public and admin-managed announcements."""

    created_by_name = serializers.CharField(
        source="created_by.full_name",
        read_only=True,
        default=None,
    )

    class Meta:
        model = Announcement
        fields = [
            "id", "title", "body", "category", "is_published",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_by_name", "created_at", "updated_at"]
