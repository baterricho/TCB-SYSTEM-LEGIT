from django.contrib import admin

from .models import EncryptionKey, KeyActivityLog


@admin.register(EncryptionKey)
class EncryptionKeyAdmin(admin.ModelAdmin):
    list_display = ("key_code", "key_name", "algorithm", "status", "is_primary", "is_backup", "created_at")
    list_filter = ("status", "is_primary", "is_backup")
    search_fields = ("key_code", "key_name")
    readonly_fields = ("encrypted_key_material", "created_at", "rotated_at", "disabled_at")


admin.site.register(KeyActivityLog)
