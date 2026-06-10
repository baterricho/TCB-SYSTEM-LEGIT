from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "role_visibility", "notification_type", "is_read", "created_at")
    list_filter = ("role_visibility", "notification_type", "is_read")
    search_fields = ("title", "content", "recipient__email")
