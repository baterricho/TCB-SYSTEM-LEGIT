from rest_framework import serializers

from .models import Bookmark, IPRecord, MarketListing


class IPRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPRecord
        fields = ("id", "case", "application", "encryption_key", "certification_date", "is_certified", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class MarketplaceListingSerializer(serializers.ModelSerializer):
    bookmark_count = serializers.IntegerField(read_only=True)
    created_by = serializers.IntegerField(source="admin_id", read_only=True)
    listing_id = serializers.CharField(source="listing_code", read_only=True)

    class Meta:
        model = MarketListing
        fields = (
            "id", "listing_id", "listing_code", "record", "admin", "title", "ip_type", "inventor_name", "short_description",
            "full_description", "category", "availability_status", "image", "status", "created_by",
            "is_active", "created_at", "updated_at", "bookmark_count",
        )
        read_only_fields = ("id", "listing_id", "listing_code", "admin", "created_by", "created_at", "updated_at", "bookmark_count")


class BookmarkSerializer(serializers.ModelSerializer):
    listing = MarketplaceListingSerializer(read_only=True)

    class Meta:
        model = Bookmark
        fields = ("id", "listing", "created_at")
        read_only_fields = fields


class BookmarkCreateSerializer(serializers.Serializer):
    listing = serializers.IntegerField()
