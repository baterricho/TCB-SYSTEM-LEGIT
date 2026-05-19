from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import FeeAssessment, Payment
from .serializers import FeeAssessmentSerializer, PaymentDecisionSerializer, PaymentSerializer, PaymentUploadSerializer
from .services import PaymentService


class FeeAssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = FeeAssessmentSerializer
    filterset_fields = ("status", "fee_type", "case", "application", "evaluator")
    search_fields = ("case__case_number", "application__application_code", "fee_type", "description")

    def get_queryset(self):
        user = self.request.user
        qs = FeeAssessment.objects.select_related("case", "application", "evaluator")
        if user.role == "admin":
            return qs
        if user.role == "applicant":
            return qs.filter(case__applicant=user)
        if user.role == "evaluator":
            return qs.filter(case__taken_by=user)
        return qs.none()

    def perform_create(self, serializer):
        if self.request.user.role not in {"admin", "evaluator"}:
            raise PermissionDenied("Only admins or case evaluators can issue fee assessments.")
        case = serializer.validated_data["case"]
        if self.request.user.role == "evaluator" and case.taken_by_id != self.request.user.id:
            raise PermissionDenied("Only the evaluator who took this case can issue fee assessments.")
        serializer.save(evaluator=self.request.user, issued_at=timezone.now(), status=FeeAssessment.Status.ISSUED)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ("payment_status", "payment_method", "case", "assessment")
    search_fields = ("original_filename", "receipt_no", "case__case_number", "applicant__email")

    def get_queryset(self):
        user = self.request.user
        qs = Payment.objects.select_related("assessment", "case", "applicant", "verified_by", "encryption_key")
        if user.role == "admin":
            return qs
        if user.role == "applicant":
            return qs.filter(applicant=user)
        if user.role == "evaluator":
            return qs.filter(case__taken_by=user)
        return qs.none()

    def create(self, request, *args, **kwargs):
        serializer = PaymentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = PaymentService.upload_receipt(
            uploaded_file=serializer.validated_data["file"],
            applicant=request.user,
            assessment=serializer.validated_data["assessment"],
            amount_paid=serializer.validated_data["amount_paid"],
            payment_method=serializer.validated_data["payment_method"],
            receipt_no=serializer.validated_data.get("receipt_no", ""),
            payment_date=serializer.validated_data.get("payment_date"),
            request=request,
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="download")
    def download_receipt(self, request, pk=None):
        payment = self.get_object()
        plaintext = PaymentService.decrypt_receipt(payment, request.user, request)
        response = HttpResponse(plaintext, content_type=payment.mime_type)
        response["Content-Disposition"] = f'attachment; filename="{payment.original_filename}"'
        response["Content-Length"] = len(plaintext)
        return response

    @action(detail=True, methods=["post"], url_path="verify")
    def verify_receipt(self, request, pk=None):
        payment = self.get_object()
        serializer = PaymentDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = PaymentService.verify(payment, request.user, serializer.validated_data.get("remarks", ""), request)
        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject_receipt(self, request, pk=None):
        payment = self.get_object()
        serializer = PaymentDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = PaymentService.reject(payment, request.user, serializer.validated_data.get("remarks", ""), request)
        return Response(PaymentSerializer(payment).data)


PaymentProofViewSet = PaymentViewSet
