"""
Serializers for marketplace items and interest requests.
"""

from rest_framework import serializers
from .models import MarketplaceItem, InterestRequest


class PublicMarketplaceSerializer(serializers.ModelSerializer):
    """Public listing serializer — limited fields, no sensitive data."""

    ip_type = serializers.CharField(source="application.ip_type", read_only=True)
    owner_name = serializers.CharField(source="application.created_by.full_name", read_only=True)
    contact_email = serializers.EmailField(source="application.created_by.email", read_only=True)
    co_inventors = serializers.SerializerMethodField()

    class Meta:
        model = MarketplaceItem
        fields = [
            "id", "title", "abstract", "ip_type",
            "owner_name", "contact_email", "co_inventors", "created_at",
        ]
        read_only_fields = fields

    def get_co_inventors(self, obj):
        return [coinventor.name for coinventor in obj.application.coinventors.all()]


class MarketplaceItemSerializer(serializers.ModelSerializer):
    """Full serializer for admin/owner management."""

    ip_type = serializers.CharField(source="application.ip_type", read_only=True)
    applicant_name = serializers.CharField(
        source="application.created_by.full_name", read_only=True
    )
    interest_count = serializers.IntegerField(
        source="interest_requests.count", read_only=True
    )

    class Meta:
        model = MarketplaceItem
        fields = [
            "id", "application", "title", "abstract",
            "is_public", "is_archived", "archived_at",
            "ip_type", "applicant_name", "interest_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "archived_at", "created_at", "updated_at"]


class PublishToMarketplaceSerializer(serializers.Serializer):
    """Validates marketplace publish requests."""

    application_id = serializers.UUIDField()
    title = serializers.CharField(max_length=500)
    abstract = serializers.CharField()
    is_public = serializers.BooleanField(default=True)


class InterestRequestSerializer(serializers.ModelSerializer):
    """Serializer for public interest submission."""

    class Meta:
        model = InterestRequest
        fields = ["id", "requester_name", "requester_email", "message", "created_at"]
        read_only_fields = ["id", "created_at"]
