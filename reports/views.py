from rest_framework.response import Response
from rest_framework.views import APIView

from core.audit import create_audit_log
from core.permissions import IsAdmin

from .services import ExportReportService, ReportService


class ReportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, report_name=None):
        mapping = {
            "summary-metrics": ReportService.summary_metrics,
            "admin-summary": ReportService.summary_metrics,
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


class PortfolioAnalyticsExportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        response = ExportReportService.portfolio_analytics_csv(request)
        create_audit_log(
            request=request,
            user=request.user,
            action="reports.portfolio_analytics_exported",
            record="portfolio_analytics",
            details="Admin exported portfolio analytics report.",
            target="reports",
        )
        return response
