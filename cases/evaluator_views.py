from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from accounts.models import CustomUser
from .models import Case
from messaging.models import Conversation

class BaseEvaluatorView(APIView):
    def check_evaluator(self, request):
        if request.user.role != CustomUser.Role.EVALUATOR:
            raise PermissionDenied("Only evaluators can access this endpoint.")

class EvaluatorDashboardSummaryView(BaseEvaluatorView):
    def get(self, request):
        self.check_evaluator(request)
        user = request.user
        
        from .services import evaluator_matches_case
        available_cases = [
            case for case in Case.objects.filter(is_taken=False, status=Case.Status.PENDING)
            if evaluator_matches_case(user, case)
        ]
        
        my_cases = Case.objects.filter(taken_by=user)
        
        unread_messages = 0
        unread_notifications = user.notifications.filter(is_read=False).count() if hasattr(user, "notifications") else 0
        
        data = {
            "available_cases": len(available_cases),
            "my_cases": my_cases.count(),
            "under_review_cases": my_cases.filter(status=Case.Status.UNDER_REVIEW).count(),
            "evaluated_cases": my_cases.filter(status=Case.Status.EVALUATED).count(),
            "on_going_cases": my_cases.filter(status=Case.Status.ON_GOING).count(),
            "certified_cases": my_cases.filter(status=Case.Status.CERTIFIED).count(),
            "overdue_cases": my_cases.filter(deadline__lt=timezone.now().date()).count(),
            "due_soon_cases": my_cases.filter(deadline__gte=timezone.now().date(), deadline__lte=timezone.now().date() + timezone.timedelta(days=7)).count(),
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
            return Response(distribution)
        elif report_name == "monthly-evaluations":
            return Response([])
        elif report_name == "deadline-monitoring":
            return Response([])
        elif report_name == "workload-summary":
            return Response([])
        else:
            return Response({"detail": "Unknown report."}, status=status.HTTP_404_NOT_FOUND)
