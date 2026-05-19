from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdmin

from .services import ReportService


class ReportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, report_name=None):
        mapping = {
            "summary-metrics": ReportService.summary_metrics,
            "applications-by-ip-type": ReportService.applications_by_ip_type,
            "monthly-submissions": ReportService.monthly_submissions,
            "case-status-distribution": ReportService.case_status_distribution,
            "evaluator-workload": ReportService.evaluator_workload,
            "deadline-monitoring": ReportService.deadline_monitoring,
            "inquiry-popularity": ReportService.inquiry_popularity,
            "marketplace-interest": ReportService.marketplace_interest,
        }
        if report_name not in mapping:
            return Response({"detail": "Unknown report."}, status=404)
        return Response(mapping[report_name]())
