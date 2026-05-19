import uuid

from django.conf import settings
from django.db import models


class IPApplication(models.Model):
    class IPType(models.TextChoices):
        PATENT = "patent", "Patent"
        UTILITY_MODEL = "utility_model", "Utility Model"
        INDUSTRIAL_DESIGN = "industrial_design", "Industrial Design"
        TRADEMARK = "trademark", "Trademark"
        COPYRIGHT = "copyright", "Copyright"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        WITHDRAWN = "withdrawn", "Withdrawn"

    class LanguageStatus(models.TextChoices):
        VALID = "valid", "Valid"
        WARNING = "warning", "Warning"
        FAILED = "failed", "Failed"

    id = models.BigAutoField(primary_key=True, db_column="application_id")
    application_code = models.CharField(max_length=40, unique=True, editable=False)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ip_applications", db_column="applicant_id")
    ip_type = models.CharField(max_length=30, choices=IPType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    abstract = models.TextField(blank=True)
    claims = models.TextField(blank=True)
    technical_explanation = models.TextField(blank=True)
    novelty_explanation = models.TextField(blank=True)
    supporting_details = models.TextField(blank=True)
    declaration_accepted = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    completeness_score = models.PositiveSmallIntegerField(default=0)
    language_validation_status = models.CharField(max_length=30, choices=LanguageStatus.choices, default=LanguageStatus.VALID)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ip_application"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["application_code"]),
            models.Index(fields=["applicant"]),
            models.Index(fields=["ip_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["submitted_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.application_code:
            self.application_code = f"APP-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application_code} - {self.title}"


class ApplicationChecklist(models.Model):
    class Status(models.TextChoices):
        COMPLETE = "complete", "Complete"
        MISSING = "missing", "Missing"
        NEEDS_REVIEW = "needs_review", "Needs Review"
        OPTIONAL = "optional", "Optional"

    id = models.BigAutoField(primary_key=True, db_column="checklist_id")
    application = models.ForeignKey(IPApplication, on_delete=models.CASCADE, related_name="checklist_items", db_column="application_id")
    item_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "application_checklist"
        unique_together = ("application", "item_name")
        ordering = ("id",)

    def __str__(self):
        return f"{self.application.application_code} - {self.item_name}"
