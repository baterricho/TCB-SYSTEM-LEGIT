"""
Serializers for audit logs and encryption key management.
"""

from rest_framework import serializers
from .models import AuditLog, EncryptionKey


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for audit log entries."""

    user_name = serializers.CharField(
        source="user.full_name",
        read_only=True,
        default="System",
    )

    class Meta:
        model = AuditLog
        fields = ["id", "user", "user_name", "action", "entity", "timestamp"]
        read_only_fields = fields


class EncryptionKeySerializer(serializers.ModelSerializer):
    """
    Serializer for encryption key management.
    key_value is write-only — it gets encrypted before storage.
    The encrypted value is never exposed through the API.
    """

    key_value = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = EncryptionKey
        fields = ["id", "key_name", "key_value", "created_by", "created_at"]
        read_only_fields = ["id", "created_by", "created_at"]

    def create(self, validated_data):
        plaintext_value = validated_data.pop("key_value")
        key = EncryptionKey(**validated_data)
        key.set_key_value(plaintext_value)
        key.save()
        return key

    def update(self, instance, validated_data):
        if "key_value" in validated_data:
            plaintext_value = validated_data.pop("key_value")
            instance.set_key_value(plaintext_value)
        if "key_name" in validated_data:
            instance.key_name = validated_data["key_name"]
        instance.save()
        return instance


class EncryptionKeyListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer — no key values exposed."""

    created_by_name = serializers.CharField(
        source="created_by.full_name",
        read_only=True,
        default="Unknown",
    )

    class Meta:
        model = EncryptionKey
        fields = ["id", "key_name", "created_by", "created_by_name", "created_at"]
        read_only_fields = fields
