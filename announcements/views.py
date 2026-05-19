from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from core.audit import create_audit_log

from .models import Announcement
from .serializers import AnnouncementSerializer


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    filterset_fields = ("category", "is_published")
    search_fields = ("title", "content", "category")

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = Announcement.objects.select_related("admin")
        user = self.request.user
        if user.is_authenticated and user.role == "admin":
            return qs
        return qs.filter(is_published=True)

    def perform_create(self, serializer):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admins can create announcements.")
        announcement = serializer.save(admin=self.request.user)
        create_audit_log(self.request, self.request.user, "announcement.created", str(announcement.id), "Announcement created.")

    def perform_update(self, serializer):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admins can update announcements.")
        announcement = serializer.save()
        create_audit_log(self.request, self.request.user, "announcement.updated", str(announcement.id), "Announcement updated.")
