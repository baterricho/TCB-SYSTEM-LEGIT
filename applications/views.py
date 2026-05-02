"""
Views for IP application management.
Thin controllers — complex logic delegates to services.

New endpoints:
  PATCH /api/applications/<app_id>/documents/<doc_id>/stamp/
    — Evaluator applies 'Reviewed By' stamp to a document.
  PATCH /api/applications/<id>/consent/
    — Applicant updates their marketplace consent.
"""

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from core.permissions import (
    IsAdmin,
    IsAdminOrEvaluator,
    IsOwnerOrAdmin,
    IsOwnerOrAdminOrAssignedEvaluator,
)
from .models import IPApplication, IPDocument, IPRequirement, PaymentRecord, CoInventor
from .serializers import (
    IPApplicationSerializer,
    IPApplicationListSerializer,
    IPApplicationCreateSerializer,
    IPDocumentSerializer,
    IPRequirementSerializer,
    PaymentRecordSerializer,
    PaymentVerificationSerializer,
    CoInventorSerializer,
    MarketplaceConsentSerializer,
    ArchiveApplicationSerializer,
)


class IPApplicationListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/applications/ — List applications (role-filtered).
    POST /api/applications/ — Create a new draft application.
    """

    permission_classes = [IsAuthenticated]
    filterset_fields = ["ip_type", "status", "stage", "is_archived"]
    search_fields = ["transaction_code", "title", "description"]
    ordering_fields = ["created_at", "title", "status"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return IPApplicationCreateSerializer
        return IPApplicationListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = IPApplication.objects.select_related("created_by", "assigned_evaluator")
        if user.role == "admin":
            return qs  # Admin sees all
        elif user.role == "evaluator":
            return qs.filter(assigned_evaluator=user, is_archived=False)
        else:
            return qs.filter(created_by=user, is_archived=False)  # Applicant sees own

    def perform_create(self, serializer):
        application = serializer.save(created_by=self.request.user, status="Draft")

        from services.audit_service import log_audit
        log_audit(
            user=self.request.user,
            action="CREATE_APPLICATION",
            entity=f"IPApplication:{application.id}",
        )


class IPApplicationDetailView(generics.RetrieveUpdateAPIView):
    """
    GET        /api/applications/<id>/ — Get application details.
    PUT/PATCH  /api/applications/<id>/ — Update application (owner/admin only, draft status).
    """

    permission_classes = [IsAuthenticated, IsOwnerOrAdminOrAssignedEvaluator]
    serializer_class = IPApplicationSerializer

    def get_queryset(self):
        return IPApplication.objects.select_related(
            "created_by", "assigned_evaluator"
        ).prefetch_related("documents", "coinventors", "payments")

    def perform_update(self, serializer):
        application = self.get_object()
        # Only allow edits if in Draft status (for applicants)
        if self.request.user.role == "applicant" and application.status != "Draft":
            raise PermissionDenied("You can only edit applications in Draft status.")
        serializer.save()

        from services.audit_service import log_audit
        log_audit(
            user=self.request.user,
            action="UPDATE_APPLICATION",
            entity=f"IPApplication:{application.id}",
        )


class SubmitApplicationView(APIView):
    """POST /api/applications/<id>/submit/ — Submit a draft application."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        application = get_object_or_404(IPApplication, pk=pk)

        if application.created_by != request.user:
            return Response(
                {"error": "Only the application owner can submit."},
                status=status.HTTP_403_FORBIDDEN,
            )

        from services.application_service import submit_application
        submit_application(application=application, user=request.user)

        return Response(
            {"message": "Application submitted successfully."},
            status=status.HTTP_200_OK,
        )


class ArchiveApplicationView(APIView):
    """
    PATCH /api/applications/<id>/archive/ - Admin archives or restores a case.
    Archived cases stay retained for audit/IP records but leave active queues.
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        application = get_object_or_404(IPApplication, pk=pk)
        serializer = ArchiveApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["is_archived"]:
            application.archive(
                user=request.user,
                reason=serializer.validated_data.get("reason", ""),
            )
            action = "ARCHIVE_APPLICATION"
            message = "Application archived."
        else:
            application.restore()
            action = "RESTORE_APPLICATION"
            message = "Application restored."

        from services.audit_service import log_audit
        log_audit(
            user=request.user,
            action=action,
            entity=f"IPApplication:{application.id}",
        )

        return Response(
            {"message": message, "application": IPApplicationSerializer(application).data},
            status=status.HTTP_200_OK,
        )


class AssignEvaluatorView(APIView):
    """POST /api/applications/<id>/assign/ — Assign an evaluator (admin only)."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        application = get_object_or_404(IPApplication, pk=pk)

        from services.application_service import assign_evaluator
        evaluator_id = request.data.get("evaluator_id")
        assign_evaluator(
            application=application,
            evaluator_id=evaluator_id,
            admin_user=request.user,
        )

        return Response(
            {"message": "Evaluator assigned successfully."},
            status=status.HTTP_200_OK,
        )


class IPDocumentUploadView(APIView):
    """POST /api/applications/<id>/documents/ — Upload documents."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        application = get_object_or_404(IPApplication, pk=pk)

        # Only owner or admin can upload
        if application.created_by != request.user and request.user.role != "admin":
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        files = request.FILES.getlist("files")
        if not files:
            files = [request.FILES.get("file")]
            files = [f for f in files if f is not None]

        if not files:
            return Response(
                {"error": "No files provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document_type = request.data.get("document_type", "Other")
        created_docs = []

        for file_obj in files:
            serializer = IPDocumentSerializer(data={
                "file": file_obj,
                "document_type": document_type,
            })
            serializer.is_valid(raise_exception=True)
            doc = serializer.save(application=application)
            created_docs.append(doc)

            from services.audit_service import log_audit
            log_audit(
                user=request.user,
                action="UPLOAD_DOCUMENT",
                entity=f"IPDocument:{doc.id}",
            )

        return Response(
            {
                "message": f"{len(created_docs)} document(s) uploaded.",
                "documents": IPDocumentSerializer(created_docs, many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )


class IPDocumentDeleteView(APIView):
    """DELETE /api/applications/<app_id>/documents/<doc_id>/ — Delete a document."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, doc_pk):
        document = get_object_or_404(IPDocument, pk=doc_pk, application__pk=pk)

        if document.application.created_by != request.user and request.user.role != "admin":
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        from services.audit_service import log_audit
        log_audit(
            user=request.user,
            action="DELETE_DOCUMENT",
            entity=f"IPDocument:{document.id}",
        )

        document.file.delete()
        document.delete()

        return Response(
            {"message": "Document deleted."},
            status=status.HTTP_200_OK,
        )


class IPRequirementListView(generics.ListAPIView):
    """
    GET /api/applications/requirements/ - Public checklist/forms directory.
    Optional query params: ip_type, category.
    """

    permission_classes = [AllowAny]
    serializer_class = IPRequirementSerializer
    filterset_fields = ["ip_type", "category", "is_required"]
    search_fields = ["title", "description"]
    ordering_fields = ["ip_type", "sort_order", "title"]

    def get_queryset(self):
        return IPRequirement.objects.filter(is_active=True)


class PaymentRecordListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/applications/<id>/payments/ - List case payment/OR records.
    POST /api/applications/<id>/payments/ - Applicant/admin records uploaded proof.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PaymentRecordSerializer

    def get_application(self):
        return get_object_or_404(
            IPApplication.objects.select_related("created_by", "assigned_evaluator"),
            pk=self.kwargs["pk"],
        )

    def get_queryset(self):
        application = self.get_application()
        user = self.request.user

        if (
            user.role == "admin"
            or application.created_by == user
            or application.assigned_evaluator == user
        ):
            return PaymentRecord.objects.filter(application=application).select_related(
                "receipt_document", "verified_by"
            )
        return PaymentRecord.objects.none()

    def perform_create(self, serializer):
        application = self.get_application()
        user = self.request.user

        if application.created_by != user and user.role != "admin":
            raise PermissionDenied("Only the applicant or an admin can record payment proof.")

        receipt_document = serializer.validated_data.get("receipt_document")
        if receipt_document and receipt_document.application_id != application.id:
            raise ValidationError(
                {"receipt_document": "Receipt document must belong to this application."}
            )
        if receipt_document and receipt_document.document_type != "Receipt":
            raise ValidationError(
                {"receipt_document": "Selected document must be uploaded as a Receipt."}
            )

        payment = serializer.save(
            application=application,
            status="Submitted" if receipt_document else "Pending",
        )

        from services.audit_service import log_audit
        log_audit(
            user=user,
            action="SUBMIT_PAYMENT_PROOF",
            entity=f"PaymentRecord:{payment.id}",
        )


class VerifyPaymentRecordView(APIView):
    """
    PATCH /api/applications/<id>/payments/<payment_id>/verify/
    Admin or assigned evaluator verifies/rejects payment proof.
    """

    permission_classes = [IsAuthenticated, IsAdminOrEvaluator]

    def patch(self, request, pk, payment_pk):
        payment = get_object_or_404(
            PaymentRecord.objects.select_related(
                "application", "application__created_by", "application__assigned_evaluator"
            ),
            pk=payment_pk,
            application__pk=pk,
        )
        application = payment.application

        if request.user.role == "evaluator" and application.assigned_evaluator != request.user:
            return Response(
                {"error": "You are not the assigned evaluator for this application."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PaymentVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment.status = serializer.validated_data["status"]
        payment.notes = serializer.validated_data.get("notes", "")
        payment.verified_by = request.user
        payment.verified_at = timezone.now()
        payment.save()

        from services.notification_service import send_notification
        send_notification(
            user=application.created_by,
            message=(
                f"Payment proof for '{application.title}' was marked "
                f"{payment.status.lower()}."
            ),
        )

        from services.audit_service import log_audit
        log_audit(
            user=request.user,
            action=f"PAYMENT_{payment.status.upper()}",
            entity=f"PaymentRecord:{payment.id}",
        )

        return Response(
            {
                "message": f"Payment proof {payment.status.lower()}.",
                "payment": PaymentRecordSerializer(payment).data,
            },
            status=status.HTTP_200_OK,
        )


class StampDocumentView(APIView):
    """
    PATCH /api/applications/<app_id>/documents/<doc_id>/stamp/
    Evaluator applies a 'Reviewed By' digital stamp to a document.
    Only the assigned evaluator or admin can stamp.
    """

    permission_classes = [IsAuthenticated, IsAdminOrEvaluator]

    def patch(self, request, pk, doc_pk):
        document = get_object_or_404(IPDocument, pk=doc_pk, application__pk=pk)
        application = document.application

        # Ensure the evaluator is assigned to this application
        if (
            request.user.role == "evaluator"
            and application.assigned_evaluator != request.user
        ):
            return Response(
                {"error": "You are not the assigned evaluator for this application."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if document.is_stamped:
            return Response(
                {"error": "This document has already been stamped."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.reviewed_by = request.user
        document.reviewed_at = timezone.now()
        document.save()

        from services.audit_service import log_audit
        log_audit(
            user=request.user,
            action="STAMP_DOCUMENT",
            entity=f"IPDocument:{document.id}",
        )

        return Response(
            {
                "message": f"Document stamped as reviewed by {request.user.full_name}.",
                "document": IPDocumentSerializer(document).data,
            },
            status=status.HTTP_200_OK,
        )


class UpdateMarketplaceConsentView(APIView):
    """
    PATCH /api/applications/<id>/consent/
    Applicant updates their marketplace consent for their own application.
    Only the application owner can change this.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        application = get_object_or_404(IPApplication, pk=pk)

        if application.created_by != request.user:
            return Response(
                {"error": "Only the application owner can change marketplace consent."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = MarketplaceConsentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        application.marketplace_consent = serializer.validated_data["marketplace_consent"]
        application.save()

        consent_status = "granted" if application.marketplace_consent else "revoked"

        from services.audit_service import log_audit
        log_audit(
            user=request.user,
            action=f"MARKETPLACE_CONSENT_{consent_status.upper()}",
            entity=f"IPApplication:{application.id}",
        )

        return Response(
            {
                "message": f"Marketplace consent {consent_status}.",
                "marketplace_consent": application.marketplace_consent,
            },
            status=status.HTTP_200_OK,
        )


class CoInventorListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/applications/<id>/coinventors/ — List co-inventors.
    POST /api/applications/<id>/coinventors/ — Add a co-inventor.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CoInventorSerializer

    def get_queryset(self):
        return CoInventor.objects.filter(application__pk=self.kwargs["pk"])

    def perform_create(self, serializer):
        application = get_object_or_404(IPApplication, pk=self.kwargs["pk"])
        if application.created_by != self.request.user and self.request.user.role != "admin":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Permission denied.")
        serializer.save(application=application)


class CoInventorDeleteView(generics.DestroyAPIView):
    """DELETE /api/applications/<app_id>/coinventors/<coinventor_id>/ — Remove a co-inventor."""

    permission_classes = [IsAuthenticated]
    serializer_class = CoInventorSerializer

    def get_queryset(self):
        return CoInventor.objects.filter(application__pk=self.kwargs["pk"])

    def get_object(self):
        return get_object_or_404(
            CoInventor,
            pk=self.kwargs["coinventor_pk"],
            application__pk=self.kwargs["pk"],
        )
