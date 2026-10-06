from django.db import transaction
from django.utils import timezone

from core.models import WorkflowHistory, WorkflowInstance
from core.services.audit import log_action
from core.services.workflow_action import execute_transition_actions
from core.services.workflow_condition import evaluate_transition_conditions


@transaction.atomic
def select_transition(*, instance):
    if instance.status != "active":
        return None

    transitions = (
        instance.workflow.transitions
        .filter(
            from_step=instance.current_step,
            is_active=True,
        )
        .order_by("created_at")
    )

    for transition in transitions:
        if evaluate_transition_conditions(
            transition,
            instance.record,
        ):
            return transition

    return None


@transaction.atomic
def advance_workflow(
    *,
    user,
    instance,
    ip_address=None,
):
    if instance.status != "active":
        return {
            "success": False,
            "completed": instance.status == "completed",
            "status": instance.status,
        }

    transition = select_transition(
        instance=instance,
    )

    if transition is None:
        return {
            "success": True,
            "transitioned": False,
            "waiting": True,
            "step_id": str(instance.current_step_id),
        }

    old_step = instance.current_step
    new_step = transition.to_step

    instance.current_step = new_step

    if new_step.is_final:
        instance.status = "completed"
        instance.completed_at = timezone.now()

    instance.save(
        update_fields=[
            "current_step",
            "status",
            "completed_at",
        ]
    )

    WorkflowHistory.objects.create(
        instance=instance,
        from_step=old_step,
        to_step=new_step,
        action="completed" if new_step.is_final else "transitioned",
        performed_by=user,
        note=transition.name,
    )

    log_action(
        business=instance.workflow.business,
        user=user,
        action="workflow.instance.transitioned",
        resource="workflow_instance",
        object_id=instance.pk,
        ip_address=ip_address,
        metadata={
            "transition_id": str(transition.pk),
            "from_step": str(old_step.pk),
            "to_step": str(new_step.pk),
        },
    )

    actions = execute_transition_actions(
        transition=transition,
        instance=instance,
        user=user,
        ip_address=ip_address,
    )

    return {
        "success": True,
        "transitioned": True,
        "completed": instance.status == "completed",
        "transition_id": str(transition.pk),
        "from_step": str(old_step.pk),
        "to_step": str(new_step.pk),
        "actions": actions,
    }


@transaction.atomic
def cancel_workflow(
    *,
    user,
    instance,
    reason="",
    ip_address=None,
):
    if instance.status != "active":
        raise ValueError(
            "Only active workflow instances can be cancelled."
        )

    instance.status = "cancelled"
    instance.completed_at = timezone.now()
    instance.save(
        update_fields=[
            "status",
            "completed_at",
        ]
    )

    WorkflowHistory.objects.create(
        instance=instance,
        from_step=instance.current_step,
        to_step=instance.current_step,
        action="cancelled",
        performed_by=user,
        note=(reason or "Workflow cancelled.").strip(),
    )

    log_action(
        business=instance.workflow.business,
        user=user,
        action="workflow.instance.cancelled",
        resource="workflow_instance",
        object_id=instance.pk,
        ip_address=ip_address,
        metadata={
            "reason": (reason or "").strip(),
            "step_id": str(instance.current_step_id),
        },
    )

    return instance


@transaction.atomic
def resume_workflow(
    *,
    user,
    instance,
    ip_address=None,
):
    if instance.status != "cancelled":
        raise ValueError(
            "Only cancelled workflow instances can be resumed."
        )

    instance.status = "active"
    instance.completed_at = None
    instance.save(
        update_fields=[
            "status",
            "completed_at",
        ]
    )

    WorkflowHistory.objects.create(
        instance=instance,
        from_step=instance.current_step,
        to_step=instance.current_step,
        action="resumed",
        performed_by=user,
        note="Workflow resumed.",
    )

    log_action(
        business=instance.workflow.business,
        user=user,
        action="workflow.instance.resumed",
        resource="workflow_instance",
        object_id=instance.pk,
        ip_address=ip_address,
        metadata={
            "step_id": str(instance.current_step_id),
        },
    )

    return instance
