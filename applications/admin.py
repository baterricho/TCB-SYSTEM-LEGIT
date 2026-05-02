"""Admin configuration for applications app."""

from django.contrib import admin
from .models import (
    IPApplication,
    IPDocument,
    IPRequirement,
    PaymentRecord,
    CoInventor,
)


class IPDocumentInline(admin.TabularInline):
    model = IPDocument
    extra = 0
    readonly_fields = ("uploaded_at", "reviewed_by", "reviewed_at", "is_stamped")

    def is_stamped(self, obj):
        return obj.is_stamped
    is_stamped.boolean = True
    is_stamped.short_description = "Stamped"


class CoInventorInline(admin.TabularInline):
    model = CoInventor
    extra = 0


class PaymentRecordInline(admin.TabularInline):
    model = PaymentRecord
    extra = 0
    readonly_fields = ("created_at", "updated_at", "verified_at")


@admin.register(IPApplication)
class IPApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_code", "title", "ip_type", "status", "stage",
        "marketplace_consent", "is_archived", "created_by",
        "assigned_evaluator", "created_at",
    )
    list_filter = ("ip_type", "status", "stage", "marketplace_consent", "is_archived")
    search_fields = (
        "transaction_code", "title", "description",
        "created_by__full_name", "created_by__email",
    )
    readonly_fields = (
        "id", "transaction_code", "archived_at", "archived_by",
        "created_at", "updated_at",
    )
    inlines = [IPDocumentInline, CoInventorInline, PaymentRecordInline]
    actions = ["archive_selected", "restore_selected"]

    fieldsets = (
        ("Application Info", {
            "fields": ("id", "transaction_code", "title", "description", "ip_type"),
        }),
        ("Status & Stage", {
            "fields": ("status", "stage"),
        }),
        ("Copyright Identifiers (for Copyright type only)", {
            "fields": ("isbn", "issn", "ismn"),
            "classes": ("collapse",),
        }),
        ("Marketplace", {
            "fields": ("marketplace_consent",),
        }),
        ("People", {
            "fields": ("created_by", "assigned_evaluator"),
        }),
        ("Archive", {
            "fields": ("is_archived", "archived_at", "archived_by", "archive_reason"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.action(description="Archive selected applications")
    def archive_selected(self, request, queryset):
        for application in queryset:
            application.archive(request.user, reason="Archived from Django admin.")

    @admin.action(description="Restore selected applications")
    def restore_selected(self, request, queryset):
        for application in queryset:
            application.restore()


@admin.register(IPDocument)
class IPDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename", "document_type", "application",
        "uploaded_at", "reviewed_by", "reviewed_at",
    )
    list_filter = ("document_type",)
    search_fields = ("original_filename",)
    readonly_fields = ("uploaded_at",)


@admin.register(IPRequirement)
class IPRequirementAdmin(admin.ModelAdmin):
    list_display = (
        "ip_type", "title", "category", "expected_document_type",
        "is_required", "is_active", "sort_order",
    )
    list_filter = ("ip_type", "category", "is_required", "is_active")
    search_fields = ("title", "description")
    ordering = ("ip_type", "sort_order", "title")


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = (
        "application", "amount_due", "reference_number",
        "status", "verified_by", "verified_at", "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "application__transaction_code", "application__title",
        "reference_number", "notes",
    )
    readonly_fields = ("id", "created_at", "updated_at", "verified_at")


@admin.register(CoInventor)
class CoInventorAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "application")
    search_fields = ("name", "email")
