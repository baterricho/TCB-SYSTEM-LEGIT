from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.audit import create_audit_log
from core.permissions import IsAdmin
from nlq.services import NLQService

from .models import Inquiry
from .serializers import InquiryAdminUpdateSerializer, InquirySerializer


class InquiryViewSet(viewsets.ModelViewSet):
    serializer_class = InquirySerializer
    filterset_fields = ("status", "category", "listing")
    search_fields = ("inquiry_code", "sender_name", "email", "subject", "message")
    ordering_fields = ("created_at", "popularity_count")

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [IsAdmin()]

    def get_queryset(self):
        qs = Inquiry.objects.all()
        sort = self.request.query_params.get("sort")
        if sort == "most_popular":
            return qs.order_by("-popularity_count")
        if sort == "less_popular":
            return qs.order_by("popularity_count")
        if sort == "oldest":
            return qs.order_by("created_at")
        return qs.order_by("-created_at")

    def get_serializer_class(self):
        if self.action in {"partial_update", "update"}:
            return InquiryAdminUpdateSerializer
        return InquirySerializer

    def perform_create(self, serializer):
        user = self.request.user if self.request.user and self.request.user.is_authenticated else None
        inquiry = serializer.save(user=user)
        create_audit_log(self.request, user, "inquiry.created", inquiry.inquiry_code, "Public inquiry submitted.")

    def perform_update(self, serializer):
        inquiry = serializer.save()
        create_audit_log(
            self.request,
            self.request.user,
            "inquiry.status_updated",
            inquiry.inquiry_code,
            f"Admin updated inquiry status. New status: {inquiry.status}.",
        )

    @action(detail=False, methods=["post"], url_path="nlq-search")
    def nlq_search(self, request):
        if request.user.role != "admin":
            raise PermissionDenied("Only admins can run inquiry NLQ search.")
        query = request.data.get("query", "")
        return Response(NLQService.process(query, request.user))
