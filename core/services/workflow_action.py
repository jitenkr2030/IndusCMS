
from core.models import WorkflowAction
from core.services.audit import log_action


VALID_ACTION_TYPES = {
    "audit",
    "notification",
    "webhook",
    "update_record",
}


def execute_workflow_action(
    *,
    action,
    instance,
    user=None,
    ip_address=None,
):
    if not action.is_active:
        return {
            "success": True,
            "skipped": True,
            "reason": "Action is inactive.",
        }

    record = instance.record
    business = instance.workflow.business
    config = action.config or {}

    if action.action_type == "audit":
        audit_action = config.get(
            "action",
            "workflow.action.executed",
        )

        log_action(
            business=business,
            user=user,
            action=audit_action,
            resource="workflow_action",
            object_id=action.pk,
            ip_address=ip_address,
            metadata={
                "workflow_instance_id": str(instance.pk),
                "record_id": str(record.pk),
                "action_id": str(action.pk),
                "message": config.get(
                    "message",
                    action.name,
                ),
            },
        )

        return {
            "success": True,
            "action": "audit",
        }

    if action.action_type == "notification":
        message = config.get(
            "message",
            action.name,
        )

        log_action(
            business=business,
            user=user,
            action="workflow.notification.triggered",
            resource="workflow_action",
            object_id=action.pk,
            ip_address=ip_address,
            metadata={
                "workflow_instance_id": str(instance.pk),
                "record_id": str(record.pk),
                "recipient": config.get("recipient", ""),
                "message": message,
                "channel": config.get("channel", "in_app"),
            },
        )

        return {
            "success": True,
            "action": "notification",
        }

    if action.action_type == "update_record":
        field_slug = config.get("field_slug")
        value = config.get("value")

        if not field_slug:
            raise ValueError(
                "update_record action requires field_slug."
            )

        record.data[field_slug] = value
        record.save(update_fields=["data", "updated_at"])

        log_action(
            business=business,
            user=user,
            action="workflow.record.updated",
            resource="entity_record",
            object_id=record.pk,
            ip_address=ip_address,
            metadata={
                "workflow_instance_id": str(instance.pk),
                "action_id": str(action.pk),
                "field_slug": field_slug,
                "value": value,
            },
        )

        return {
            "success": True,
            "action": "update_record",
            "field_slug": field_slug,
        }

    if action.action_type == "webhook":
        # Provider-independent webhook foundation.
        # URL delivery is intentionally deferred to the external
        # integration layer so workflow execution remains reliable.
        url = config.get("url", "")

        log_action(
            business=business,
            user=user,
            action="workflow.webhook.triggered",
            resource="workflow_action",
            object_id=action.pk,
            ip_address=ip_address,
            metadata={
                "workflow_instance_id": str(instance.pk),
                "record_id": str(record.pk),
                "url": url,
                "method": config.get("method", "POST"),
                "payload": config.get(
                    "payload",
                    {
                        "record_id": str(record.pk),
                        "workflow_instance_id": str(instance.pk),
                    },
                ),
            },
        )

        return {
            "success": True,
            "action": "webhook",
            "queued": False,
        }

    raise ValueError("Invalid workflow action type.")


def execute_transition_actions(
    *,
    transition,
    instance,
    user=None,
    ip_address=None,
):
    results = []

    actions = transition.actions.filter(
        is_active=True,
    ).order_by(
        "position",
        "created_at",
    )

    for action in actions:
        results.append(
            execute_workflow_action(
                action=action,
                instance=instance,
                user=user,
                ip_address=ip_address,
            )
        )

    return results
