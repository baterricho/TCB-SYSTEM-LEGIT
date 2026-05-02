"""
Audit Log and Encryption Key models.
Provides full traceability and admin-controlled encryption key management.
"""

import uuid
from django.db import models
from django.conf import settings
from core.utils.encryption import encrypt_value, decrypt_value


class AuditLog(models.Model):
    """
    Immutable audit trail for all critical system actions.
    Tracks: login, status updates, file uploads, deletions,
    user management, and all administrative operations.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100)
    entity = models.CharField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self):
        user_name = self.user.full_name if self.user else "System"
        return f"[{self.timestamp}] {user_name}: {self.action} on {self.entity}"


class EncryptionKey(models.Model):
    """
    Admin-managed encryption keys for securing sensitive system data.
    Key values are encrypted with Fernet before database storage.
    Only admins can create, view, or manage encryption keys.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key_name = models.CharField(max_length=255, unique=True)
    key_value_encrypted = models.TextField(
        help_text="Fernet-encrypted key value. Never stored in plaintext."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_encryption_keys",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Key: {self.key_name}"

    def set_key_value(self, plaintext_value):
        """Encrypt and store the key value."""
        self.key_value_encrypted = encrypt_value(plaintext_value)

    def get_key_value(self):
        """Decrypt and return the key value."""
        return decrypt_value(self.key_value_encrypted)
