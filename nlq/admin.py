from django.contrib import admin

from .models import NLQQuery


@admin.register(NLQQuery)
class NLQQueryAdmin(admin.ModelAdmin):
    list_display = ("user", "detected_intent", "result_count", "created_at")
    search_fields = ("raw_query", "detected_intent")
    readonly_fields = ("created_at",)
