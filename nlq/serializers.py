from rest_framework import serializers

from .models import NLQQuery


class NLQProcessSerializer(serializers.Serializer):
    query = serializers.CharField()


class NLQQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = NLQQuery
        fields = ("id", "user", "raw_query", "detected_intent", "extracted_filters", "result_count", "created_at")
        read_only_fields = fields
