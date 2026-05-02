"""URL patterns for the marketplace app."""

from django.urls import path
from . import views

app_name = "marketplace"

urlpatterns = [
    # Public endpoints (no auth)
    path("", views.PublicMarketplaceListView.as_view(), name="public-list"),
    path("<uuid:pk>/", views.PublicMarketplaceDetailView.as_view(), name="public-detail"),
    path("<uuid:pk>/interest/", views.SubmitInterestView.as_view(), name="submit-interest"),
    # Admin/owner endpoints
    path("publish/", views.PublishToMarketplaceView.as_view(), name="publish"),
    path("manage/", views.ManageMarketplaceListView.as_view(), name="manage-list"),
    path("<uuid:pk>/interests/", views.InterestRequestListView.as_view(), name="interest-list"),
]
