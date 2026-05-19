from django.conf import settings
from django.db import models


class NLQQuery(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="nlq_query_id")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="nlq_queries", db_column="user_id")
    raw_query = models.TextField()
    detected_intent = models.CharField(max_length=150, blank=True)
    extracted_filters = models.JSONField(default=dict, blank=True)
    result_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "nlq_query"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["detected_intent"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.raw_query[:80]
