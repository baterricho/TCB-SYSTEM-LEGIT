import uuid

from django.conf import settings
from django.db import models


class EncryptionKey(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ROTATED = "rotated", "Rotated"
        DISABLED = "disabled", "Disabled"

    id = models.BigAutoField(primary_key=True, db_column="key_id")
    key_code = models.CharField(max_length=50, unique=True, editable=False)
    key_name = models.CharField(max_length=150)
    algorithm = models.CharField(max_length=50, default="AES-256-GCM")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    encrypted_key_material = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_encryption_keys", db_column="created_by_id")
    created_at = models.DateTimeField(auto_now_add=True)
    rotated_at = models.DateTimeField(null=True, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)
    rotation_policy = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    is_backup = models.BooleanField(default=False)

    class Meta:
        db_table = "encryption_key"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["key_code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_primary"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["is_primary"], condition=models.Q(is_primary=True), name="unique_active_primary_key")
        ]

    def save(self, *args, **kwargs):
        if not self.key_code:
            self.key_code = f"KEY-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    @property
    def key_id(self):
        return self.key_code

    def __str__(self):
        return self.key_code


class KeyActivityLog(models.Model):
    class Action(models.TextChoices):
        GENERATED = "generated", "Generated"
        ROTATED = "rotated", "Rotated"
        DISABLED = "disabled", "Disabled"
        ESCROW_REPORT_GENERATED = "escrow_report_generated", "Escrow Report Generated"

    id = models.BigAutoField(primary_key=True, db_column="key_activity_id")
    key = models.ForeignKey(EncryptionKey, on_delete=models.CASCADE, related_name="activity_logs", db_column="key_id")
    action = models.CharField(max_length=100)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, db_column="performed_by_id")
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "key_activity_log"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["key"]),
            models.Index(fields=["created_at"]),
        ]
