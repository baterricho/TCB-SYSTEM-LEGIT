from rest_framework import generics, status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils.http import content_disposition_header

from cases.models import Case
from core.permissions import IsEvaluator
from security_keys.services import AESGCMDocumentCipher

from .models import Conversation, Message, MessageAttachment
from .serializers import ConversationCreateSerializer, ConversationSerializer, MessageSerializer, SendMessageSerializer
from .services import MessagingService


class EvaluatorConversationListView(generics.ListAPIView):
    permission_classes = [IsEvaluator]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(evaluator=self.request.user).select_related("case", "applicant", "evaluator")


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ("case",)

    def get_queryset(self):
        user = self.request.user
        qs = Conversation.objects.select_related("case", "applicant", "evaluator")
        if user.role == "admin":
            return qs
        if user.role == "applicant":
            return qs.filter(applicant=user)
        if user.role == "evaluator":
            return qs.filter(evaluator=user)
        return qs.none()

    def create(self, request, *args, **kwargs):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = get_object_or_404(Case, pk=serializer.validated_data["case"])
        conversation = MessagingService.get_or_create_conversation(case, request.user, request)
        return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"], url_path="messages")
    def list_messages(self, request, pk=None):
        conversation = self.get_object()
        if request.user.role != "admin" and not MessagingService.ensure_participant(conversation.case, request.user):
            raise PermissionDenied("You can view only messages connected to your case.")
        if request.method == "POST":
            files = request.FILES.getlist("files") or request.FILES.getlist("file")
            serializer = SendMessageSerializer(data={"content": request.data.get("content", request.data.get("body", "")), "files": files})
            serializer.is_valid(raise_exception=True)
            message = MessagingService.send_message(
                conversation,
                request.user,
                serializer.validated_data.get("content", ""),
                serializer.validated_data.get("files", []),
                request,
            )
            return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
        qs = conversation.messages.select_related("sender").prefetch_related("attachments")
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(MessageSerializer(page, many=True).data)
        return Response(MessageSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="send")
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        if request.user.role != "admin" and not MessagingService.ensure_participant(conversation.case, request.user):
            raise PermissionDenied("You can send messages only within your own case.")
        files = request.FILES.getlist("files") or request.FILES.getlist("file")
        serializer = SendMessageSerializer(data={"content": request.data.get("content", request.data.get("body", "")), "files": files})
        serializer.is_valid(raise_exception=True)
        message = MessagingService.send_message(
            conversation,
            request.user,
            serializer.validated_data.get("content", ""),
            serializer.validated_data.get("files", []),
            request,
        )
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_as_read(self, request, pk=None):
        conversation = self.get_object()
        if request.user.role != "admin" and not MessagingService.ensure_participant(conversation.case, request.user):
            raise PermissionDenied("You can update only your messages.")
        Message.objects.filter(conversation=conversation).exclude(sender=request.user).update(is_read=True)
        return Response({"detail": "Messages marked as read."})


class MessageAttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = MessageAttachment.objects.all()

    @action(detail=True, methods=["get"], url_path="download")
    def secure_download(self, request, pk=None):
        attachment = self.get_object()
        case = attachment.message.conversation.case
        if request.user.role != "admin" and not MessagingService.ensure_participant(case, request.user):
            raise PermissionDenied("You do not have permission to download this attachment.")
        try:
            with attachment.file_path.open("rb") as f:
                ciphertext = f.read()
        except Exception as e:
            raise ValidationError(f"Could not read attachment file: {str(e)}")
        if attachment.is_encrypted:
            plaintext = AESGCMDocumentCipher.decrypt(ciphertext, attachment.encryption_key, attachment.nonce)
        else:
            plaintext = ciphertext
        response = HttpResponse(plaintext, content_type=attachment.mime_type)
        response["Content-Disposition"] = content_disposition_header(True, attachment.original_filename)
        response["Content-Length"] = len(plaintext)
        return response
