import uuid

from django.conf import settings
from django.db import models


class IPRecord(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="record_id")
    case = models.OneToOneField("cases.Case", on_delete=models.PROTECT, related_name="ip_record", db_column="case_id")
    application = models.ForeignKey("applications.IPApplication", on_delete=models.PROTECT, related_name="ip_records", db_column="application_id")
    encryption_key = models.ForeignKey("security_keys.EncryptionKey", on_delete=models.SET_NULL, null=True, blank=True, related_name="ip_records", db_column="encryption_key_id")
    certification_date = models.DateField(null=True, blank=True)
    is_certified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ip_record"
        ordering = ("-certification_date", "-created_at")
        indexes = [
            models.Index(fields=["case"]),
            models.Index(fields=["application"]),
            models.Index(fields=["is_certified"]),
        ]

    def __str__(self):
        return f"Record for {self.case.case_number}"


class MarketListing(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    id = models.BigAutoField(primary_key=True, db_column="listing_id")
    listing_code = models.CharField(max_length=50, unique=True, editable=False)
    record = models.ForeignKey(IPRecord, on_delete=models.PROTECT, related_name="market_listings", db_column="record_id")
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="market_listings", db_column="admin_id")
    title = models.CharField(max_length=255)
    ip_type = models.CharField(max_length=30)
    inventor_name = models.CharField(max_length=255)
    short_description = models.TextField()
    full_description = models.TextField()
    category = models.CharField(max_length=150)
    availability_status = models.CharField(max_length=100)
    image = models.ImageField(upload_to="marketplace/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "market_listing"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["listing_code"]),
            models.Index(fields=["record"]),
            models.Index(fields=["admin"]),
            models.Index(fields=["ip_type"]),
            models.Index(fields=["status", "is_active"]),
        ]

    def save(self, *args, **kwargs):
        if not self.listing_code:
            self.listing_code = f"LST-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    @property
    def listing_id(self):
        return self.listing_code

    @property
    def created_by(self):
        return self.admin

    def __str__(self):
        return self.title


class Bookmark(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="bookmark_id")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks", db_column="applicant_id")
    listing = models.ForeignKey(MarketListing, on_delete=models.CASCADE, related_name="bookmarks", db_column="listing_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bookmark"
        constraints = [
            models.UniqueConstraint(fields=["applicant", "listing"], name="unique_applicant_market_listing_bookmark"),
        ]
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["applicant"]),
            models.Index(fields=["listing"]),
        ]

    def __str__(self):
        return f"{self.applicant.email} - {self.listing.title}"


MarketplaceListing = MarketListing
