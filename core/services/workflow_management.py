from django.db import transaction
from django.utils.text import slugify

from core.models import WorkflowDefinition
from core.services.audit import log_action
from core.services.permissions import get_membership, user_can


@transaction.atomic
def update_workflow(
    *,
    user,
    workflow,
    name=None,
    slug=None,
    description=None,
    ip_address=None,
):
    business = workflow.business

    if not get_membership(user, business):
        raise PermissionError("You are not an active member of this business.")

    if not user_can(user, business, "workflow.manage"):
        raise PermissionError("You do not have permission to update workflows.")

    old_data = {
        "name": workflow.name,
        "slug": workflow.slug,
        "description": workflow.description,
    }

    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("Workflow name is required.")
        workflow.name = name

    if slug is not None:
        slug = slugify(slug)
        if not slug:
            raise ValueError("A valid workflow slug is required.")

        duplicate = WorkflowDefinition.objects.filter(
            business=business,
            slug=slug,
        ).exclude(pk=workflow.pk).exists()

        if duplicate:
            raise ValueError(
                f"A workflow with slug '{slug}' already exists."
            )

        workflow.slug = slug

    if description is not None:
        workflow.description = description.strip()

    workflow.save(
        update_fields=[
            "name",
            "slug",
            "description",
            "updated_at",
        ]
    )

    log_action(
        business=business,
        user=user,
        action="workflow.updated",
        resource="workflow",
        object_id=workflow.pk,
        ip_address=ip_address,
        metadata={
            "old": old_data,
            "new": {
                "name": workflow.name,
                "slug": workflow.slug,
                "description": workflow.description,
            },
        },
    )

    return workflow


@transaction.atomic
def deactivate_workflow(
    *,
    user,
    workflow,
    ip_address=None,
):
    business = workflow.business

    if not get_membership(user, business):
        raise PermissionError("You are not an active member of this business.")

    if not user_can(user, business, "workflow.manage"):
        raise PermissionError(
            "You do not have permission to deactivate workflows."
        )

    if not workflow.is_active:
        raise ValueError("Workflow is already inactive.")

    workflow.is_active = False
    workflow.save(update_fields=["is_active", "updated_at"])

    log_action(
        business=business,
        user=user,
        action="workflow.deactivated",
        resource="workflow",
        object_id=workflow.pk,
        ip_address=ip_address,
        metadata={
            "name": workflow.name,
            "slug": workflow.slug,
        },
    )

    return workflow


@transaction.atomic
def delete_workflow(
    *,
    user,
    workflow,
    ip_address=None,
):
    business = workflow.business

    if not get_membership(user, business):
        raise PermissionError("You are not an active member of this business.")

    if not user_can(user, business, "workflow.delete"):
        raise PermissionError("You do not have permission to delete workflows.")

    if workflow.instances.exists():
        raise ValueError(
            "Workflow cannot be deleted while workflow instances exist."
        )

    log_action(
        business=business,
        user=user,
        action="workflow.deleted",
        resource="workflow",
        object_id=workflow.pk,
        ip_address=ip_address,
        metadata={
            "name": workflow.name,
            "slug": workflow.slug,
        },
    )

    workflow.delete()
    return True
