from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from core.models import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTransition,
    WorkflowInstance,
    WorkflowHistory,
)
from core.services.audit import log_action
from core.services.permissions import get_membership, user_can
from core.services.workflow_condition import evaluate_transition_conditions
from core.services.workflow_action import execute_transition_actions



@transaction.atomic
def create_workflow(
    *,
    user,
    business,
    entity,
    name,
    slug="",
    description="",
    ip_address=None,
):
    if not user or not user.is_authenticated:
        raise ValueError("Authenticated user is required.")

    if entity.business_id != business.id:
        raise ValueError("Entity must belong to the selected business.")

    if not entity.is_active:
        raise ValueError("Entity must be active.")

    if not get_membership(user, business):
        raise PermissionError("You are not an active member of this business.")

    if not user_can(user, business, "workflow.create"):
        raise PermissionError(
            "You do not have permission to create workflows."
        )

    name = (name or "").strip()
    if not name:
        raise ValueError("Workflow name is required.")

    slug = slugify(slug or name)
    if not slug:
        raise ValueError("A valid workflow slug is required.")

    if WorkflowDefinition.objects.filter(
        business=business,
        slug=slug,
    ).exists():
        raise ValueError(
            f"A workflow with slug '{slug}' already exists."
        )

    workflow = WorkflowDefinition.objects.create(
        business=business,
        entity=entity,
        name=name,
        slug=slug,
        description=(description or "").strip(),
    )

    log_action(
        business=business,
        user=user,
        action="workflow.created",
        resource="workflow",
        object_id=workflow.pk,
        ip_address=ip_address,
        metadata={
            "name": workflow.name,
            "slug": workflow.slug,
            "entity_id": str(entity.pk),
        },
    )

    return workflow


@transaction.atomic
def create_workflow_step(
    *,
    user,
    workflow,
    name,
    slug="",
    description="",
    position=0,
    is_initial=False,
    is_final=False,
    ip_address=None,
):
    business = workflow.business

    if not get_membership(user, business):
        raise PermissionError("You are not an active member of this business.")

    if not user_can(user, business, "workflow.manage"):
        raise PermissionError(
            "You do not have permission to manage workflows."
        )

    if not workflow.is_active:
        raise ValueError("Workflow is inactive.")

    name = (name or "").strip()
    if not name:
        raise ValueError("Step name is required.")

    slug = slugify(slug or name)

    if WorkflowStep.objects.filter(
        workflow=workflow,
        slug=slug,
    ).exists():
        raise ValueError(
            f"A step with slug '{slug}' already exists."
        )

    if is_initial and WorkflowStep.objects.filter(
        workflow=workflow,
        is_initial=True,
        is_active=True,
    ).exists():
        raise ValueError(
            "Workflow already has an initial step."
        )

    step = WorkflowStep.objects.create(
        workflow=workflow,
        name=name,
        slug=slug,
        description=(description or "").strip(),
        position=position,
        is_initial=is_initial,
        is_final=is_final,
    )

    log_action(
        business=business,
        user=user,
        action="workflow.step.created",
        resource="workflow_step",
        object_id=step.pk,
        ip_address=ip_address,
        metadata={
            "workflow_id": str(workflow.pk),
            "name": step.name,
            "slug": step.slug,
        },
    )

    return step


@transaction.atomic
def create_workflow_transition(
    *,
    user,
    workflow,
    from_step,
    to_step,
    name,
    slug="",
    ip_address=None,
):
    business = workflow.business

    if from_step.workflow_id != workflow.id:
        raise ValueError("Source step does not belong to workflow.")

    if to_step.workflow_id != workflow.id:
        raise ValueError("Target step does not belong to workflow.")

    if not get_membership(user, business):
        raise PermissionError("You are not an active member of this business.")

    if not user_can(user, business, "workflow.manage"):
        raise PermissionError(
            "You do not have permission to manage workflows."
        )

    name = (name or "").strip()
    if not name:
        raise ValueError("Transition name is required.")

    slug = slugify(slug or name)

    if WorkflowTransition.objects.filter(
        workflow=workflow,
        slug=slug,
    ).exists():
        raise ValueError(
            f"A transition with slug '{slug}' already exists."
        )

    transition = WorkflowTransition.objects.create(
        workflow=workflow,
        from_step=from_step,
        to_step=to_step,
        name=name,
        slug=slug,
    )

    log_action(
        business=business,
        user=user,
        action="workflow.transition.created",
        resource="workflow_transition",
        object_id=transition.pk,
        ip_address=ip_address,
        metadata={
            "workflow_id": str(workflow.pk),
            "from_step": str(from_step.pk),
            "to_step": str(to_step.pk),
            "name": transition.name,
        },
    )

    return transition


@transaction.atomic
def start_workflow_instance(
    *,
    user,
    workflow,
    record,
    ip_address=None,
):
    business = workflow.business

    if record.entity_id != workflow.entity_id:
        raise ValueError(
            "Record does not belong to the workflow entity."
        )

    if record.is_deleted:
        raise ValueError("Cannot start workflow for deleted record.")

    if not workflow.is_active:
        raise ValueError("Workflow is inactive.")

    if not get_membership(user, business):
        raise PermissionError("You are not an active member of this business.")

    if not user_can(user, business, "workflow.create"):
        raise PermissionError(
            "You do not have permission to start workflows."
        )

    if WorkflowInstance.objects.filter(
        workflow=workflow,
        record=record,
    ).exists():
        raise ValueError(
            "A workflow instance already exists for this record."
        )

    initial_step = workflow.steps.filter(
        is_active=True,
        is_initial=True,
    ).first()

    if not initial_step:
        raise ValueError(
            "Workflow does not have an active initial step."
        )

    instance = WorkflowInstance.objects.create(
        workflow=workflow,
        record=record,
        current_step=initial_step,
        started_by=user,
        status="completed" if initial_step.is_final else "active",
        completed_at=timezone.now() if initial_step.is_final else None,
    )

    WorkflowHistory.objects.create(
        instance=instance,
        from_step=None,
        to_step=initial_step,
        action="completed" if initial_step.is_final else "started",
        performed_by=user,
        note="Workflow started.",
    )

    log_action(
        business=business,
        user=user,
        action="workflow.instance.started",
        resource="workflow_instance",
        object_id=instance.pk,
        ip_address=ip_address,
        metadata={
            "workflow_id": str(workflow.pk),
            "record_id": str(record.pk),
            "step_id": str(initial_step.pk),
        },
    )

    return instance


@transaction.atomic
def transition_workflow_instance(
    *,
    user,
    instance,
    transition,
    ip_address=None,
):
    business = instance.workflow.business

    if not get_membership(user, business):
        raise PermissionError("You are not an active member of this business.")

    if not user_can(user, business, "workflow.update"):
        raise PermissionError(
            "You do not have permission to transition workflows."
        )

    if instance.status != "active":
        raise ValueError("Workflow instance is not active.")

    if transition.workflow_id != instance.workflow_id:
        raise ValueError("Transition does not belong to this workflow.")

    if transition.from_step_id != instance.current_step_id:
        raise ValueError(
            "Transition is not valid for the current workflow step."
        )

    if not transition.is_active:
        raise ValueError("Transition is inactive.")

    if not evaluate_transition_conditions(
        transition,
        instance.record,
    ):
        raise ValueError(
            "Workflow transition conditions are not satisfied."
        )

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
            "updated_at",
        ]
    )

    WorkflowHistory.objects.create(
        instance=instance,
        transition=transition,
        from_step=old_step,
        to_step=new_step,
        action="completed" if new_step.is_final else "transitioned",
        performed_by=user,
        note=f"Transition: {transition.name}",
    )

    execute_transition_actions(
        transition=transition,
        instance=instance,
        user=user,
        ip_address=ip_address,
    )

    log_action(
        business=business,
        user=user,
        action="workflow.instance.transitioned",
        resource="workflow_instance",
        object_id=instance.pk,
        ip_address=ip_address,
        metadata={
            "transition_id": str(transition.pk),
            "from_step_id": str(old_step.pk),
            "to_step_id": str(new_step.pk),
            "status": instance.status,
        },
    )

    return instance
