"""
IP Application, Document, Payment, Requirement, and CoInventor models.
Core entities for the IP submission and evaluation pipeline.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from core.utils.file_validators import generate_upload_path, validate_file_extension, validate_file_size


IP_TYPE_CHOICES = (
    ("Patent", "Patent"),
    ("Copyright", "Copyright"),
    ("Utility Model", "Utility Model"),
    ("Industrial Design", "Industrial Design"),
)


STATUS_CHOICES = (
    # IPTTO Stage
    ("Draft", "Draft"),
    ("Submitted", "Submitted"),
    ("Under Evaluation", "Under Evaluation"),
    ("Under Review", "Under Review (legacy)"),
    ("Deficient", "Deficient"),
    ("Certified", "Certified"),
    # IPOPHL Stage
    ("Forwarded to IPOPHL", "Forwarded to IPOPHL"),
    ("IPOPHL Under Review", "IPOPHL Under Review"),
    ("IPOPHL Deficient", "IPOPHL Deficient"),
    ("Registered", "Registered"),
)


DOCUMENT_TYPE_CHOICES = (
    ("Blueprint", "Blueprint"),
    ("Affidavit", "Affidavit"),
    ("Receipt", "Receipt"),
    ("Specification", "Specification"),
    ("Drawing", "Drawing"),
    ("Support", "Supporting Document"),
    ("Manuscript", "Manuscript"),
    ("Declaration", "Declaration"),
    ("Checklist", "Checklist/Form"),
    ("Other", "Other"),
)


class IPApplication(models.Model):
    """
    Core IP application entity.
    Tracks the full lifecycle:
      IPTTO Stage: Draft -> Submitted -> Under Evaluation -> Deficient/Certified
      IPOPHL Stage: Forwarded to IPOPHL -> IPOPHL Under Review -> IPOPHL Deficient | Registered
    """

    IP_TYPE_CHOICES = IP_TYPE_CHOICES
    STATUS_CHOICES = STATUS_CHOICES

    STAGE_CHOICES = (
        ("IPTTO", "IPTTO Evaluation"),
        ("IPOPHL", "IPOPHL Processing"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_code = models.CharField(
        max_length=40,
        unique=True,
        blank=True,
        editable=False,
        help_text="Applicant-facing case code used for searching and tracking.",
    )
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    ip_type = models.CharField(max_length=20, choices=IP_TYPE_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Draft")
    stage = models.CharField(
        max_length=10,
        choices=STAGE_CHOICES,
        default="IPTTO",
        help_text="Current processing stage: IPTTO evaluation or IPOPHL submission.",
    )

    # Copyright-specific identifiers (National Library of the Philippines compliance)
    isbn = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="International Standard Book Number (Copyright: Books).",
    )
    issn = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="International Standard Serial Number (Copyright: Periodicals).",
    )
    ismn = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="International Standard Music Number (Copyright: Music).",
    )

    # Marketplace privacy — applicant controls whether their certified IP is shown publicly
    marketplace_consent = models.BooleanField(
        default=False,
        help_text="Applicant's consent to display this IP in the public marketplace.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    assigned_evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_applications",
    )
    is_archived = models.BooleanField(
        default=False,
        help_text="Archived records remain retained but are hidden from active queues.",
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archived_applications",
    )
    archive_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["stage"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["assigned_evaluator"]),
            models.Index(fields=["ip_type"]),
            models.Index(fields=["transaction_code"]),
            models.Index(fields=["is_archived", "-created_at"]),
        ]

    def __str__(self):
        code = self.transaction_code or str(self.id)
        return f"{code} - [{self.ip_type}] {self.title} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.transaction_code:
            today = timezone.localdate().strftime("%Y%m%d")
            self.transaction_code = f"TCB-{today}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def archive(self, user, reason=""):
        self.is_archived = True
        self.archived_at = timezone.now()
        self.archived_by = user
        self.archive_reason = reason
        self.save(update_fields=["is_archived", "archived_at", "archived_by", "archive_reason", "updated_at"])

    def restore(self):
        self.is_archived = False
        self.archived_at = None
        self.archived_by = None
        self.archive_reason = ""
        self.save(update_fields=["is_archived", "archived_at", "archived_by", "archive_reason", "updated_at"])


class IPDocument(models.Model):
    """
    Documents attached to an IP application.
    Supports multiple documents per application with type classification.
    Evaluators can stamp documents with a 'Reviewed By' digital mark.
    """

    DOCUMENT_TYPE_CHOICES = DOCUMENT_TYPE_CHOICES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        IPApplication,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(
        upload_to=generate_upload_path,
        validators=[validate_file_extension, validate_file_size],
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        default="Other",
    )
    original_filename = models.CharField(max_length=255, blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Evaluator "Reviewed By" digital stamp — per User Story 2 (Evaluator)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_documents",
        help_text="Evaluator who stamped this document as reviewed.",
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the evaluator applied their review stamp.",
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.document_type}: {self.original_filename}"

    @property
    def is_stamped(self):
        """True if an evaluator has applied their review stamp."""
        return self.reviewed_by is not None


class IPRequirement(models.Model):
    """
    Admin-managed checklist item for each IP service.
    These records power the public/applicant forms and guidelines directory.
    """

    CATEGORY_CHOICES = (
        ("form", "Form"),
        ("supporting_document", "Supporting Document"),
        ("payment", "Payment"),
        ("legal", "Legal"),
        ("guideline", "Guideline"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ip_type = models.CharField(max_length=30, choices=IP_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="form")
    expected_document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        blank=True,
        default="",
        help_text="Optional document type expected when this requirement is uploaded.",
    )
    is_required = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["ip_type", "sort_order", "title"]
        indexes = [
            models.Index(fields=["ip_type", "is_active"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        required = "Required" if self.is_required else "Optional"
        return f"{self.ip_type}: {self.title} ({required})"


class PaymentRecord(models.Model):
    """
    Tracks proof-of-payment receipts uploaded by applicants.
    Evaluators or admins verify the receipt before/while reviewing the case.
    """

    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Submitted", "Submitted"),
        ("Verified", "Verified"),
        ("Rejected", "Rejected"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        IPApplication,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    reference_number = models.CharField(max_length=100, blank=True, default="")
    receipt_document = models.ForeignKey(
        IPDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_records",
        limit_choices_to={"document_type": "Receipt"},
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    notes = models.TextField(blank=True, default="")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_payments",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.application.transaction_code} payment ({self.status})"


class CoInventor(models.Model):
    """
    Co-inventors associated with an IP application.
    Multiple co-inventors can be attached to a single application.
    Their names are included in the final certification and marketplace listing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        IPApplication,
        on_delete=models.CASCADE,
        related_name="coinventors",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.email})"
