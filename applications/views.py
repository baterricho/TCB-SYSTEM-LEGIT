from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from core.permissions import IsAdmin

from .models import IPApplication
from .serializers import CompletenessResultSerializer, IPApplicationSerializer
from .services import ApplicationSubmissionService, CompletenessService


class IPApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = IPApplicationSerializer
    filterset_fields = ("ip_type", "status", "language_validation_status")
    search_fields = ("application_code", "title", "description")

    def get_permissions(self):
        if self.action in {"update", "partial_update", "destroy"}:
            from core.permissions import IsOwnerApplicant
            return [IsOwnerApplicant()]
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = IPApplication.objects.select_related("applicant").prefetch_related("checklist_items")
        if user.role == "admin":
            return qs
        return qs.filter(applicant=user)

    def perform_create(self, serializer):
        if self.request.user.role != "applicant":
            raise PermissionDenied("Only applicants can create applications.")
        serializer.save(applicant=self.request.user)

    def perform_update(self, serializer):
        application = self.get_object()
        if application.status != IPApplication.Status.DRAFT and self.request.user.role != "admin":
            raise ValidationError("Only draft applications can be updated.")
        serializer.save()

    @action(detail=True, methods=["post"], url_path="run-completeness-checker")
    def run_completeness_checker(self, request, pk=None):
        application = self.get_object()
        checklist = CompletenessService.run(application)
        return Response(CompletenessResultSerializer({"completeness_score": application.completeness_score, "checklist": checklist}).data)

    @action(detail=True, methods=["get", "post"], url_path="completeness")
    def completeness(self, request, pk=None):
        application = self.get_object()
        checklist = CompletenessService.run(application)
        return Response(CompletenessResultSerializer({"completeness_score": application.completeness_score, "checklist": checklist}).data)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit_application(self, request, pk=None):
        application = self.get_object()
        if request.user.role != "applicant" or application.applicant_id != request.user.id:
            raise PermissionDenied("You can submit only your own application.")
        case, created = ApplicationSubmissionService.submit(application, request)
        return Response(
            {
                "detail": "Application submitted.",
                "application_id": application.id,
                "application_code": application.application_code,
                "case_number": case.case_number,
                "case_id": case.id,
                "case_created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
