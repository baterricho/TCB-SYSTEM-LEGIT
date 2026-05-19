from django.conf import settings
from django.db import models


class FeeAssessment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ISSUED = "issued", "Issued"
        PAID = "paid", "Paid"
        WAIVED = "waived", "Waived"
        CANCELLED = "cancelled", "Cancelled"

    id = models.BigAutoField(primary_key=True, db_column="assessment_id")
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, related_name="fee_assessments", db_column="case_id")
    application = models.ForeignKey("applications.IPApplication", on_delete=models.PROTECT, related_name="fee_assessments", db_column="application_id")
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="issued_fee_assessments", db_column="evaluator_id")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fee_type = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    issued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fee_assessment"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["case"]),
            models.Index(fields=["application"]),
            models.Index(fields=["evaluator"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.case.case_number} - {self.fee_type}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    id = models.BigAutoField(primary_key=True, db_column="payment_id")
    assessment = models.ForeignKey(FeeAssessment, on_delete=models.PROTECT, related_name="payments", db_column="assessment_id")
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, related_name="payments", db_column="case_id")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments", db_column="applicant_id")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=80)
    receipt_no = models.CharField(max_length=100, blank=True)
    encrypted_receipt_file = models.FileField(upload_to="encrypted/receipts/")
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField(default=0)
    mime_type = models.CharField(max_length=150, blank=True)
    encryption_key = models.ForeignKey("security_keys.EncryptionKey", on_delete=models.PROTECT, related_name="payments", db_column="encryption_key_id")
    nonce = models.CharField(max_length=50)
    checksum = models.CharField(max_length=64)
    payment_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_date = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_payments", db_column="verified_by_id")
    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["assessment"]),
            models.Index(fields=["case"]),
            models.Index(fields=["applicant"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["payment_date"]),
        ]

    @property
    def status(self):
        return self.payment_status

    def __str__(self):
        return f"{self.case.case_number} - {self.amount_paid}"


PaymentProof = Payment
