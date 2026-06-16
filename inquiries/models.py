from django.conf import settings
from django.db import models
from django.utils import timezone


class Inquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        ANSWERED = "answered", "Answered"
        CLOSED = "closed", "Closed"

    id = models.BigAutoField(primary_key=True, db_column="inquiry_id")
    inquiry_code = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="inquiries", db_column="user_id")
    listing = models.ForeignKey("marketplace.MarketListing", on_delete=models.SET_NULL, null=True, blank=True, related_name="inquiries", db_column="listing_id")
    sender_name = models.CharField(max_length=255)
    email = models.EmailField()
    category = models.CharField(max_length=100)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    popularity_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inquiry"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["listing"]),
            models.Index(fields=["category"]),
            models.Index(fields=["status"]),
            models.Index(fields=["popularity_count"]),
        ]

    def save(self, *args, **kwargs):
        if not self.inquiry_code:
            from django.db import transaction, IntegrityError
            import uuid

            year = timezone.now().year
            for attempt in range(10):
                try:
                    with transaction.atomic():
                        next_number = Inquiry.objects.filter(created_at__year=year).count() + 1
                        self.inquiry_code = f"INQ-{year}-{next_number:05d}"
                        super().save(*args, **kwargs)
                        return
                except IntegrityError:
                    if attempt == 9:
                        self.inquiry_code = f"INQ-{year}-{uuid.uuid4().hex[:8].upper()}"
                        super().save(*args, **kwargs)
                        return
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.subject
