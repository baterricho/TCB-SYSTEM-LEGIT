from django.http import HttpResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.http import content_disposition_header
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from cases.models import Case

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .services import DocumentService


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]
    filterset_fields = ("document_type", "case", "is_confidential")
    search_fields = ("original_filename", "document_type", "case__case_number")

    def get_queryset(self):
        user = self.request.user
        qs = Document.objects.select_related("case", "uploaded_by", "encryption_key")
        if user.role == "admin":
            return qs
        if user.role == "applicant":
            return qs.filter(
                Q(uploaded_by=user)
                | Q(case__applicant=user)
                | Q(case__application__applicant=user)
            )
        if user.role == "evaluator":
            return qs.filter(case__taken_by=user)
        return qs.none()

    def create(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = None
        if serializer.validated_data.get("case"):
            case = get_object_or_404(Case, pk=serializer.validated_data["case"])
        document = DocumentService.upload(
            uploaded_file=serializer.validated_data["file"],
            uploaded_by=request.user,
            document_type=serializer.validated_data["document_type"],
            case=case,
            request=request,
        )
        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="download")
    def secure_download(self, request, pk=None):
        document = self.get_object()
        plaintext = DocumentService.decrypt(document, request.user, request)
        response = HttpResponse(plaintext, content_type=document.mime_type)
        response["Content-Disposition"] = content_disposition_header(True, document.original_filename)
        response["Content-Length"] = len(plaintext)
        return response

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        if document.uploaded_by_id != request.user.id and request.user.role != "admin":
            raise PermissionDenied("You can delete only your own draft document.")
        if request.user.role != "admin" and document.case.status != Case.Status.PENDING:
            raise ValidationError("Only pending-case documents can be deleted.")
        return super().destroy(request, *args, **kwargs)
