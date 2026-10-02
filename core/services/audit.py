from core.models import AuditLog


def log_action(
    *,
    business,
    action,
    resource,
    user=None,
    object_id="",
    ip_address=None,
    metadata=None,
):
    """
    Create an append-only audit event for a business.
    Do not pass passwords, tokens, or sensitive personal data.
    """
    return AuditLog.objects.create(
        business=business,
        user=user,
        action=action,
        resource=resource,
        object_id=str(object_id) if object_id else "",
        ip_address=ip_address,
        metadata=metadata or {},
    )
