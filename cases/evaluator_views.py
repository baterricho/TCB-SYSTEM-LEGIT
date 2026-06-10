from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import CustomUser
from core.audit import create_audit_log
from reports.services import ExportReportService

from .models import Case


class BaseEvaluatorView(APIView):
    permission_classes = [IsAuthenticated]

    def check_evaluator(self, request):
        if getattr(request.user, "role", None) != CustomUser.Role.EVALUATOR:
            raise PermissionDenied("Only evaluators can access this endpoint.")


class EvaluatorDashboardSummaryView(BaseEvaluatorView):
    def get(self, request):
        self.check_evaluator(request)
        user = request.user
        now = timezone.now()
        due_soon_until = now + timedelta(days=7)

        from .services import ensure_cases_for_submitted_applications, evaluator_matches_case

        ensure_cases_for_submitted_applications()

        try:
            profile = user.evaluator_profile
        except CustomUser.evaluator_profile.RelatedObjectDoesNotExist:
            profile = None

        available_cases = [
            case
            for case in Case.objects.select_related("application").filter(
                Q(assigned_evaluator__isnull=True) | Q(assigned_evaluator=user),
                application__status="submitted",
                is_taken=False,
                taken_by__isnull=True,
                status=Case.Status.PENDING,
            )
            if evaluator_matches_case(user, case)
        ]

        my_cases = Case.objects.filter(taken_by=user)

        counts = my_cases.aggregate(
            my_cases_count=Count("id"),
            under_review_cases=Count("id", filter=Q(status=Case.Status.UNDER_REVIEW)),
            evaluated_cases=Count("id", filter=Q(status=Case.Status.EVALUATED)),
            on_going_cases=Count("id", filter=Q(status=Case.Status.ON_GOING)),
            certified_cases=Count("id", filter=Q(status=Case.Status.CERTIFIED)),
            overdue_cases=Count("id", filter=Q(deadline__lt=now)),
            due_soon_cases=Count("id", filter=Q(deadline__gte=now, deadline__lte=due_soon_until)),
        )

        unread_messages = 0
        unread_notifications = user.notifications.filter(is_read=False).count() if hasattr(user, "notifications") else 0

        data = {
            "available_cases": len(available_cases),
            "my_cases": counts["my_cases_count"],
            "under_review_cases": counts["under_review_cases"],
            "evaluated_cases": counts["evaluated_cases"],
            "on_going_cases": counts["on_going_cases"],
            "certified_cases": counts["certified_cases"],
            "overdue_cases": counts["overdue_cases"],
            "due_soon_cases": counts["due_soon_cases"],
            "unread_messages": unread_messages,
            "unread_notifications": unread_notifications,
        }
        return Response(data)


class EvaluatorReportsView(BaseEvaluatorView):
    def get(self, request, report_name):
        self.check_evaluator(request)
        user = request.user
        my_cases = Case.objects.filter(taken_by=user)

        if report_name == "cases-by-status":
            distribution = my_cases.values("status").annotate(count=Count("id"))
            return Response(list(distribution))
        elif report_name == "monthly-evaluations":
            from .models import CaseEvaluation

            return Response(
                list(
                    CaseEvaluation.objects.filter(evaluator=user)
                    .annotate(month=TruncMonth("created_at"))
                    .values("month")
                    .annotate(count=Count("id"))
                    .order_by("month")
                )
            )
        elif report_name == "deadline-monitoring":
            due_soon_until = timezone.now() + timedelta(days=7)
            return Response(
                {
                    "overdue": my_cases.filter(deadline__lt=timezone.now()).count(),
                    "due_soon": my_cases.filter(deadline__gte=timezone.now(), deadline__lte=due_soon_until).count(),
                    "no_deadline": my_cases.filter(deadline__isnull=True).count(),
                }
            )
        elif report_name == "workload-summary":
            return Response(
                {
                    "active_cases": my_cases.exclude(status__in=[Case.Status.CERTIFIED, Case.Status.ARCHIVED]).count(),
                    "completed_cases": my_cases.filter(status__in=[Case.Status.EVALUATED, Case.Status.CERTIFIED]).count(),
                    "total_cases": my_cases.count(),
                }
            )
        else:
            return Response({"detail": "Unknown report."}, status=status.HTTP_404_NOT_FOUND)


class EvaluatorCaseExportView(BaseEvaluatorView):
    def get(self, request):
        self.check_evaluator(request)

        forbidden_filters = {"evaluator", "evaluator_id", "assigned_evaluator", "assigned_evaluator_id", "taken_by", "taken_by_id"}
        attempted_scope_override = sorted(forbidden_filters.intersection(request.query_params.keys()))
        if attempted_scope_override:
            create_audit_log(
                request=request,
                user=request.user,
                action="reports.evaluator_export_denied",
                record="evaluator_case_report",
                details=f"Evaluator attempted to export with unauthorized scope filters: {', '.join(attempted_scope_override)}.",
                target="reports",
            )
            raise PermissionDenied("Evaluators can export only assigned or taken cases.")

        response = ExportReportService.evaluator_case_report_csv(request)
        create_audit_log(
            request=request,
            user=request.user,
            action="reports.evaluator_case_report_exported",
            record="evaluator_case_report",
            details="Evaluator exported case report.",
            target="reports",
        )
        return response
