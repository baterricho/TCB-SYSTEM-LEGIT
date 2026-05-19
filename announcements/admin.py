from django.contrib import admin

from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "admin", "created_at")
    list_filter = ("category", "is_published")
    search_fields = ("title", "content", "admin__email")
