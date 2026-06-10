import csv

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action

from core.permissions import IsAdmin

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("user").all()
    filterset_fields = ("role", "action", "user")
    search_fields = ("account_name", "record_id", "details", "ip_address")
    ordering_fields = ("log_timestamp", "action", "role")

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if not start_date or not end_date:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Both start_date and end_date query parameters are required.")

        from django.utils.dateparse import parse_date
        parsed_start = parse_date(start_date)
        parsed_end = parse_date(end_date)
        if not parsed_start or not parsed_end:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Invalid start_date or end_date format. Use YYYY-MM-DD.")

        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(log_timestamp__date__gte=parsed_start, log_timestamp__date__lte=parsed_end)

        total_count = queryset.count()
        truncated = False
        if total_count > 10000:
            queryset = queryset[:10000]
            truncated = True

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'
        if truncated:
            response["X-Truncated"] = "True"
            response["Warning"] = "199 - 'Export truncated to 10000 rows max'"

        writer = csv.writer(response)
        writer.writerow(["log_timestamp", "user", "related_case", "account_name", "role", "action", "target", "record_id", "details", "ip_address", "user_agent"])
        for log in queryset.iterator():
            writer.writerow([log.log_timestamp, log.user_id, log.related_case_id, log.account_name, log.role, log.action, log.target, log.record_id, log.details, log.ip_address, log.user_agent])
        return response

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        return self.export_csv(request)
