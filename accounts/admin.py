"""Admin configuration for accounts app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, OTPVerification


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email", "full_name", "role", "institution",
        "contact_number", "is_verified", "is_active", "created_at",
    )
    list_filter = ("role", "is_verified", "is_active", "is_staff")
    search_fields = (
        "email", "full_name",
        "profile__institution", "profile__contact_number",
    )
    ordering = ("-created_at",)
    inlines = [UserProfileInline]
    readonly_fields = ("id", "created_at")
    actions = ["mark_verified", "activate_users", "deactivate_users"]

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Personal Info", {"fields": ("full_name",)}),
        ("Roles & Status", {"fields": ("role", "is_verified", "is_active", "is_staff", "is_superuser")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Timestamps", {"fields": ("created_at",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "role", "password1", "password2"),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("profile")

    @admin.display(description="Institution")
    def institution(self, obj):
        try:
            return obj.profile.institution
        except UserProfile.DoesNotExist:
            return ""

    @admin.display(description="Contact Number")
    def contact_number(self, obj):
        try:
            return obj.profile.contact_number
        except UserProfile.DoesNotExist:
            return ""

    @admin.action(description="Mark selected users as verified")
    def mark_verified(self, request, queryset):
        queryset.update(is_verified=True)

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "contact_number", "institution")
    search_fields = ("user__full_name", "user__email", "institution")


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "is_used", "expires_at", "created_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("user__email",)
    readonly_fields = ("otp_code", "created_at", "expires_at")
