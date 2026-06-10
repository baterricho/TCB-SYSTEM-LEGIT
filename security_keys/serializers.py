from rest_framework import serializers

from .models import EncryptionKey, KeyActivityLog


class EncryptionKeySerializer(serializers.ModelSerializer):
    masked_key_material = serializers.SerializerMethodField()
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True, default="")

    class Meta:
        model = EncryptionKey
        fields = (
            "id", "key_code", "key_name", "algorithm", "status", "masked_key_material",
            "created_by", "created_by_email", "created_at", "rotated_at", "disabled_at",
            "rotation_policy", "is_primary", "is_backup",
        )
        read_only_fields = fields

    def get_masked_key_material(self, obj):
        return f"{obj.key_code[:7]}********"


class GenerateEncryptionKeySerializer(serializers.Serializer):
    key_name = serializers.CharField(max_length=150)
    rotation_policy = serializers.CharField(required=False, allow_blank=True)
    is_primary = serializers.BooleanField(default=True)
    is_backup = serializers.BooleanField(default=False)


class RotateEncryptionKeySerializer(serializers.Serializer):
    key_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    rotation_policy = serializers.CharField(required=False, allow_blank=True)


class KeyActivityLogSerializer(serializers.ModelSerializer):
    key_code = serializers.CharField(source="key.key_code", read_only=True)
    performed_by_email = serializers.EmailField(source="performed_by.email", read_only=True, default="")

    class Meta:
        model = KeyActivityLog
        fields = ("id", "key", "key_code", "action", "performed_by", "performed_by_email", "created_at", "details", "ip_address")
        read_only_fields = fields
