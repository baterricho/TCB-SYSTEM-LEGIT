from rest_framework import serializers

from .models import IPOPHLEmailParse


class EmailParseSerializer(serializers.ModelSerializer):
    matched_case_number = serializers.CharField(source="matched_case.case_number", read_only=True)

    class Meta:
        model = IPOPHLEmailParse
        fields = (
            "id", "sender", "subject", "body", "case_number_detected", "report_type",
            "deadline_detected", "required_action", "attachments_metadata", "matched_case",
            "matched_case_number", "status", "created_at",
        )
        read_only_fields = ("id", "case_number_detected", "report_type", "deadline_detected", "required_action", "matched_case", "matched_case_number", "status", "created_at")


class ParseEmailSerializer(serializers.Serializer):
    sender = serializers.EmailField()
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()
    attachments_metadata = serializers.JSONField(required=False)


class MatchEmailSerializer(serializers.Serializer):
    case = serializers.IntegerField()
