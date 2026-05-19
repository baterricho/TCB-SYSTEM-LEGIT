from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="log_id")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs", db_column="user_id")
    related_case = models.ForeignKey("cases.Case", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs", db_column="case_id")
    account_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=30, blank=True)
    action = models.CharField(max_length=150)
    target = models.CharField(max_length=150, blank=True)
    record_id = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    log_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        ordering = ("-log_timestamp",)
        indexes = [
            models.Index(fields=["log_timestamp"]),
            models.Index(fields=["action"]),
            models.Index(fields=["role"]),
            models.Index(fields=["related_case"]),
            models.Index(fields=["record_id"]),
        ]

    def __str__(self):
        return f"{self.log_timestamp} - {self.action}"
