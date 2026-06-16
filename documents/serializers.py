from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    encryption_key_code = serializers.CharField(source="encryption_key.key_code", read_only=True, default="")

    class Meta:
        model = Document
        fields = (
            "id", "case", "uploaded_by", "document_type", "original_filename",
            "file_size", "mime_type", "encryption_key_code", "checksum", "uploaded_at", "is_confidential",
        )
        read_only_fields = fields


class DocumentUploadSerializer(serializers.Serializer):
    case = serializers.IntegerField(required=False)
    document_type = serializers.CharField(max_length=100)
    file = serializers.FileField()
