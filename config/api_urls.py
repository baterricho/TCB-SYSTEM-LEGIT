from django.urls import include, path
from django.http import JsonResponse

from core.views import AdminConversationsView, AdminSubmissionsView, AdminUsersView, SystemConfigView
from messaging.views import EvaluatorConversationListView

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
                "/api/messages/",
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
    path("auth/", include("accounts.urls")),
    path("applications/", include("applications.urls")),
    path("admin/submissions/", AdminSubmissionsView.as_view(), name="api-admin-submissions"),
    path("admin/users/", AdminUsersView.as_view(), name="api-admin-users"),
    path("admin/conversations/", AdminConversationsView.as_view(), name="api-admin-conversations"),
    path("system-config/", SystemConfigView.as_view(), name="api-system-config"),
    path("evaluator/conversations/", EvaluatorConversationListView.as_view(), name="api-evaluator-conversations"),
    path("evaluator/", include("cases.evaluator_urls")),
    path("cases/", include("cases.urls")),
    path("documents/", include("documents.urls")),
    path("payments/", include("payments.urls")),
    path("messaging/", include("messaging.urls")),
    path("messages/", include("messaging.urls")),
    path("notifications/", include("notifications.urls")),
    path("audit-logs/", include("auditlog.urls")),
    path("marketplace/", include("marketplace.urls")),
    path("inquiries/", include("inquiries.urls")),
    path("announcements/", include("announcements.urls")),
    path("reports/", include("reports.urls")),
    path("security-keys/", include("security_keys.urls")),
    path("ipophl-email/", include("ipophl_email.urls")),
    path("nlq/", include("nlq.urls")),
]
