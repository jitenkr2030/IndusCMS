from django.db import transaction

from core.models import WorkflowCondition
from core.services.audit import log_action
from core.services.permissions import get_membership, user_can

VALID_OPERATORS = {
    "equals",
    "not_equals",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "contains",
    "is_true",
    "is_false",
}


def _check_access(*, user, condition):
    business = condition.transition.workflow.business

    if not get_membership(user, business):
        raise PermissionError("You are not an active member of this business.")

    if not user_can(user, business, "workflow.manage"):
        raise PermissionError(
            "You do not have permission to manage workflow conditions."
        )

    if not condition.transition.workflow.is_active:
        raise ValueError("Workflow is inactive.")

    if not condition.transition.is_active:
        raise ValueError("Transition is inactive.")

    return business


@transaction.atomic
def update_workflow_condition(
    *,
    user,
    condition,
    field_slug=None,
    operator=None,
    value=None,
    ip_address=None,
):
    business = _check_access(user=user, condition=condition)

    old = {
        "field_slug": condition.field_slug,
        "operator": condition.operator,
        "value": condition.value,
    }

    if field_slug is not None:
        field_slug = str(field_slug).strip()
        if not field_slug:
            raise ValueError("field_slug is required.")
        condition.field_slug = field_slug

    if operator is not None:
        if operator not in VALID_OPERATORS:
            raise ValueError("Invalid condition operator.")
        condition.operator = operator

    if value is not None:
        condition.value = value

    condition.save(update_fields=[
        "field_slug", "operator", "value", "updated_at"
    ])

    log_action(
        business=business,
        user=user,
        action="workflow.condition.updated",
        resource="workflow_condition",
        object_id=condition.pk,
        ip_address=ip_address,
        metadata={
            "old": old,
            "new": {
                "field_slug": condition.field_slug,
                "operator": condition.operator,
                "value": condition.value,
            },
        },
    )
    return condition


@transaction.atomic
def deactivate_workflow_condition(*, user, condition, ip_address=None):
    business = _check_access(user=user, condition=condition)

    if not condition.is_active:
        raise ValueError("Condition is already inactive.")

    condition.is_active = False
    condition.save(update_fields=["is_active", "updated_at"])

    log_action(
        business=business,
        user=user,
        action="workflow.condition.deactivated",
        resource="workflow_condition",
        object_id=condition.pk,
        ip_address=ip_address,
        metadata={"field_slug": condition.field_slug},
    )
    return condition


@transaction.atomic
def delete_workflow_condition(*, user, condition, ip_address=None):
    business = _check_access(user=user, condition=condition)

    log_action(
        business=business,
        user=user,
        action="workflow.condition.deleted",
        resource="workflow_condition",
        object_id=condition.pk,
        ip_address=ip_address,
        metadata={
            "field_slug": condition.field_slug,
            "operator": condition.operator,
        },
    )

    condition.delete()
    return True
