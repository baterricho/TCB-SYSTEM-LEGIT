"""
Application Service Layer.
Handles business logic for IP application lifecycle:
submission, evaluator assignment, and state transitions.
"""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from applications.models import IPApplication
from accounts.models import User
from core.exceptions import ApplicationNotSubmittable
from services.workflow_service import update_application_status
from services.notification_service import send_notification
from services.audit_service import log_audit


def submit_application(application, user):
    """
    Submit a draft application.
    Validates that the application is in Draft status and
    triggers the state machine transition to Submitted.
    """
    if application.status != "Draft":
        raise ApplicationNotSubmittable(
            "Only applications in 'Draft' status can be submitted."
        )

    # Validate minimum requirements
    if not application.title.strip():
        raise ApplicationNotSubmittable("Application title is required.")
    if not application.description.strip():
        raise ApplicationNotSubmittable("Application description is required.")

    # Transition via state machine
    update_application_status(
        application=application,
        user=user,
        new_status="Submitted",
        remarks="Application submitted for review.",
    )

    # Notify admins about new submission
    admin_users = User.objects.filter(role="admin", is_active=True)
    for admin in admin_users:
        send_notification(
            user=admin,
            message=f"New {application.ip_type} application submitted: '{application.title}' by {user.full_name}.",
        )


def assign_evaluator(application, evaluator_id, admin_user):
    """
    Assign an evaluator to an application.
    Only admins can assign evaluators. The application must be in 'Submitted' status.
    """
    if not evaluator_id:
        raise ValidationError({"evaluator_id": "Evaluator ID is required."})

    evaluator = get_object_or_404(User, pk=evaluator_id)

    if evaluator.role != "evaluator":
        raise ValidationError(
            {"evaluator_id": "Selected user is not an evaluator."}
        )

    application.assigned_evaluator = evaluator
    application.save()

    # Transition to Under Evaluation if currently Submitted
    if application.status == "Submitted":
        update_application_status(
            application=application,
            user=admin_user,
            new_status="Under Evaluation",
            remarks=f"Assigned to evaluator: {evaluator.full_name}.",
        )

    # Notify the evaluator
    send_notification(
        user=evaluator,
        message=f"You have been assigned to evaluate: '{application.title}' ({application.ip_type}).",
    )

    # Notify the applicant
    send_notification(
        user=application.created_by,
        message=f"Your application '{application.title}' has been assigned for review.",
    )

    log_audit(
        user=admin_user,
        action="ASSIGN_EVALUATOR",
        entity=f"IPApplication:{application.id}",
    )
