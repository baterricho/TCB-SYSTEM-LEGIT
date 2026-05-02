"""Admin configuration for security app."""

from django.contrib import admin
from .models import AuditLog, EncryptionKey


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "entity_preview")
    list_filter = ("action",)
    search_fields = ("action", "entity", "user__full_name")
    readonly_fields = ("id", "user", "action", "entity", "timestamp")
    date_hierarchy = "timestamp"

    @admin.display(description="Entity")
    def entity_preview(self, obj):
        return obj.entity[:80] + "..." if len(obj.entity) > 80 else obj.entity

    def has_add_permission(self, request):
        return False  # Logs are system-generated only

    def has_change_permission(self, request, obj=None):
        return False  # Logs are immutable

    def has_delete_permission(self, request, obj=None):
        return False  # Logs cannot be deleted


@admin.register(EncryptionKey)
class EncryptionKeyAdmin(admin.ModelAdmin):
    list_display = ("key_name", "created_by", "created_at")
    search_fields = ("key_name",)
    readonly_fields = ("id", "created_at")

    # Never show the encrypted value in admin
    exclude = ("key_value_encrypted",)
