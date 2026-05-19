from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ("id", "log_timestamp", "user", "related_case", "account_name", "role", "action", "target", "record_id", "details", "ip_address", "user_agent")
        read_only_fields = fields
