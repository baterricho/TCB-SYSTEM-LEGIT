from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from cases.models import Case
from core.audit import create_audit_log
from core.file_validators import validate_message_attachment
from core.notifications import create_notification

from .models import Conversation, Message, MessageAttachment


class MessagingService:
    @staticmethod
    def ensure_participant(case, user):
        return case.applicant_id == user.id or case.taken_by_id == user.id

    @staticmethod
    def get_or_create_conversation(case, user, request=None):
        if not case.is_taken or not case.taken_by_id:
            raise ValidationError("No evaluator has taken this case yet.")
        if not MessagingService.ensure_participant(case, user):
            raise PermissionDenied("You can message only within your own taken case.")
        conversation, _ = Conversation.objects.get_or_create(
            case=case,
            applicant=case.applicant,
            evaluator=case.taken_by,
        )
        return conversation

    @staticmethod
    @transaction.atomic
    def send_message(conversation, sender, content="", files=None, request=None):
        if not MessagingService.ensure_participant(conversation.case, sender):
            raise PermissionDenied("You can message only within your own taken case.")
        if not content and not files:
            raise ValidationError("Message body or attachment is required.")
        message = Message.objects.create(conversation=conversation, sender=sender, content=content, has_attachment=bool(files))
        for uploaded_file in files or []:
            mime_type = validate_message_attachment(uploaded_file)
            MessageAttachment.objects.create(
                message=message,
                file_path=uploaded_file,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                mime_type=mime_type,
            )
        recipient = conversation.evaluator if sender_id_matches(sender, conversation.applicant_id) else conversation.applicant
        create_notification(recipient, "New Case Message", f"You have a new message for Case #{conversation.case.case_number}.", "message", conversation.case, recipient.role)
        create_audit_log(request, sender, "message.sent", conversation.case.case_number, "Message sent.", related_case=conversation.case)
        return message


def sender_id_matches(sender, user_id):
    return sender.id == user_id
