from rest_framework import serializers

from applications.serializers import IPApplicationSerializer

from .models import ActivityTimeline, Case, CaseEvaluation, CaseStatusHistory


class CaseStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.get_full_name", read_only=True, default="")

    class Meta:
        model = CaseStatusHistory
        fields = ("id", "previous_status", "new_status", "changed_by", "changed_by_name", "changed_at", "remarks")
        read_only_fields = fields


class ActivityTimelineSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source="performed_by.get_full_name", read_only=True, default="")

    class Meta:
        model = ActivityTimeline
        fields = ("id", "role_visibility", "action", "applicant_message", "admin_message", "performed_by", "performed_by_name", "created_at")
        read_only_fields = fields


class CaseEvaluationSerializer(serializers.ModelSerializer):
    evaluator_name = serializers.CharField(source="evaluator.get_full_name", read_only=True)

    class Meta:
        model = CaseEvaluation
        fields = ("id", "case", "evaluator", "evaluator_name", "content", "recommendation", "created_at", "updated_at")
        read_only_fields = ("id", "case", "evaluator", "evaluator_name", "created_at", "updated_at")


class CaseSerializer(serializers.ModelSerializer):
    application = IPApplicationSerializer(read_only=True)
    application_code = serializers.CharField(source="application.application_code", read_only=True)
    ip_type = serializers.CharField(source="application.ip_type", read_only=True)
    title = serializers.CharField(source="application.title", read_only=True)
    submitted_at = serializers.DateTimeField(source="application.submitted_at", read_only=True)
    applicant_email = serializers.EmailField(source="applicant.email", read_only=True)
    applicant_name = serializers.CharField(source="applicant.get_full_name", read_only=True)
    evaluator_name = serializers.CharField(source="taken_by.get_full_name", read_only=True, default="")
    status_history = CaseStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = (
            "id", "case_number", "application", "application_code", "ip_type", "title",
            "submitted_at", "applicant", "applicant_name", "applicant_email",
            "assigned_evaluator", "taken_by", "evaluator_name", "is_taken", "taken_at", "status",
            "priority_label", "priority_score", "deadline", "sla_stage", "sla_due_date",
            "evaluation_summary", "evaluator_recommendation", "created_at", "updated_at", "status_history",
        )
        read_only_fields = fields


class CaseStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Case.Status.choices)
    remarks = serializers.CharField(required=False, allow_blank=True)


class CaseDeadlineSerializer(serializers.Serializer):
    deadline = serializers.DateTimeField()
    sla_stage = serializers.CharField(required=False, allow_blank=True)


class EvaluationSubmitSerializer(serializers.Serializer):
    content = serializers.CharField()
    recommendation = serializers.CharField(required=False, allow_blank=True)
