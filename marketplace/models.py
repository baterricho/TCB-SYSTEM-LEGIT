"""
Marketplace and Interest Request models.
Only certified IP applications can be published to the marketplace.
Public users can view abstracts and send interest requests.
"""

import uuid
from django.db import models
from django.utils import timezone


class MarketplaceItem(models.Model):
    """
    Public marketplace listing for certified IP applications.
    Only exposes non-confidential information (title + abstract).
    Documents are NEVER exposed through the marketplace.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(
        "applications.IPApplication",
        on_delete=models.CASCADE,
        related_name="marketplace_item",
    )
    title = models.CharField(max_length=500)
    abstract = models.TextField()
    is_public = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_public", "is_archived", "-created_at"]),
        ]

    def __str__(self):
        visibility = "Public" if self.is_public else "Private"
        return f"[{visibility}] {self.title}"

    def archive(self):
        self.is_archived = True
        self.archived_at = timezone.now()
        self.is_public = False
        self.save(update_fields=["is_archived", "archived_at", "is_public", "updated_at"])


class InterestRequest(models.Model):
    """
    Interest requests from external stakeholders.
    No authentication required — public users can express interest.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    marketplace_item = models.ForeignKey(
        MarketplaceItem,
        on_delete=models.CASCADE,
        related_name="interest_requests",
    )
    requester_name = models.CharField(max_length=255)
    requester_email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Interest from {self.requester_name} for '{self.marketplace_item.title}'"
