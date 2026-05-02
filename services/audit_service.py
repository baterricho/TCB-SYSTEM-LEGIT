"""
Audit Service Layer.
Centralized audit logging for full traceability.
Tracks: login, status updates, file uploads, deletions, and all critical actions.
"""


def log_audit(user, action, entity):
    """
    Create an audit log entry.

    Args:
        user: User instance who performed the action (can be None for system actions)
        action: Action string (e.g., 'LOGIN', 'UPDATE_STATUS', 'UPLOAD_DOCUMENT')
        entity: Entity description (e.g., 'IPApplication:<uuid>')
    """
    from security.models import AuditLog

    AuditLog.objects.create(
        user=user,
        action=action,
        entity=entity,
    )
