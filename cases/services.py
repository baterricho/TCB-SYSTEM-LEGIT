from datetime import timedelta

from django.db import transaction
from django.db.models import Case as DbCase
from django.db.models import IntegerField, Value, When
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import CustomUser, EvaluatorProfile
from core.audit import create_audit_log
from core.notifications import create_notification

from .models import ActivityTimeline, Case, CaseEvaluation, CaseStatusHistory


STATUS_LABELS = dict(Case.Status.choices)


def ensure_cases_for_submitted_applications():
    from applications.models import IPApplication

    submitted_without_cases = (
        IPApplication.objects
        .filter(status=IPApplication.Status.SUBMITTED, case__isnull=True)
        .select_related("applicant")[:500]
    )
    created_cases = []
    for application in submitted_without_cases:
        case, created = Case.objects.get_or_create(
            application=application,
            defaults={
                "applicant": application.applicant,
                "status": Case.Status.PENDING,
                "is_taken": False,
                "taken_by": None,
                "assigned_evaluator": None,
                "taken_at": None,
                "deadline": None,
                "priority_score": 0,
                "priority_label": Case.PriorityLabel.NORMAL,
            },
        )
        if created:
            created_cases.append(case)
    return created_cases


def evaluator_matches_case(evaluator, case):
    try:
        profile = evaluator.evaluator_profile
    except EvaluatorProfile.DoesNotExist:
        return False
    specialization = profile.specialization.lower().replace("_", " ")
    ip_type = case.application.ip_type.lower().replace("_", " ")
    ip_label = case.application.get_ip_type_display().lower().replace("_", " ")
    return profile.is_available and (
        "all" in specialization
        or "general" in specialization
        or ip_type in specialization
        or ip_label in specialization
    )


def evaluator_display_name(user):
    return user.get_full_name() or user.email


class CaseWorkflowService:
    @staticmethod
    @transaction.atomic
    def take_case(case, evaluator, request=None):
        if evaluator.role != CustomUser.Role.EVALUATOR:
            raise PermissionDenied("Only evaluators can take cases.")
        admin_users = list(CustomUser.objects.filter(role=CustomUser.Role.ADMIN, status=CustomUser.Status.ACTIVE))
        case = Case.objects.select_for_update().select_related("application", "applicant").get(pk=case.pk)
        if case.is_taken or case.taken_by_id:
            raise ValidationError("This case has already been taken.")
        if not evaluator_matches_case(evaluator, case):
            raise PermissionDenied("This case is outside your allowed specialization.")
        now = timezone.now()
        previous_status = case.status
        case.is_taken = True
        case.taken_by = evaluator
        case.assigned_evaluator = evaluator
        case.taken_at = now
        case.status = Case.Status.UNDER_REVIEW
        case.deadline = now + timedelta(days=90)
        case.sla_stage = "Evaluator Review"
        case.sla_due_date = case.deadline
        case.save(update_fields=["is_taken", "taken_by", "assigned_evaluator", "taken_at", "status", "deadline", "sla_stage", "sla_due_date"])
        EvaluatorProfile.objects.filter(user=evaluator).update(workload_count=evaluator.taken_cases.count())
        CaseStatusHistory.objects.create(
            case=case,
            previous_status=previous_status,
            new_status=case.status,
            changed_by=evaluator,
            remarks="Evaluator took the case.",
        )
        name = evaluator_display_name(evaluator)
        ActivityTimeline.objects.create(
            case=case,
            role_visibility=ActivityTimeline.RoleVisibility.APPLICANT,
            action="case_taken",
            applicant_message=f"{name} took this case.",
            admin_message="",
            performed_by=evaluator,
        )
        ActivityTimeline.objects.create(
            case=case,
            role_visibility=ActivityTimeline.RoleVisibility.ADMIN,
            action="case_taken",
            applicant_message="",
            admin_message=f"{name} took Case #{case.case_number}. The 90-day deadline is {case.deadline.date()}.",
            performed_by=evaluator,
        )
        create_notification(evaluator, "Case Taken Successfully", "You have taken this case.", "case_taken", case, "evaluator")
        create_notification(case.applicant, "Case Accepted", f"Your case has been accepted by {name}.", "case_taken", case, "applicant")
        for admin in admin_users:
            create_notification(admin, "Case Taken by Evaluator", f"{name} took Case #{case.case_number}.", "case_taken", case, "admin")
        create_audit_log(request, evaluator, "case.taken", case.case_number, f"{name} took this case.")
        return case

    @staticmethod
    @transaction.atomic
    def update_status(case, evaluator, new_status, remarks="", request=None):
        if case.taken_by_id != evaluator.id:
            raise PermissionDenied("Only the evaluator who took this case can update the case status.")
        if new_status == case.status:
            raise ValidationError(f"This case is already marked as {STATUS_LABELS.get(new_status, new_status)}.")
        if new_status not in Case.Status.values:
            raise ValidationError("Invalid case status.")
        admin_users = list(CustomUser.objects.filter(role=CustomUser.Role.ADMIN, status=CustomUser.Status.ACTIVE))
        previous_status = case.status
        case.status = new_status
        case.save(update_fields=["status", "updated_at"])
        CaseStatusHistory.objects.create(
            case=case,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=evaluator,
            remarks=remarks,
        )
        label = STATUS_LABELS.get(new_status, new_status)
        ActivityTimeline.objects.create(
            case=case,
            role_visibility=ActivityTimeline.RoleVisibility.APPLICANT,
            action="status_updated",
            applicant_message=f"Your case status is now {label}.",
            performed_by=evaluator,
        )
        ActivityTimeline.objects.create(
            case=case,
            role_visibility=ActivityTimeline.RoleVisibility.ADMIN,
            action="status_updated",
            admin_message=f"Case #{case.case_number} changed from {STATUS_LABELS.get(previous_status, previous_status)} to {label}. Remarks: {remarks}",
            performed_by=evaluator,
        )
        create_notification(case.applicant, "Case Status Updated", f"Your case status is now {label}.", "case_status", case, "applicant")
        for admin in admin_users:
            create_notification(admin, "Case Status Updated", f"Case #{case.case_number} is now {label}.", "case_status", case, "admin")
        create_audit_log(request, evaluator, "case.status_updated", case.case_number, f"{previous_status} -> {new_status}. {remarks}")
        return case

    @staticmethod
    @transaction.atomic
    def submit_evaluation(case, evaluator, content, recommendation="", request=None):
        if case.taken_by_id != evaluator.id:
            raise PermissionDenied("Only the evaluator who took this case can submit an evaluation.")
        evaluation = CaseEvaluation.objects.create(case=case, evaluator=evaluator, content=content, recommendation=recommendation)
        create_audit_log(request, evaluator, "case.evaluation_submitted", case.case_number, "Evaluation submitted.")
        create_notification(case.applicant, "Evaluation Submitted", "An evaluator update has been added to your case.", "evaluation", case, "applicant")
        return evaluation

    @staticmethod
    def urgency_ordering(queryset):
        now = timezone.now()
        today = now.date()
        return queryset.annotate(
            urgency_rank=DbCase(
                When(deadline__isnull=True, then=Value(6)),
                When(deadline__lt=now, then=Value(1)),
                When(deadline__date=today, then=Value(2)),
                When(deadline__date__gt=today, deadline__date__lte=today + timedelta(days=3), then=Value(3)),
                When(deadline__date__gt=today + timedelta(days=3), deadline__date__lte=today + timedelta(days=7), then=Value(4)),
                default=Value(5),
                output_field=IntegerField(),
            )
        ).order_by("urgency_rank", "deadline")
