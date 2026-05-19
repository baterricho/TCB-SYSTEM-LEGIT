from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from cases.models import Case

from .models import Conversation, Message
from .serializers import ConversationCreateSerializer, ConversationSerializer, MessageSerializer, SendMessageSerializer
from .services import MessagingService


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
        case = Case.objects.get(pk=serializer.validated_data["case"])
        conversation = MessagingService.get_or_create_conversation(case, request.user, request)
        return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="messages")
    def list_messages(self, request, pk=None):
        conversation = self.get_object()
        if request.user.role != "admin" and not MessagingService.ensure_participant(conversation.case, request.user):
            raise PermissionDenied("You can view only messages connected to your case.")
        return Response(MessageSerializer(conversation.messages.all(), many=True).data)

    @action(detail=True, methods=["post"], url_path="send")
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        serializer = SendMessageSerializer(data={"content": request.data.get("content", request.data.get("body", "")), "files": request.FILES.getlist("files")})
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
