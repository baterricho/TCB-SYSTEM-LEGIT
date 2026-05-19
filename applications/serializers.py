from rest_framework import serializers

from .models import ApplicationChecklist, IPApplication


class ApplicationChecklistSerializer(serializers.ModelSerializer):
    display_status = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ApplicationChecklist
        fields = ("id", "item_name", "status", "display_status", "remarks")
        read_only_fields = fields


class IPApplicationSerializer(serializers.ModelSerializer):
    checklist_items = ApplicationChecklistSerializer(many=True, read_only=True)
    applicant_email = serializers.EmailField(source="applicant.email", read_only=True)

    class Meta:
        model = IPApplication
        fields = (
            "id", "application_code", "applicant", "applicant_email", "ip_type", "title",
            "description", "abstract", "claims", "technical_explanation", "novelty_explanation",
            "supporting_details", "declaration_accepted", "status", "completeness_score",
            "language_validation_status", "created_at", "submitted_at", "updated_at", "checklist_items",
        )
        read_only_fields = (
            "id", "application_code", "applicant", "applicant_email", "status", "completeness_score",
            "language_validation_status", "created_at", "submitted_at", "updated_at", "checklist_items",
        )


class CompletenessResultSerializer(serializers.Serializer):
    completeness_score = serializers.IntegerField()
    checklist = ApplicationChecklistSerializer(many=True)
