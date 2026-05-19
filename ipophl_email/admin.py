from django.contrib import admin

from .models import IPOPHLEmailParse


@admin.register(IPOPHLEmailParse)
class EmailParseAdmin(admin.ModelAdmin):
    list_display = ("sender", "subject", "case_number_detected", "status", "matched_case", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("sender", "subject", "case_number_detected", "body")
