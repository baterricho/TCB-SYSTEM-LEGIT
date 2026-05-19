from rest_framework import serializers

from .models import Announcement


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ("id", "admin", "title", "content", "category", "is_published", "created_at", "updated_at")
        read_only_fields = ("id", "admin", "created_at", "updated_at")
