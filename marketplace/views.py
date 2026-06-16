from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from core.audit import create_audit_log
from core.permissions import IsAdmin

from .models import Bookmark, MarketListing
from .serializers import BookmarkCreateSerializer, BookmarkSerializer, MarketplaceListingSerializer


class MarketplaceListingViewSet(viewsets.ModelViewSet):
    serializer_class = MarketplaceListingSerializer
    filterset_fields = ("status", "ip_type", "category", "availability_status")
    search_fields = ("listing_code", "title", "inventor_name", "short_description", "full_description")

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.AllowAny()]
        if self.action == "bookmark":
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]

    def get_queryset(self):
        qs = MarketListing.objects.select_related("record", "admin").annotate(bookmark_count=Count("bookmarks")).order_by("-created_at")
        user = self.request.user
        if user.is_authenticated and user.role == "admin":
            return qs
        return qs.filter(status=MarketListing.Status.PUBLISHED, is_active=True)

    def perform_create(self, serializer):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admins can create marketplace listings.")
        listing = serializer.save(admin=self.request.user)
        create_audit_log(self.request, self.request.user, "marketplace.created", listing.listing_code, "Marketplace listing created.")

    def perform_update(self, serializer):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admins can update marketplace listings.")
        listing = serializer.save()
        create_audit_log(self.request, self.request.user, "marketplace.updated", listing.listing_code, "Marketplace listing updated.")

    def perform_destroy(self, instance):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admins can delete marketplace listings.")
        listing_code = instance.listing_code
        instance.delete()
        create_audit_log(self.request, self.request.user, "marketplace.deleted", listing_code, "Marketplace listing deleted.")

    @action(detail=True, methods=["post"], url_path="archive")
    def archive_listing(self, request, pk=None):
        if request.user.role != "admin":
            raise PermissionDenied("Only admins can archive marketplace listings.")
        listing = self.get_object()
        listing.status = MarketListing.Status.ARCHIVED
        listing.is_active = False
        listing.save(update_fields=["status", "is_active", "updated_at"])
        create_audit_log(request, request.user, "marketplace.archived", listing.listing_code, "Marketplace listing archived.")
        return Response(MarketplaceListingSerializer(listing).data)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish_listing(self, request, pk=None):
        if request.user.role != "admin":
            raise PermissionDenied("Only admins can publish marketplace listings.")
        listing = self.get_object()
        listing.status = MarketListing.Status.PUBLISHED
        listing.is_active = True
        listing.save(update_fields=["status", "is_active", "updated_at"])
        create_audit_log(request, request.user, "marketplace.published", listing.listing_code, "Marketplace listing published.")
        return Response(MarketplaceListingSerializer(listing).data)

    @action(detail=True, methods=["post"], url_path="restore")
    def restore_listing(self, request, pk=None):
        if request.user.role != "admin":
            raise PermissionDenied("Only admins can restore marketplace listings.")
        listing = self.get_object()
        listing.status = MarketListing.Status.PUBLISHED
        listing.is_active = True
        listing.save(update_fields=["status", "is_active", "updated_at"])
        create_audit_log(request, request.user, "marketplace.restored", listing.listing_code, "Marketplace listing restored.")
        return Response(MarketplaceListingSerializer(listing).data)

    @action(detail=True, methods=["post", "delete"], url_path="bookmark")
    def bookmark(self, request, pk=None):
        if not request.user.is_authenticated or request.user.role != "applicant":
            raise PermissionDenied("Only applicants can bookmark listings.")
        listing = self.get_object()
        if request.method == "DELETE":
            Bookmark.objects.filter(applicant=request.user, listing=listing).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        bookmark, created = Bookmark.objects.get_or_create(applicant=request.user, listing=listing)
        if not created:
            return Response(BookmarkSerializer(bookmark).data)
        return Response(BookmarkSerializer(bookmark).data, status=status.HTTP_201_CREATED)


class AdminMarketplaceListingViewSet(MarketplaceListingViewSet):
    permission_classes = [IsAdmin]

    def get_permissions(self):
        return [IsAdmin()]

    def get_queryset(self):
        return (
            MarketListing.objects.select_related("record", "admin")
            .annotate(bookmark_count=Count("bookmarks"))
            .order_by("-created_at")
        )


class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return Bookmark.objects.filter(applicant=self.request.user).select_related("listing")

    def create(self, request, *args, **kwargs):
        if request.user.role != "applicant":
            raise PermissionDenied("Only applicants can bookmark listings.")
        serializer = BookmarkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        listing = get_object_or_404(MarketListing, pk=serializer.validated_data["listing"], status=MarketListing.Status.PUBLISHED, is_active=True)
        bookmark, created = Bookmark.objects.get_or_create(applicant=request.user, listing=listing)
        if not created:
            raise ValidationError("This listing is already bookmarked.")
        return Response(BookmarkSerializer(bookmark).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        bookmark = self.get_object()
        bookmark.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
