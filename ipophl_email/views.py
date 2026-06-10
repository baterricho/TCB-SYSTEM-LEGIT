from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from cases.models import Case
from core.audit import create_audit_log
from core.permissions import IsAdmin

from .models import EmailParse
from .serializers import EmailParseSerializer, MatchEmailSerializer, ParseEmailSerializer
from .services import IPOPHLEmailParserService


class EmailParseViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = EmailParseSerializer
    queryset = EmailParse.objects.select_related("matched_case").all()
    filterset_fields = ("status", "report_type", "case_number_detected")
    search_fields = ("sender", "subject", "body", "case_number_detected")

    @action(detail=False, methods=["post"], url_path="parse")
    def parse_email(self, request):
        serializer = ParseEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parse, message = IPOPHLEmailParserService.parse(user=request.user, request=request, **serializer.validated_data)
        data = EmailParseSerializer(parse).data
        if message:
            data["detail"] = message
        create_audit_log(request, request.user, "ipophl_email.processed", parse.subject, "Admin processed IPOPHL email.")
        return Response(data, status=201)

    @action(detail=True, methods=["post"], url_path="match")
    def match_email_to_case(self, request, pk=None):
        parse = self.get_object()
        serializer = MatchEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = get_object_or_404(Case, pk=serializer.validated_data["case"])
        parse.matched_case = case
        parse.case_number_detected = case.case_number
        parse.status = EmailParse.Status.MATCHED
        parse.save(update_fields=["matched_case", "case_number_detected", "status"])
        create_audit_log(request, request.user, "ipophl_email.manually_matched", case.case_number, f"Email parse {parse.id} manually matched.")
        return Response(EmailParseSerializer(parse).data)
