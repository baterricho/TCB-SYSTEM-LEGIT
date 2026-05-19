from rest_framework import serializers

from .models import FeeAssessment, Payment


class FeeAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeAssessment
        fields = (
            "id", "case", "application", "evaluator", "amount", "fee_type",
            "description", "status", "issued_at", "created_at", "updated_at",
        )
        read_only_fields = ("id", "evaluator", "issued_at", "created_at", "updated_at")


class PaymentSerializer(serializers.ModelSerializer):
    encryption_key_code = serializers.CharField(source="encryption_key.key_code", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id", "assessment", "case", "applicant", "amount_paid", "payment_method",
            "receipt_no", "original_filename", "file_size", "mime_type", "encryption_key_code",
            "checksum", "payment_status", "payment_date", "verified_by", "verified_at",
            "remarks", "created_at", "updated_at",
        )
        read_only_fields = fields


class PaymentUploadSerializer(serializers.Serializer):
    assessment = serializers.IntegerField()
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.CharField(max_length=80)
    receipt_no = serializers.CharField(max_length=100, required=False, allow_blank=True)
    payment_date = serializers.DateField(required=False)
    file = serializers.FileField()


class PaymentDecisionSerializer(serializers.Serializer):
    remarks = serializers.CharField(required=False, allow_blank=True)


PaymentProofSerializer = PaymentSerializer
