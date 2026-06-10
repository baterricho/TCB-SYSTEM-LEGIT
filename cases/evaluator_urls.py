from django.urls import path
from .evaluator_views import EvaluatorCaseExportView, EvaluatorDashboardSummaryView, EvaluatorReportsView

urlpatterns = [
    path("dashboard-summary/", EvaluatorDashboardSummaryView.as_view(), name="evaluator-dashboard-summary"),
    path("export/cases/", EvaluatorCaseExportView.as_view(), name="evaluator-case-export"),
    path("reports/<str:report_name>/", EvaluatorReportsView.as_view(), name="evaluator-reports"),
]
