"""
Notification Service Layer.
Centralized notification creation.
Two-layer: DB notification (immediate) + Email (future async via Celery).
"""

from workflow.models import Notification


def send_notification(user, message, notification_type="system"):
    """
    Create a notification for a user.

    Args:
        user: User instance to notify
        message: Notification message text
        notification_type: 'system' or 'email'

    Returns:
        Notification instance created
    """
    notification = Notification.objects.create(
        user=user,
        message=message,
        notification_type=notification_type,
    )

    # TODO: Integrate Celery for async email notifications
    # if notification_type == "email":
    #     send_email_notification.delay(user.email, message)

    return notification


def send_bulk_notification(users, message, notification_type="system"):
    """
    Send the same notification to multiple users.

    Args:
        users: QuerySet or list of User instances
        message: Notification message text
        notification_type: 'system' or 'email'

    Returns:
        List of Notification instances created
    """
    notifications = [
        Notification(
            user=user,
            message=message,
            notification_type=notification_type,
        )
        for user in users
    ]
    return Notification.objects.bulk_create(notifications)
