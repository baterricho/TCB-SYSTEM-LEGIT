from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse


def root_api_index(request):
    return JsonResponse(
        {
            "message": "TCB Backend API is running",
            "available_routes": [
                "/admin/",
                "/api/auth/",
                "/api/applications/",
                "/api/cases/",
                "/api/documents/",
                "/api/payments/",
                "/api/messaging/",
                "/api/notifications/",
                "/api/audit-logs/",
                "/api/marketplace/",
                "/api/inquiries/",
                "/api/announcements/",
                "/api/reports/",
                "/api/security-keys/",
                "/api/ipophl-email/",
                "/api/nlq/",
            ],
        }
    )


urlpatterns = [
    path("", root_api_index, name="api-root"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/applications/", include("applications.urls")),
    path("api/cases/", include("cases.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/messaging/", include("messaging.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/audit-logs/", include("auditlog.urls")),
    path("api/marketplace/", include("marketplace.urls")),
    path("api/inquiries/", include("inquiries.urls")),
    path("api/announcements/", include("announcements.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/security-keys/", include("security_keys.urls")),
    path("api/ipophl-email/", include("ipophl_email.urls")),
    path("api/nlq/", include("nlq.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
