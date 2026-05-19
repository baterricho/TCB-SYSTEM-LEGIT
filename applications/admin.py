from django.contrib import admin

from .models import ApplicationChecklist, IPApplication


class ApplicationChecklistInline(admin.TabularInline):
    model = ApplicationChecklist
    extra = 0


@admin.register(IPApplication)
class IPApplicationAdmin(admin.ModelAdmin):
    list_display = ("application_code", "applicant", "ip_type", "status", "completeness_score", "created_at")
    list_filter = ("ip_type", "status", "language_validation_status")
    search_fields = ("application_code", "title", "applicant__email")
    inlines = [ApplicationChecklistInline]


admin.site.register(ApplicationChecklist)
