from rest_framework import serializers

from .models import Conversation, Message, MessageAttachment


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ("id", "original_filename", "file_size", "mime_type", "file_path", "uploaded_at")
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ("id", "conversation", "sender", "sender_name", "content", "sent_at", "is_read", "has_attachment", "attachments")
        read_only_fields = ("id", "conversation", "sender", "sender_name", "sent_at", "is_read", "has_attachment", "attachments")


class ConversationSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="case.case_number", read_only=True)
    applicant_name = serializers.CharField(source="applicant.get_full_name", read_only=True)
    evaluator_name = serializers.CharField(source="evaluator.get_full_name", read_only=True)

    class Meta:
        model = Conversation
        fields = ("id", "case", "case_number", "applicant", "applicant_name", "evaluator", "evaluator_name", "created_at", "updated_at")
        read_only_fields = fields


class ConversationCreateSerializer(serializers.Serializer):
    case = serializers.IntegerField()


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True)
    files = serializers.ListField(child=serializers.FileField(), required=False, allow_empty=True)
