from django.urls import path
from .evaluator_views import EvaluatorDashboardSummaryView, EvaluatorReportsView

urlpatterns = [
    path("dashboard-summary/", EvaluatorDashboardSummaryView.as_view(), name="evaluator-dashboard-summary"),
    path("reports/<str:report_name>/", EvaluatorReportsView.as_view(), name="evaluator-reports"),
]
