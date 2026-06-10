from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from accounts.models import CustomUser
from core.audit import create_audit_log
from core.notifications import create_notification
from core.permissions import IsAdmin

from .models import ActivityTimeline, Case
from .serializers import (
    ActivityTimelineSerializer,
    CaseDeadlineSerializer,
    CaseEvaluationSerializer,
    CaseSerializer,
    CaseStatusUpdateSerializer,
    EvaluationSubmitSerializer,
)
from .services import CaseWorkflowService, ensure_cases_for_submitted_applications, evaluator_matches_case


class CaseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CaseSerializer
    filterset_fields = ("status", "is_taken", "application__ip_type")
    search_fields = ("case_number", "application__application_code", "application__title", "applicant__email", "taken_by__email")

    def _paginated_response(self, queryset_or_list, serializer_class=CaseSerializer):
        page = self.paginate_queryset(queryset_or_list)
        if page is not None:
            return self.get_paginated_response(serializer_class(page, many=True).data)
        return Response(serializer_class(queryset_or_list, many=True).data)

    def get_queryset(self):
        user = self.request.user
        qs = Case.objects.select_related("application", "applicant", "taken_by", "assigned_evaluator").prefetch_related("status_history")
        if user.role == CustomUser.Role.ADMIN:
            return qs
        if user.role == CustomUser.Role.APPLICANT:
            return qs.filter(applicant=user)
        if user.role == CustomUser.Role.EVALUATOR:
            return qs.filter(taken_by=user)
        return qs.none()

    def _get_case_any_for_evaluator_action(self):
        if self.request.user.role == CustomUser.Role.ADMIN:
            return get_object_or_404(Case, pk=self.kwargs["pk"])
        if self.action == "take_case":
            return get_object_or_404(Case, pk=self.kwargs["pk"])
        return self.get_object()

    @action(detail=False, methods=["get"], url_path="available")
    def list_available_cases(self, request):
        if request.user.role != CustomUser.Role.EVALUATOR:
            raise PermissionDenied("Only evaluators can view available cases.")
        ensure_cases_for_submitted_applications()
        try:
            request.user.evaluator_profile
        except CustomUser.evaluator_profile.RelatedObjectDoesNotExist:
            pass
        cases = [
            case for case in Case.objects.select_related("application", "applicant", "assigned_evaluator")
            .filter(
                Q(assigned_evaluator__isnull=True) | Q(assigned_evaluator=request.user),
                application__status="submitted",
                is_taken=False,
                taken_by__isnull=True,
                status=Case.Status.PENDING,
            )
            if evaluator_matches_case(request.user, case)
        ]
        return self._paginated_response(cases)

    @action(detail=False, methods=["get"], url_path="my-cases")
    def my_cases(self, request):
        if request.user.role == CustomUser.Role.EVALUATOR:
            qs = CaseWorkflowService.urgency_ordering(Case.objects.filter(taken_by=request.user).select_related("application", "applicant", "taken_by"))
        elif request.user.role == CustomUser.Role.APPLICANT:
            qs = Case.objects.filter(applicant=request.user).select_related("application", "applicant", "taken_by")
        elif request.user.role == CustomUser.Role.ADMIN:
            qs = Case.objects.all().select_related("application", "applicant", "taken_by")
        else:
            qs = Case.objects.none()
        return self._paginated_response(qs)

    @action(detail=True, methods=["post"], url_path="take")
    def take_case(self, request, pk=None):
        case = get_object_or_404(Case, pk=pk)
        case = CaseWorkflowService.take_case(case, request.user, request)
        return Response({
            "detail": "Case Taken Successfully. You have taken this case.",
            "case": CaseSerializer(case).data,
        })

    @action(detail=True, methods=["post"], url_path="update-status")
    def update_case_status(self, request, pk=None):
        case = get_object_or_404(Case, pk=pk)
        serializer = CaseStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = CaseWorkflowService.update_status(
            case,
            request.user,
            serializer.validated_data["status"],
            serializer.validated_data.get("remarks", ""),
            request,
        )
        return Response(CaseSerializer(case).data)

    @action(detail=True, methods=["post"], url_path="evaluation")
    def create_evaluation(self, request, pk=None):
        case = get_object_or_404(Case, pk=pk)
        serializer = EvaluationSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evaluation = CaseWorkflowService.submit_evaluation(
            case,
            request.user,
            serializer.validated_data["content"],
            serializer.validated_data.get("recommendation", ""),
            request,
        )
        return Response(CaseEvaluationSerializer(evaluation).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="payments")
    def list_payments(self, request, pk=None):
        case = self.get_object()
        from payments.serializers import PaymentSerializer

        qs = case.payments.select_related("assessment", "applicant", "verified_by", "encryption_key").all()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(PaymentSerializer(page, many=True).data)
        return Response(PaymentSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="set-deadline")
    def set_deadline(self, request, pk=None):
        case = self.get_object()
        if request.user.role != CustomUser.Role.ADMIN and case.taken_by_id != request.user.id:
            raise PermissionDenied("Only admins or the evaluator who took this case can set the deadline.")
        serializer = CaseDeadlineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case.deadline = serializer.validated_data["deadline"]
        case.sla_due_date = serializer.validated_data["deadline"]
        if serializer.validated_data.get("sla_stage") is not None:
            case.sla_stage = serializer.validated_data.get("sla_stage", "")
        case.save(update_fields=["deadline", "sla_due_date", "sla_stage", "updated_at"])
        create_audit_log(request, request.user, "case.deadline_set", case.case_number, f"Deadline set to {case.deadline}.")
        create_notification(case.applicant, "Case Deadline Updated", f"Your case deadline is {case.deadline}.", "deadline", case, "applicant")
        return Response(CaseSerializer(case).data)

    @action(detail=True, methods=["get"], url_path="timeline")
    def list_timeline(self, request, pk=None):
        case = self.get_object()
        if not case.is_taken:
            return Response({"detail": "No evaluator has taken this case yet.", "results": []})
        if request.user.role == CustomUser.Role.APPLICANT:
            qs = case.activity_timeline.filter(role_visibility__in=[ActivityTimeline.RoleVisibility.APPLICANT, ActivityTimeline.RoleVisibility.ALL])
        elif request.user.role == CustomUser.Role.ADMIN:
            qs = case.activity_timeline.filter(role_visibility__in=[ActivityTimeline.RoleVisibility.ADMIN, ActivityTimeline.RoleVisibility.ALL])
        elif request.user.role == CustomUser.Role.EVALUATOR and case.taken_by_id == request.user.id:
            qs = case.activity_timeline.filter(role_visibility__in=[ActivityTimeline.RoleVisibility.ADMIN, ActivityTimeline.RoleVisibility.ALL])
        else:
            qs = case.activity_timeline.none()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(ActivityTimelineSerializer(page, many=True).data)
        return Response(ActivityTimelineSerializer(qs, many=True).data)
