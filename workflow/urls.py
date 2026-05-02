"""URL patterns for the workflow app."""

from django.urls import path
from . import views

app_name = "workflow"

urlpatterns = [
    # Public/admin announcements
    path("announcements/", views.PublicAnnouncementListView.as_view(), name="announcement-list"),
    path(
        "announcements/manage/",
        views.AnnouncementManageListCreateView.as_view(),
        name="announcement-manage-list",
    ),
    path(
        "announcements/manage/<uuid:pk>/",
        views.AnnouncementManageDetailView.as_view(),
        name="announcement-manage-detail",
    ),
    # Status logs & updates (IPTTO stage)
    path(
        "applications/<uuid:pk>/logs/",
        views.StatusLogListView.as_view(),
        name="status-logs",
    ),
    path(
        "applications/<uuid:pk>/messages/",
        views.CaseMessageListCreateView.as_view(),
        name="case-messages",
    ),
    path(
        "applications/<uuid:pk>/update-status/",
        views.UpdateStatusView.as_view(),
        name="update-status",
    ),
    # IPOPHL stage transitions (admin only)
    path(
        "applications/<uuid:pk>/forward-to-ipophl/",
        views.ForwardToIPOPHLView.as_view(),
        name="forward-to-ipophl",
    ),
    path(
        "applications/<uuid:pk>/update-ipophl-status/",
        views.UpdateIPOPHLStatusView.as_view(),
        name="update-ipophl-status",
    ),
    # Notifications
    path("notifications/", views.NotificationListView.as_view(), name="notification-list"),
    path(
        "notifications/unread-count/",
        views.UnreadNotificationCountView.as_view(),
        name="unread-count",
    ),
    path(
        "notifications/<uuid:pk>/read/",
        views.MarkNotificationReadView.as_view(),
        name="notification-read",
    ),
    path(
        "notifications/read-all/",
        views.MarkAllNotificationsReadView.as_view(),
        name="notification-read-all",
    ),
]
