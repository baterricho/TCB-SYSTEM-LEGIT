from django.conf import settings
from django.db import models


class Notification(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="notification_id")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications", db_column="user_id")
    related_case = models.ForeignKey("cases.Case", on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications", db_column="related_case_id")
    notification_type = models.CharField(max_length=100, blank=True, db_column="type")
    title = models.CharField(max_length=255)
    content = models.TextField()
    role_visibility = models.CharField(max_length=30, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["recipient"]),
            models.Index(fields=["related_case"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["role_visibility"]),
            models.Index(fields=["is_read"]),
        ]

    def __str__(self):
        return self.title
