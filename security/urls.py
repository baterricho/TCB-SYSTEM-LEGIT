"""URL patterns for the security app."""

from django.urls import path
from . import views

app_name = "security"

urlpatterns = [
    path("audit-logs/", views.AuditLogListView.as_view(), name="audit-log-list"),
    path(
        "encryption-keys/",
        views.EncryptionKeyListCreateView.as_view(),
        name="encryption-key-list-create",
    ),
    path(
        "encryption-keys/<uuid:pk>/",
        views.EncryptionKeyDetailView.as_view(),
        name="encryption-key-detail",
    ),
]
