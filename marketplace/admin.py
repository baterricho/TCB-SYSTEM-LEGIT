"""Admin configuration for marketplace app."""

from django.contrib import admin
from .models import MarketplaceItem, InterestRequest


class InterestRequestInline(admin.TabularInline):
    model = InterestRequest
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(MarketplaceItem)
class MarketplaceItemAdmin(admin.ModelAdmin):
    list_display = (
        "title", "application", "is_public",
        "is_archived", "interest_count", "created_at",
    )
    list_filter = ("is_public", "is_archived")
    search_fields = ("title", "abstract")
    readonly_fields = ("id", "archived_at", "created_at", "updated_at")
    inlines = [InterestRequestInline]
    actions = ["archive_selected"]

    @admin.display(description="Interests")
    def interest_count(self, obj):
        return obj.interest_requests.count()

    @admin.action(description="Archive selected marketplace listings")
    def archive_selected(self, request, queryset):
        for item in queryset:
            item.archive()


@admin.register(InterestRequest)
class InterestRequestAdmin(admin.ModelAdmin):
    list_display = ("requester_name", "requester_email", "marketplace_item", "created_at")
    search_fields = ("requester_name", "requester_email")
    readonly_fields = ("created_at",)
