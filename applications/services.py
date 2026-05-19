import re

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.audit import create_audit_log
from core.notifications import create_notification

from .models import ApplicationChecklist, IPApplication


ENGLISH_VALIDATION_MESSAGE = (
    "Please use English. The system detected Tagalog or non-English text. "
    "For consistency and proper evaluation, kindly provide your answer in English."
)
MISSING_INFORMATION_MESSAGE = "Some required information is missing. Please complete the missing sections before submission."

TAGALOG_MARKERS = {
    "ang", "ng", "mga", "sa", "para", "kaya", "dahil", "hindi", "ito", "iyon",
    "ako", "ikaw", "kami", "tayo", "nila", "namin", "atin", "kung", "mayroon",
    "wala", "gamit", "ginagamit", "paano", "bakit", "saan", "kailan",
}


def contains_non_english(text):
    if not text:
        return False
    lowered = text.lower()
    words = set(re.findall(r"[a-zA-Z]+", lowered))
    if len(words & TAGALOG_MARKERS) >= 2:
        return True
    non_latin = sum(1 for char in text if ord(char) > 127 and not char.isspace())
    return bool(text and non_latin / max(len(text), 1) > 0.15)


class CompletenessService:
    REQUIRED_BY_TYPE = {
        IPApplication.IPType.PATENT: ["Applicant Information", "IP Type Selection", "Title", "Description", "Claims", "Abstract", "Supporting Documents", "Declaration"],
        IPApplication.IPType.UTILITY_MODEL: ["Applicant Information", "IP Type Selection", "Title", "Description", "Claims", "Abstract", "Supporting Documents", "Declaration"],
        IPApplication.IPType.INDUSTRIAL_DESIGN: ["Applicant Information", "IP Type Selection", "Title", "Description", "Drawings", "Supporting Documents", "Declaration"],
        IPApplication.IPType.TRADEMARK: ["Applicant Information", "IP Type Selection", "Title", "Description", "Supporting Documents", "Declaration"],
        IPApplication.IPType.COPYRIGHT: ["Applicant Information", "IP Type Selection", "Title", "Description", "Supporting Documents", "Declaration"],
    }

    @staticmethod
    def validate_language(application):
        fields = [
            application.title,
            application.description,
            application.abstract,
            application.claims,
            application.technical_explanation,
            application.novelty_explanation,
            application.supporting_details,
        ]
        if any(contains_non_english(value) for value in fields):
            application.language_validation_status = IPApplication.LanguageStatus.FAILED
            application.save(update_fields=["language_validation_status"])
            raise ValidationError(ENGLISH_VALIDATION_MESSAGE)
        application.language_validation_status = IPApplication.LanguageStatus.VALID
        application.save(update_fields=["language_validation_status"])

    @staticmethod
    def _status_for_item(application, item_name):
        applicant = application.applicant
        if item_name == "Applicant Information":
            return ApplicationChecklist.Status.COMPLETE if applicant.first_name and applicant.last_name and applicant.email else ApplicationChecklist.Status.MISSING
        if item_name == "IP Type Selection":
            return ApplicationChecklist.Status.COMPLETE if application.ip_type else ApplicationChecklist.Status.MISSING
        if item_name == "Title":
            return ApplicationChecklist.Status.COMPLETE if application.title else ApplicationChecklist.Status.MISSING
        if item_name == "Description":
            return ApplicationChecklist.Status.COMPLETE if application.description else ApplicationChecklist.Status.MISSING
        if item_name == "Claims":
            return ApplicationChecklist.Status.COMPLETE if application.claims else ApplicationChecklist.Status.MISSING
        if item_name == "Abstract":
            return ApplicationChecklist.Status.COMPLETE if application.abstract else ApplicationChecklist.Status.MISSING
        if item_name == "Drawings":
            has_drawings = hasattr(application, "case") and application.case.documents.filter(document_type__icontains="drawing").exists()
            return ApplicationChecklist.Status.COMPLETE if has_drawings else ApplicationChecklist.Status.NEEDS_REVIEW
        if item_name == "Supporting Documents":
            if hasattr(application, "case"):
                return ApplicationChecklist.Status.COMPLETE if application.case.documents.exists() else ApplicationChecklist.Status.MISSING
            return ApplicationChecklist.Status.OPTIONAL
        if item_name == "Payment Proof if applicable":
            return ApplicationChecklist.Status.OPTIONAL
        if item_name == "Declaration":
            return ApplicationChecklist.Status.COMPLETE if application.declaration_accepted else ApplicationChecklist.Status.MISSING
        return ApplicationChecklist.Status.OPTIONAL

    @staticmethod
    @transaction.atomic
    def run(application):
        CompletenessService.validate_language(application)
        items = list(CompletenessService.REQUIRED_BY_TYPE.get(application.ip_type, []))
        items.append("Payment Proof if applicable")
        completed = 0
        required_count = len([item for item in items if item != "Payment Proof if applicable"])
        checklist = []
        for item in items:
            status = CompletenessService._status_for_item(application, item)
            if status == ApplicationChecklist.Status.COMPLETE:
                completed += 1
            record, _ = ApplicationChecklist.objects.update_or_create(
                application=application,
                item_name=item,
                defaults={"status": status, "remarks": ""},
            )
            checklist.append(record)
        application.completeness_score = int((completed / max(required_count, 1)) * 100)
        application.save(update_fields=["completeness_score"])
        return checklist

    @staticmethod
    def ensure_submittable(application):
        checklist = CompletenessService.run(application)
        missing = [item for item in checklist if item.status in {ApplicationChecklist.Status.MISSING, ApplicationChecklist.Status.NEEDS_REVIEW}]
        if missing:
            raise ValidationError(MISSING_INFORMATION_MESSAGE)


class ApplicationSubmissionService:
    @staticmethod
    @transaction.atomic
    def submit(application, request=None):
        if application.status == IPApplication.Status.SUBMITTED:
            raise ValidationError("This application has already been submitted.")
        CompletenessService.ensure_submittable(application)
        application.status = IPApplication.Status.SUBMITTED
        application.submitted_at = timezone.now()
        application.save(update_fields=["status", "submitted_at"])
        from cases.models import Case

        case = Case.objects.create(application=application, applicant=application.applicant)
        admins = application.applicant.__class__.objects.filter(role="admin", status="active")
        for admin in admins:
            create_notification(
                admin,
                "New Application Submitted",
                f"Application {application.application_code} was submitted and Case #{case.case_number} was created.",
                "application_submitted",
                case,
                "admin",
            )
        create_audit_log(request, application.applicant, "application.submitted", application.application_code, f"Case {case.case_number} created.", related_case=case)
        return case
