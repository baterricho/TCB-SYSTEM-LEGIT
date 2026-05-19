from django.contrib import admin

from .models import FeeAssessment, Payment


@admin.register(FeeAssessment)
class FeeAssessmentAdmin(admin.ModelAdmin):
    list_display = ("case", "application", "fee_type", "amount", "status", "issued_at")
    list_filter = ("status", "fee_type")
    search_fields = ("case__case_number", "application__application_code", "fee_type")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "applicant", "case", "amount_paid", "payment_method", "payment_status", "created_at")
    list_filter = ("payment_status", "payment_method")
    search_fields = ("original_filename", "applicant__email", "case__case_number")
    readonly_fields = ("nonce", "checksum", "created_at", "updated_at", "verified_at")
