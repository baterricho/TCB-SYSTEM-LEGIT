from django.conf import settings
from django.db import models


class ReportExport(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="report_export_id")
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="report_exports", db_column="generated_by_id")
    report_type = models.CharField(max_length=120)
    file_path = models.FileField(upload_to="reports/exports/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "report_export"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["generated_by"]),
            models.Index(fields=["report_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.report_type} - {self.created_at:%Y-%m-%d}"
