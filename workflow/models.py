"""
Application Status Log, Notification, Messaging, and Announcement models.
"""

import uuid
from django.db import models
from django.conf import settings
from core.utils.file_validators import generate_upload_path, validate_file_extension, validate_file_size


class ApplicationStatusLog(models.Model):
    """
    Immutable audit trail of every status change on an application.
    Solves the 'communication black hole' problem by logging
    every transition with remarks and timestamp.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        "applications.IPApplication",
        on_delete=models.CASCADE,
        related_name="status_logs",
    )
    status = models.CharField(max_length=20)
    remarks = models.TextField(blank=True, default="")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="status_updates",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["application", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.application.title} → {self.status} ({self.timestamp})"


class Notification(models.Model):
    """
    System notifications for users.
    Supports both system dashboard alerts and email notifications.
    """

    TYPE_CHOICES = (
        ("system", "System"),
        ("email", "Email"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.TextField()
    notification_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default="system",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"[{status}] {self.message[:50]}..."


class CaseMessage(models.Model):
    """
    Conversation message scoped to one IP application.
    Applicants and assigned evaluators can send messages; admins monitor them.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        "applications.IPApplication",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="case_messages",
    )
    body = models.TextField(blank=True, default="")
    attachment = models.FileField(
        upload_to=generate_upload_path,
        validators=[validate_file_extension, validate_file_size],
        blank=True,
        null=True,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["application", "created_at"]),
            models.Index(fields=["sender", "-created_at"]),
            models.Index(fields=["is_read"]),
        ]

    def __str__(self):
        sender = self.sender.full_name if self.sender else "System"
        return f"{self.application.transaction_code} message from {sender}"


class Announcement(models.Model):
    """
    News, event, alert, or system announcement shown on dashboards/landing pages.
    """

    CATEGORY_CHOICES = (
        ("news", "News"),
        ("event", "Event"),
        ("alert", "Alert"),
        ("system", "System"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    body = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="news")
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["is_published", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_category_display()}: {self.title}"
