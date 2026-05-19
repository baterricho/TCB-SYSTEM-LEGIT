from django.db import models


class IPOPHLEmailParse(models.Model):
    class Status(models.TextChoices):
        MATCHED = "matched", "Matched"
        UNMATCHED = "unmatched", "Unmatched"
        FAILED = "failed", "Failed"

    id = models.BigAutoField(primary_key=True, db_column="email_parse_id")
    sender = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    case_number_detected = models.CharField(max_length=80, blank=True)
    report_type = models.CharField(max_length=150, blank=True)
    deadline_detected = models.DateField(null=True, blank=True)
    required_action = models.TextField(blank=True)
    attachments_metadata = models.JSONField(default=list, blank=True)
    matched_case = models.ForeignKey("cases.Case", on_delete=models.SET_NULL, null=True, blank=True, related_name="ipophl_email_parses", db_column="matched_case_id")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNMATCHED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ipophl_email_parse"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["sender"]),
            models.Index(fields=["case_number_detected"]),
            models.Index(fields=["report_type"]),
            models.Index(fields=["deadline_detected"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.subject


EmailParse = IPOPHLEmailParse
