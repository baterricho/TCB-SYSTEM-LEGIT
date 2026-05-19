from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ApplicantProfile, User, EvaluatorProfile, OTPCode


@admin.register(User)
class UserAdminConfig(UserAdmin):
    model = User
    ordering = ("email",)
    list_display = ("email", "username", "first_name", "last_name", "role", "status", "is_staff")
    list_filter = ("role", "status", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal information", {"fields": ("username", "first_name", "middle_name", "last_name", "contact_number", "address")}),
        ("Role and status", {"fields": ("role", "status", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Security", {"fields": ("failed_login_attempts", "locked_until", "last_login_ip", "last_login", "last_login_at")}),
        ("Important dates", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at", "last_login", "last_login_at")
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "first_name", "last_name", "role", "status", "password1", "password2", "is_staff"),
        }),
    )


admin.site.register(OTPCode)
admin.site.register(ApplicantProfile)
admin.site.register(EvaluatorProfile)
