from django.db import transaction

from core.models import WorkflowAction
from core.services.audit import log_action
from core.services.permissions import get_membership, user_can

VALID_ACTION_TYPES = {
    "audit",
    "notification",
    "webhook",
    "update_record",
}


def _check_access(*, user, action):
    business = action.transition.workflow.business

    if not get_membership(user, business):
        raise PermissionError("You are not an active member of this business.")

    if not user_can(user, business, "workflow.manage"):
        raise PermissionError(
            "You do not have permission to manage workflow actions."
        )

    if not action.transition.workflow.is_active:
        raise ValueError("Workflow is inactive.")

    if not action.transition.is_active:
        raise ValueError("Transition is inactive.")

    return business


@transaction.atomic
def update_workflow_action(
    *,
    user,
    action,
    name=None,
    action_type=None,
    config=None,
    position=None,
    ip_address=None,
):
    business = _check_access(user=user, action=action)

    old = {
        "name": action.name,
        "action_type": action.action_type,
        "config": action.config,
        "position": action.position,
    }

    if name is not None:
        name = str(name).strip()
        if not name:
            raise ValueError("name is required.")
        action.name = name

    if action_type is not None:
        if action_type not in VALID_ACTION_TYPES:
            raise ValueError("Invalid workflow action type.")
        action.action_type = action_type

    if config is not None:
        if not isinstance(config, dict):
            raise ValueError("config must be a JSON object.")
        action.config = config

    if position is not None:
        try:
            position = int(position)
        except (TypeError, ValueError):
            raise ValueError("position must be a non-negative integer.")
        if position < 0:
            raise ValueError("position must be a non-negative integer.")
        action.position = position

    action.save(update_fields=[
        "name", "action_type", "config", "position", "updated_at"
    ])

    log_action(
        business=business,
        user=user,
        action="workflow.action.updated",
        resource="workflow_action",
        object_id=action.pk,
        ip_address=ip_address,
        metadata={
            "old": old,
            "new": {
                "name": action.name,
                "action_type": action.action_type,
                "config": action.config,
                "position": action.position,
            },
        },
    )
    return action


@transaction.atomic
def deactivate_workflow_action(*, user, action, ip_address=None):
    business = _check_access(user=user, action=action)

    if not action.is_active:
        raise ValueError("Action is already inactive.")

    action.is_active = False
    action.save(update_fields=["is_active", "updated_at"])

    log_action(
        business=business,
        user=user,
        action="workflow.action.deactivated",
        resource="workflow_action",
        object_id=action.pk,
        ip_address=ip_address,
        metadata={"name": action.name},
    )
    return action


@transaction.atomic
def delete_workflow_action(*, user, action, ip_address=None):
    business = _check_access(user=user, action=action)

    log_action(
        business=business,
        user=user,
        action="workflow.action.deleted",
        resource="workflow_action",
        object_id=action.pk,
        ip_address=ip_address,
        metadata={"name": action.name},
    )

    action.delete()
    return True


@transaction.atomic
def reorder_workflow_action(
    *,
    user,
    action,
    position,
    ip_address=None,
):
    business = _check_access(user=user, action=action)

    try:
        position = int(position)
    except (TypeError, ValueError):
        raise ValueError("position must be a non-negative integer.")

    if position < 0:
        raise ValueError("position must be a non-negative integer.")

    old_position = action.position
    action.position = position
    action.save(update_fields=["position", "updated_at"])

    log_action(
        business=business,
        user=user,
        action="workflow.action.reordered",
        resource="workflow_action",
        object_id=action.pk,
        ip_address=ip_address,
        metadata={
            "old_position": old_position,
            "new_position": position,
        },
    )
    return action
