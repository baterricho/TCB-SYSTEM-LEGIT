from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("log_timestamp", "user", "role", "action", "target", "record_id", "ip_address")
    list_filter = ("role", "action", "log_timestamp")
    search_fields = ("account_name", "target", "record_id", "details", "user__email")
    readonly_fields = ("log_timestamp",)
