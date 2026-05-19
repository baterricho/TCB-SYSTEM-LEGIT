from django.conf import settings
from django.db import models


class Announcement(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="announcement_id")
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="announcements")
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=120)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "announcement"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["is_published"]),
            models.Index(fields=["category"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title
