from django.conf import settings

def get_client_ip(request):
    if not request:
        return ""
    remote_addr = request.META.get("REMOTE_ADDR", "")
    trusted_proxies = getattr(settings, "TRUSTED_PROXY_IPS", [])
    if remote_addr in trusted_proxies:
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    return remote_addr


def create_audit_log(request=None, user=None, action="", record="", details="", related_case=None, target=""):
    from auditlog.models import AuditLog

    actor = user or getattr(request, "user", None)
    if actor is not None and not getattr(actor, "is_authenticated", False):
        actor = None

    return AuditLog.objects.create(
        user=actor,
        account_name=actor.get_full_name() if actor else "",
        role=getattr(actor, "role", "") if actor else "",
        action=action,
        target=target or action.split(".")[0],
        record_id=str(record or ""),
        related_case=related_case,
        details=details,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
    )
