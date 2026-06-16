from rest_framework import serializers

from .models import Inquiry


class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = (
            "id", "inquiry_code", "user", "listing", "sender_name", "email", "category", "subject",
            "message", "popularity_count", "status", "created_at", "updated_at",
        )
        read_only_fields = ("id", "inquiry_code", "user", "popularity_count", "created_at", "updated_at")


class InquiryAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = ("status", "popularity_count")
