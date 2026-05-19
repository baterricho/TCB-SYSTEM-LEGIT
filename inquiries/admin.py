from django.contrib import admin

from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("inquiry_code", "sender_name", "email", "category", "status", "popularity_count", "created_at")
    list_filter = ("status", "category")
    search_fields = ("inquiry_code", "sender_name", "email", "subject", "message")
