from django.db import transaction
from django.utils.text import slugify

from core.models import EntityDefinition
from core.services.audit import log_action
from core.services.permissions import user_can, get_membership


@transaction.atomic
def create_entity_for_business(
    *,
    user,
    business,
    name,
    slug="",
    description="",
    is_active=True,
    ip_address=None,
):
    """
    Create a dynamic entity for a business.

    Security:
    - User must be authenticated.
    - User must have an active membership in the business.
    - User must have entity.create permission.
    """

    if not user or not user.is_authenticated:
        raise ValueError("Authenticated user is required.")

    membership = get_membership(user, business)

    if not membership:
        raise PermissionError(
            "You are not an active member of this business."
        )

    if not user_can(user, business, "entity.create"):
        raise PermissionError(
            "You do not have permission to create entities."
        )

    name = (name or "").strip()

    if not name:
        raise ValueError("Entity name is required.")

    description = (description or "").strip()

    if slug:
        slug = slugify(slug)
    else:
        slug = slugify(name)

    if not slug:
        raise ValueError("A valid entity slug could not be generated.")

    if EntityDefinition.objects.filter(
        business=business,
        slug=slug,
    ).exists():
        raise ValueError(
            f"An entity with slug '{slug}' already exists in this business."
        )

    entity = EntityDefinition.objects.create(
        business=business,
        name=name,
        slug=slug,
        description=description,
        is_active=is_active,
    )

    log_action(
        business=business,
        user=user,
        action="entity.created",
        resource="entity",
        object_id=entity.pk,
        ip_address=ip_address,
        metadata={
            "name": entity.name,
            "slug": entity.slug,
        },
    )

    return entity


@transaction.atomic
def update_entity_for_business(
    *,
    user,
    entity,
    name=None,
    slug=None,
    description=None,
    ip_address=None,
):
    """
    Update an existing dynamic entity.

    Security:
    - User must be authenticated.
    - User must have an active membership in the business.
    - User must have entity.manage permission.
    """

    if not user or not user.is_authenticated:
        raise ValueError("Authenticated user is required.")

    business = entity.business

    membership = get_membership(
        user,
        business,
    )

    if not membership:
        raise PermissionError(
            "You are not an active member of this business."
        )

    if not user_can(
        user,
        business,
        "entity.manage",
    ):
        raise PermissionError(
            "You do not have permission to update entities."
        )

    old_data = {
        "name": entity.name,
        "slug": entity.slug,
        "description": entity.description,
    }

    if name is not None:
        name = name.strip()

        if not name:
            raise ValueError(
                "Entity name is required."
            )

        entity.name = name

    if slug is not None:
        slug = slugify(slug)

        if not slug:
            raise ValueError(
                "A valid entity slug is required."
            )

        duplicate_exists = EntityDefinition.objects.filter(
            business=business,
            slug=slug,
        ).exclude(
            id=entity.id,
        ).exists()

        if duplicate_exists:
            raise ValueError(
                f"An entity with slug '{slug}' already exists in this business."
            )

        entity.slug = slug

    if description is not None:
        entity.description = description.strip()

    entity.save(
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
        action="entity.updated",
        resource="entity",
        object_id=entity.pk,
        ip_address=ip_address,
        metadata={
            "old_data": old_data,
            "new_data": {
                "name": entity.name,
                "slug": entity.slug,
                "description": entity.description,
            },
        },
    )

    return entity


@transaction.atomic
def deactivate_entity_for_business(
    *,
    user,
    entity,
    ip_address=None,
):
    """
    Deactivate an existing dynamic entity.

    Deactivation does not delete the entity or its records.
    """

    if not user or not user.is_authenticated:
        raise ValueError("Authenticated user is required.")

    business = entity.business

    membership = get_membership(
        user,
        business,
    )

    if not membership:
        raise PermissionError(
            "You are not an active member of this business."
        )

    if not user_can(
        user,
        business,
        "entity.manage",
    ):
        raise PermissionError(
            "You do not have permission to deactivate entities."
        )

    if not entity.is_active:
        raise ValueError(
            "Entity is already inactive."
        )

    entity.is_active = False

    entity.save(
        update_fields=[
            "is_active",
            "updated_at",
        ]
    )

    log_action(
        business=business,
        user=user,
        action="entity.deactivated",
        resource="entity",
        object_id=entity.pk,
        ip_address=ip_address,
        metadata={
            "name": entity.name,
            "slug": entity.slug,
        },
    )

    return entity


@transaction.atomic
def delete_entity_for_business(
    *,
    user,
    entity,
    ip_address=None,
):
    if not user or not user.is_authenticated:
        raise ValueError("Authenticated user is required.")

    business = entity.business

    membership = get_membership(user, business)

    if not membership:
        raise PermissionError(
            "You are not an active member of this business."
        )

    if not user_can(user, business, "entity.manage"):
        raise PermissionError(
            "You do not have permission to delete entities."
        )

    if entity.records.filter(is_deleted=False).exists():
        raise ValueError(
            "Entity cannot be deleted while active records exist."
        )

    log_action(
        business=business,
        user=user,
        action="entity.deleted",
        resource="entity",
        object_id=entity.pk,
        ip_address=ip_address,
        metadata={
            "name": entity.name,
            "slug": entity.slug,
        },
    )

    entity.delete()

    return True
