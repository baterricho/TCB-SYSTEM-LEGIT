from django.contrib import admin

from .models import ReportExport


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ("report_type", "generated_by", "created_at")
    list_filter = ("report_type", "created_at")
    search_fields = ("report_type", "generated_by__email")
