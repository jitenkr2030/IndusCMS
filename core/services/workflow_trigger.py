
from django.db import transaction

from core.models import WorkflowTrigger
from core.services.audit import log_action
from core.services.permissions import get_membership, user_can

VALID_EVENT_TYPES = {
    "record_created",
    "record_updated",
    "record_deleted",
}


def _check_workflow_access(*, user, workflow, permission="workflow.manage"):
    business = workflow.business

    if not get_membership(user, business):
        raise PermissionError(
            "You are not an active member of this business."
        )

    if not user_can(user, business, permission):
        raise PermissionError(
            f"You do not have permission to access workflow triggers."
        )

    if not workflow.is_active:
        raise ValueError("Workflow is inactive.")

    return business


@transaction.atomic
def create_workflow_trigger(
    *,
    user,
    workflow,
    name,
    event_type,
    config=None,
    ip_address=None,
):
    business = _check_workflow_access(
        user=user,
        workflow=workflow,
    )

    name = str(name or "").strip()

    if not name:
        raise ValueError("Trigger name is required.")

    if event_type not in VALID_EVENT_TYPES:
        raise ValueError("Invalid trigger event type.")

    if config is None:
        config = {}

    if not isinstance(config, dict):
        raise ValueError("config must be a JSON object.")

    trigger = WorkflowTrigger.objects.create(
        workflow=workflow,
        name=name,
        event_type=event_type,
        config=config,
    )

    log_action(
        business=business,
        user=user,
        action="workflow.trigger.created",
        resource="workflow_trigger",
        object_id=trigger.pk,
        ip_address=ip_address,
        metadata={
            "workflow_id": str(workflow.pk),
            "name": name,
            "event_type": event_type,
        },
    )

    return trigger


@transaction.atomic
def update_workflow_trigger(
    *,
    user,
    trigger,
    name=None,
    event_type=None,
    config=None,
    ip_address=None,
):
    workflow = trigger.workflow
    business = _check_workflow_access(
        user=user,
        workflow=workflow,
    )

    old = {
        "name": trigger.name,
        "event_type": trigger.event_type,
        "config": trigger.config,
    }

    if name is not None:
        name = str(name).strip()

        if not name:
            raise ValueError("Trigger name is required.")

        trigger.name = name

    if event_type is not None:
        if event_type not in VALID_EVENT_TYPES:
            raise ValueError("Invalid trigger event type.")

        trigger.event_type = event_type

    if config is not None:
        if not isinstance(config, dict):
            raise ValueError("config must be a JSON object.")

        trigger.config = config

    trigger.save(
        update_fields=[
            "name",
            "event_type",
            "config",
            "updated_at",
        ]
    )

    log_action(
        business=business,
        user=user,
        action="workflow.trigger.updated",
        resource="workflow_trigger",
        object_id=trigger.pk,
        ip_address=ip_address,
        metadata={
            "old": old,
            "new": {
                "name": trigger.name,
                "event_type": trigger.event_type,
                "config": trigger.config,
            },
        },
    )

    return trigger


@transaction.atomic
def deactivate_workflow_trigger(
    *,
    user,
    trigger,
    ip_address=None,
):
    workflow = trigger.workflow
    business = _check_workflow_access(
        user=user,
        workflow=workflow,
    )

    if not trigger.is_active:
        raise ValueError("Trigger is already inactive.")

    trigger.is_active = False
    trigger.save(update_fields=["is_active", "updated_at"])

    log_action(
        business=business,
        user=user,
        action="workflow.trigger.deactivated",
        resource="workflow_trigger",
        object_id=trigger.pk,
        ip_address=ip_address,
        metadata={
            "name": trigger.name,
            "event_type": trigger.event_type,
        },
    )

    return trigger


@transaction.atomic
def delete_workflow_trigger(
    *,
    user,
    trigger,
    ip_address=None,
):
    workflow = trigger.workflow
    business = _check_workflow_access(
        user=user,
        workflow=workflow,
    )

    log_action(
        business=business,
        user=user,
        action="workflow.trigger.deleted",
        resource="workflow_trigger",
        object_id=trigger.pk,
        ip_address=ip_address,
        metadata={
            "name": trigger.name,
            "event_type": trigger.event_type,
        },
    )

    trigger.delete()

    return True
