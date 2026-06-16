from django.conf import settings
from django.db import models


class Document(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="document_id")
    case = models.ForeignKey("cases.Case", on_delete=models.PROTECT, related_name="documents", db_column="case_id")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_documents", db_column="uploaded_by_id")
    document_type = models.CharField(max_length=100)
    original_filename = models.CharField(max_length=255)
    encrypted_file_path = models.FileField(upload_to="encrypted/documents/")
    file_size = models.PositiveBigIntegerField()
    mime_type = models.CharField(max_length=150)
    encryption_key = models.ForeignKey("security_keys.EncryptionKey", on_delete=models.PROTECT, related_name="documents", db_column="encryption_key_id")
    nonce = models.CharField(max_length=50)
    checksum = models.CharField(max_length=64)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_confidential = models.BooleanField(default=True)

    class Meta:
        db_table = "document"
        ordering = ("-uploaded_at",)
        indexes = [
            models.Index(fields=["case"]),
            models.Index(fields=["uploaded_by"]),
            models.Index(fields=["document_type"]),
            models.Index(fields=["uploaded_at"]),
        ]

    def __str__(self):
        return self.original_filename
