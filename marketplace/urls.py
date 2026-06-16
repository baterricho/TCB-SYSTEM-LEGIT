from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminMarketplaceListingViewSet, BookmarkViewSet, MarketplaceListingViewSet


router = DefaultRouter()
router.register("listings", MarketplaceListingViewSet, basename="marketplace-listings")
router.register("admin/listings", AdminMarketplaceListingViewSet, basename="marketplace-admin-listings")
router.register("bookmarks", BookmarkViewSet, basename="marketplace-bookmarks")

urlpatterns = [path("", include(router.urls))]
