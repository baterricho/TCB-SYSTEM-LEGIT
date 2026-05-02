"""Admin configuration for workflow app."""

from django.contrib import admin
from .models import ApplicationStatusLog, Notification, CaseMessage, Announcement


@admin.register(ApplicationStatusLog)
class ApplicationStatusLogAdmin(admin.ModelAdmin):
    list_display = ("application", "status", "updated_by", "timestamp")
    list_filter = ("status",)
    search_fields = ("application__title", "remarks")
    readonly_fields = ("id", "application", "status", "remarks", "updated_by", "timestamp")

    def has_add_permission(self, request):
        return False  # Logs are created by the system only

    def has_change_permission(self, request, obj=None):
        return False  # Logs are immutable


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message_preview", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read")
    search_fields = ("user__full_name", "message")

    @admin.display(description="Message")
    def message_preview(self, obj):
        return obj.message[:80] + "..." if len(obj.message) > 80 else obj.message


@admin.register(CaseMessage)
class CaseMessageAdmin(admin.ModelAdmin):
    list_display = ("application", "sender", "message_preview", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = (
        "application__transaction_code", "application__title",
        "sender__full_name", "sender__email", "body",
    )
    readonly_fields = ("id", "application", "sender", "body", "attachment", "created_at")
    date_hierarchy = "created_at"

    @admin.display(description="Message")
    def message_preview(self, obj):
        return obj.body[:80] + "..." if len(obj.body) > 80 else obj.body

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "created_by", "created_at")
    list_filter = ("category", "is_published")
    search_fields = ("title", "body")
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "created_at"
