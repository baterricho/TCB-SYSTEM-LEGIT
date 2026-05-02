"""
URL configuration for The Creator's Bulwark.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import FrontendConfigView, frontend_home_redirect

urlpatterns = [
    path("", frontend_home_redirect, name="frontend-home"),
    path("admin/", admin.site.urls),
    path("api/frontend-config/", FrontendConfigView.as_view(), name="frontend-config"),
    path("api/accounts/", include("accounts.urls")),
    path("api/applications/", include("applications.urls")),
    path("api/workflow/", include("workflow.urls")),
    path("api/marketplace/", include("marketplace.urls")),
    path("api/security/", include("security.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin site customization
admin.site.site_header = "The Creator's Bulwark - Admin"
admin.site.site_title = "TCB Admin"
admin.site.index_title = "IP Management System"
