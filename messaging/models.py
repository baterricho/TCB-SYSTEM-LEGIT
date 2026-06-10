from django.conf import settings
from django.db import models


class Conversation(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="conversation_id")
    case = models.ForeignKey("cases.Case", on_delete=models.PROTECT, related_name="conversations", db_column="case_id")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="applicant_conversations", db_column="applicant_id")
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="evaluator_conversations", db_column="evaluator_id")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversation"
        ordering = ("-updated_at",)
        constraints = [
            models.UniqueConstraint(fields=["case", "applicant", "evaluator"], name="unique_case_applicant_evaluator_conversation"),
        ]

    def __str__(self):
        return f"Conversation {self.case.case_number}"


class Message(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="message_id")
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages", db_column="conversation_id")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sent_messages", db_column="sender_id")
    content = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    has_attachment = models.BooleanField(default=False)

    class Meta:
        db_table = "message"
        ordering = ("sent_at",)
        indexes = [
            models.Index(fields=["conversation", "sent_at"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["is_read"]),
        ]

    def __str__(self):
        return f"{self.sender.email} - {self.sent_at}"


class MessageAttachment(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="attachment_id")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments", db_index=True, db_column="message_id")
    file_path = models.FileField(upload_to="messages/attachments/")
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField()
    mime_type = models.CharField(max_length=150)
    is_encrypted = models.BooleanField(default=False)
    encryption_key = models.ForeignKey(
        "security_keys.EncryptionKey",
        on_delete=models.PROTECT,
        related_name="message_attachments",
        db_column="encryption_key_id",
        null=True,
        blank=True,
    )
    nonce = models.CharField(max_length=50, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "message_attachment"

    def __str__(self):
        return self.original_filename
