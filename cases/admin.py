from django.contrib import admin

from .models import ActivityTimeline, Case, CaseEvaluation, CaseStatusHistory


class CaseStatusHistoryInline(admin.TabularInline):
    model = CaseStatusHistory
    extra = 0


class ActivityTimelineInline(admin.TabularInline):
    model = ActivityTimeline
    extra = 0


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("case_number", "application", "applicant", "taken_by", "status", "priority_label", "deadline")
    list_filter = ("status", "is_taken", "priority_label")
    search_fields = ("case_number", "application__application_code", "applicant__email", "taken_by__email")
    inlines = [CaseStatusHistoryInline, ActivityTimelineInline]


admin.site.register(CaseStatusHistory)
admin.site.register(ActivityTimeline)
admin.site.register(CaseEvaluation)
