def create_notification(recipient, title, message, notification_type="", related_case=None, role_visibility=""):
    if not recipient:
        return None
    from notifications.models import Notification

    return Notification.objects.create(
        recipient=recipient,
        role_visibility=role_visibility or getattr(recipient, "role", ""),
        title=title,
        content=message,
        notification_type=notification_type,
        related_case=related_case,
    )
