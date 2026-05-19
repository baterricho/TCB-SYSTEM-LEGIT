from django.contrib import admin

from .models import Bookmark, IPRecord, MarketListing


@admin.register(IPRecord)
class IPRecordAdmin(admin.ModelAdmin):
    list_display = ("case", "application", "is_certified", "certification_date", "created_at")
    list_filter = ("is_certified", "certification_date")
    search_fields = ("case__case_number", "application__application_code")


@admin.register(MarketListing)
class MarketListingAdmin(admin.ModelAdmin):
    list_display = ("listing_code", "title", "ip_type", "status", "is_active", "admin", "created_at")
    list_filter = ("status", "is_active", "ip_type", "category")
    search_fields = ("listing_code", "title", "inventor_name", "short_description")


admin.site.register(Bookmark)
