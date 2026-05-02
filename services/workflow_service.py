"""
Workflow Service Layer.
Central brain of the system — enforces the strict status state machine.
Every status transition passes through here.

Updated per capstone document to include the full two-stage lifecycle:
  IPTTO Stage:  Draft -> Submitted -> Under Evaluation -> Deficient -> Submitted | Certified
  IPOPHL Stage: Certified -> Forwarded to IPOPHL -> IPOPHL Under Review
                -> IPOPHL Deficient -> IPOPHL Under Review | Registered
"""

from core.exceptions import InvalidStatusTransition
from services.notification_service import send_notification
from services.audit_service import log_audit

# ======================================================================
# STRICT STATUS STATE MACHINE
# Never allow free status updates. Only these transitions are valid.
# ======================================================================
ALLOWED_TRANSITIONS = {
    # ── IPTTO Stage ────────────────────────────────────────────────────
    "Draft": ["Submitted"],
    "Submitted": ["Under Evaluation", "Under Review"],
    "Under Evaluation": ["Deficient", "Certified"],
    "Under Review": ["Deficient", "Certified"],  # Legacy label retained for old rows.
    "Deficient": ["Submitted"],          # Applicant resubmits after fixing
    # ── Transition to IPOPHL Stage ─────────────────────────────────────
    "Certified": ["Forwarded to IPOPHL"],
    # ── IPOPHL Stage ───────────────────────────────────────────────────
    "Forwarded to IPOPHL": ["IPOPHL Under Review"],
    "IPOPHL Under Review": ["IPOPHL Deficient", "Registered"],
    "IPOPHL Deficient": ["IPOPHL Under Review"],  # Applicant corrects and IPTTO resubmits
    "Registered": [],                    # Terminal state — IP is nationally registered
}

# Statuses that belong to the IPOPHL processing stage
IPOPHL_STAGE_STATUSES = {
    "Forwarded to IPOPHL",
    "IPOPHL Under Review",
    "IPOPHL Deficient",
    "Registered",
}


def update_application_status(application, user, new_status, remarks=""):
    """
    Central function for updating application status.
    This is the CORE SYSTEM BRAIN.

    Every call:
    1. Validates the transition against the state machine
    2. Updates the application status (and stage if crossing IPTTO→IPOPHL)
    3. Creates an immutable status log entry
    4. Sends a notification to the applicant
    5. Logs the action in the audit trail

    Args:
        application: IPApplication instance
        user: User performing the update
        new_status: Target status string
        remarks: Optional remarks text
    """
    current_status = application.status
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])

    if new_status not in allowed:
        raise InvalidStatusTransition(
            f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {allowed or 'None (terminal state)'}."
        )

    # 1. Update status
    application.status = new_status

    # 2. Auto-update the stage field when crossing into IPOPHL territory
    if new_status in IPOPHL_STAGE_STATUSES:
        application.stage = "IPOPHL"
    else:
        application.stage = "IPTTO"

    application.save()

    # 3. Create immutable status log
    _create_status_log(application, user, new_status, remarks)

    # 4. Notify the applicant
    _notify_status_change(application, new_status, remarks)

    # 5. Audit trail
    log_audit(
        user=user,
        action="UPDATE_STATUS",
        entity=f"IPApplication:{application.id} → {new_status}",
    )


def _create_status_log(application, user, status, remarks):
    """Create an immutable status log entry."""
    from workflow.models import ApplicationStatusLog

    ApplicationStatusLog.objects.create(
        application=application,
        status=status,
        remarks=remarks,
        updated_by=user,
    )


def _notify_status_change(application, new_status, remarks):
    """Send notification to the applicant about status change."""
    message = (
        f"Your application '{application.title}' status has been updated to: {new_status}."
    )
    if remarks:
        message += f" Remarks: {remarks}"

    send_notification(user=application.created_by, message=message)

    # Additional targeted notifications for key transitions
    if new_status == "Deficient":
        send_notification(
            user=application.created_by,
            message=(
                f"Action required: Your application '{application.title}' has deficiencies "
                f"at the IPTTO evaluation stage. Please review remarks and resubmit."
            ),
        )
    elif new_status == "Certified":
        send_notification(
            user=application.created_by,
            message=(
                f"Your application '{application.title}' has been certified by IPTTO. "
                f"It will now be forwarded to IPOPHL for national registration."
            ),
        )
    elif new_status == "Forwarded to IPOPHL":
        send_notification(
            user=application.created_by,
            message=(
                f"Your application '{application.title}' has been officially forwarded "
                f"to the Intellectual Property Office of the Philippines (IPOPHL)."
            ),
        )
    elif new_status == "IPOPHL Deficient":
        send_notification(
            user=application.created_by,
            message=(
                f"IPOPHL has issued a deficiency notice for '{application.title}'. "
                f"The IPTTO will contact you with the required corrections."
            ),
        )
    elif new_status == "Registered":
        send_notification(
            user=application.created_by,
            message=(
                f"Congratulations! Your application '{application.title}' has been "
                f"officially REGISTERED by IPOPHL. Your IP is now nationally protected!"
            ),
        )
