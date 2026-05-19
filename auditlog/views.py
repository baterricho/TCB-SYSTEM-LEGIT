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
    search_fields = ("account_name", "record", "details", "ip_address")
    ordering_fields = ("log_timestamp", "action", "role")

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(["log_timestamp", "user", "related_case", "account_name", "role", "action", "target", "record_id", "details", "ip_address", "user_agent"])
        for log in self.filter_queryset(self.get_queryset()):
            writer.writerow([log.log_timestamp, log.user_id, log.related_case_id, log.account_name, log.role, log.action, log.target, log.record_id, log.details, log.ip_address, log.user_agent])
        return response
