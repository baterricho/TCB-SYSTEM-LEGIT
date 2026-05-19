from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "document_type", "case", "uploaded_by", "uploaded_at", "is_confidential")
    list_filter = ("document_type", "is_confidential", "mime_type")
    search_fields = ("original_filename", "case__case_number", "uploaded_by__email")
    readonly_fields = ("nonce", "checksum", "uploaded_at")
