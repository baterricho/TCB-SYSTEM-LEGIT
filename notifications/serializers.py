from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "recipient", "related_case", "notification_type", "title", "content", "role_visibility", "is_read", "created_at")
        read_only_fields = fields
