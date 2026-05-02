"""Serializers for IP applications, requirements, payments, and co-inventors."""

from rest_framework import serializers
from .models import (
    IPApplication,
    IPDocument,
    IPRequirement,
    PaymentRecord,
    CoInventor,
)
from accounts.serializers import UserListSerializer


class CoInventorSerializer(serializers.ModelSerializer):
    """Serializer for co-inventor management."""

    class Meta:
        model = CoInventor
        fields = ["id", "name", "email"]
        read_only_fields = ["id"]


class IPDocumentSerializer(serializers.ModelSerializer):
    """Serializer for document upload, listing, and stamp status."""

    reviewed_by_name = serializers.CharField(
        source="reviewed_by.full_name",
        read_only=True,
        default=None,
    )
    is_stamped = serializers.BooleanField(read_only=True)

    class Meta:
        model = IPDocument
        fields = [
            "id", "file", "document_type", "original_filename",
            "uploaded_at", "reviewed_by", "reviewed_by_name",
            "reviewed_at", "is_stamped",
        ]
        read_only_fields = [
            "id", "original_filename", "uploaded_at",
            "reviewed_by", "reviewed_by_name", "reviewed_at", "is_stamped",
        ]

    def create(self, validated_data):
        # Store the original filename before Django renames it
        file_obj = validated_data.get("file")
        if file_obj:
            validated_data["original_filename"] = file_obj.name
        return super().create(validated_data)


class IPRequirementSerializer(serializers.ModelSerializer):
    """Public/applicant checklist serializer for IP service requirements."""

    class Meta:
        model = IPRequirement
        fields = [
            "id", "ip_type", "title", "description", "category",
            "expected_document_type", "is_required", "sort_order",
        ]
        read_only_fields = fields


class PaymentRecordSerializer(serializers.ModelSerializer):
    """Serializer for proof-of-payment tracking."""

    verified_by_name = serializers.CharField(
        source="verified_by.full_name",
        read_only=True,
        default=None,
    )

    class Meta:
        model = PaymentRecord
        fields = [
            "id", "application", "amount_due", "reference_number",
            "receipt_document", "status", "notes", "verified_by",
            "verified_by_name", "verified_at", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "application", "status", "verified_by",
            "verified_by_name", "verified_at", "created_at", "updated_at",
        ]


class PaymentVerificationSerializer(serializers.Serializer):
    """Validate evaluator/admin receipt verification decisions."""

    status = serializers.ChoiceField(choices=["Verified", "Rejected"])
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class IPApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for application list views."""

    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    evaluator_name = serializers.CharField(
        source="assigned_evaluator.full_name",
        read_only=True,
        default=None,
    )
    document_count = serializers.IntegerField(source="documents.count", read_only=True)
    payment_count = serializers.IntegerField(source="payments.count", read_only=True)

    class Meta:
        model = IPApplication
        fields = [
            "id", "transaction_code", "title", "ip_type", "status", "stage",
            "created_by", "created_by_name",
            "assigned_evaluator", "evaluator_name",
            "document_count", "payment_count", "marketplace_consent",
            "is_archived",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class IPApplicationSerializer(serializers.ModelSerializer):
    """Full serializer with nested documents, co-inventors, and all IP fields."""

    created_by_detail = UserListSerializer(source="created_by", read_only=True)
    evaluator_detail = UserListSerializer(source="assigned_evaluator", read_only=True)
    documents = IPDocumentSerializer(many=True, read_only=True)
    coinventors = CoInventorSerializer(many=True, read_only=True)
    payments = PaymentRecordSerializer(many=True, read_only=True)

    class Meta:
        model = IPApplication
        fields = [
            "id", "transaction_code", "title", "description", "ip_type", "status", "stage",
            # Copyright identifiers
            "isbn", "issn", "ismn",
            # Marketplace
            "marketplace_consent",
            # Relations
            "created_by", "created_by_detail",
            "assigned_evaluator", "evaluator_detail",
            "documents", "coinventors", "payments",
            # Archive
            "is_archived", "archived_at", "archived_by", "archive_reason",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "transaction_code", "status", "stage",
            "created_by", "assigned_evaluator",
            "is_archived", "archived_at", "archived_by", "archive_reason",
            "created_at", "updated_at",
        ]


class IPApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer specifically for creating new applications."""

    coinventors = CoInventorSerializer(many=True, required=False)

    class Meta:
        model = IPApplication
        fields = [
            "id", "transaction_code", "title", "description", "ip_type",
            # Copyright identifiers (optional, Copyright type only)
            "isbn", "issn", "ismn",
            # Marketplace consent — applicant sets this at draft time or later
            "marketplace_consent",
            "coinventors",
        ]
        read_only_fields = ["id", "transaction_code"]

    def validate(self, attrs):
        ip_type = attrs.get("ip_type", "")
        # ISBN/ISSN/ISMN only make sense for Copyright type
        if ip_type != "Copyright":
            for field in ["isbn", "issn", "ismn"]:
                if attrs.get(field):
                    raise serializers.ValidationError(
                        {field: f"{field.upper()} is only applicable for Copyright applications."}
                    )
        return attrs

    def create(self, validated_data):
        coinventors_data = validated_data.pop("coinventors", [])
        application = IPApplication.objects.create(**validated_data)
        for coinventor_data in coinventors_data:
            CoInventor.objects.create(application=application, **coinventor_data)
        return application


class MarketplaceConsentSerializer(serializers.Serializer):
    """Update applicant's marketplace consent on their own application."""

    marketplace_consent = serializers.BooleanField()


class StampDocumentSerializer(serializers.Serializer):
    """Used by evaluators to apply a 'Reviewed By' stamp to a document."""

    # No body required — reviewer identity comes from request.user
    pass


class ArchiveApplicationSerializer(serializers.Serializer):
    """Archive or restore an application from the admin queue."""

    is_archived = serializers.BooleanField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")
