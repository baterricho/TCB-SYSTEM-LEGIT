from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookmarkViewSet, MarketplaceListingViewSet


router = DefaultRouter()
router.register("listings", MarketplaceListingViewSet, basename="marketplace-listings")
router.register("bookmarks", BookmarkViewSet, basename="marketplace-bookmarks")

urlpatterns = [path("", include(router.urls))]
