import re
from datetime import datetime, time

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import CustomUser
from cases.models import ActivityTimeline, Case
from core.audit import create_audit_log
from core.notifications import create_notification

from .models import EmailParse


UNMATCHED_MESSAGE = "IPOPHL email received but no matching case record was found."


def sender_is_allowed(sender):
    domain = sender.split("@")[-1].lower()
    allowed_senders = {email.lower() for email in settings.IPOPHL_ALLOWED_SENDERS if email}
    allowed_domains = {d.lower() for d in settings.IPOPHL_ALLOWED_DOMAINS if d}
    return sender.lower() in allowed_senders or domain in allowed_domains


def detect_case_number(text):
    match = re.search(r"(TCB-[A-F0-9]{10})", text, flags=re.IGNORECASE)
    return match.group(1).upper() if match else ""


def detect_report_type(text):
    lowered = text.lower()
    for label in ["office action", "examination report", "notice of allowance", "certificate", "deadline notice", "deficiency report"]:
        if label in lowered:
            return label.title()
    return ""


def detect_deadline(text):
    patterns = [
        (r"\b(\d{4}-\d{2}-\d{2})\b", "%Y-%m-%d"),
        (r"\b([A-Z][a-z]+ \d{1,2}, \d{4})\b", "%B %d, %Y"),
        (r"\b(\d{1,2}/\d{1,2}/\d{4})\b", "%m/%d/%Y"),
    ]
    for pattern, fmt in patterns:
        match = re.search(pattern, text)
        if match:
            return datetime.strptime(match.group(1), fmt).date()
    return None


def detect_required_action(text):
    action_match = re.search(r"(required action|action required|please submit|respond by)[:\s]+(.{1,500})", text, flags=re.IGNORECASE | re.DOTALL)
    if action_match:
        return action_match.group(2).strip()
    return ""


class IPOPHLEmailParserService:
    @staticmethod
    @transaction.atomic
    def parse(*, sender, subject, body, attachments_metadata=None, request=None, user=None):
        if user and user.role != CustomUser.Role.ADMIN:
            raise PermissionDenied("Only admins can parse IPOPHL emails.")
        if not sender_is_allowed(sender):
            raise ValidationError("Sender is not allowed for IPOPHL email parsing.")
        text = f"{subject}\n{body}"
        case_number = detect_case_number(text)
        report_type = detect_report_type(text)
        deadline = detect_deadline(text)
        required_action = detect_required_action(text)
        matched_case = Case.objects.filter(case_number__iexact=case_number).first() if case_number else None
        status = EmailParse.Status.MATCHED if matched_case else EmailParse.Status.UNMATCHED
        parse = EmailParse.objects.create(
            sender=sender,
            subject=subject,
            body=body,
            case_number_detected=case_number,
            report_type=report_type,
            deadline_detected=deadline,
            required_action=required_action,
            attachments_metadata=attachments_metadata or [],
            matched_case=matched_case,
            status=status,
        )
        if not matched_case:
            create_audit_log(request, user, "ipophl_email.unmatched", subject, UNMATCHED_MESSAGE)
            return parse, UNMATCHED_MESSAGE
        if deadline:
            matched_case.sla_due_date = timezone.make_aware(
                datetime.combine(deadline, time.min),
                timezone.get_current_timezone(),
            )
            matched_case.save(update_fields=["sla_due_date", "updated_at"])
        if matched_case.is_taken:
            ActivityTimeline.objects.create(
                case=matched_case,
                role_visibility=ActivityTimeline.RoleVisibility.ADMIN,
                action="ipophl_email_matched",
                admin_message=f"IPOPHL email matched. Report type: {report_type or 'Unknown'}. Deadline: {deadline or 'Not detected'}.",
                performed_by=user,
            )
            if required_action:
                ActivityTimeline.objects.create(
                    case=matched_case,
                    role_visibility=ActivityTimeline.RoleVisibility.APPLICANT,
                    action="ipophl_action_required",
                    applicant_message="An IPOPHL update requires action on your case.",
                    performed_by=user,
                )
        if matched_case.taken_by:
            create_notification(matched_case.taken_by, "IPOPHL Email Matched", f"An IPOPHL email was matched to Case #{matched_case.case_number}.", "ipophl_email", matched_case, "evaluator")
        if required_action:
            create_notification(matched_case.applicant, "IPOPHL Action Required", "An IPOPHL update requires action on your case.", "ipophl_email", matched_case, "applicant")
        create_audit_log(request, user, "ipophl_email.matched", matched_case.case_number, f"Report type: {report_type}. Deadline: {deadline}.")
        return parse, ""
