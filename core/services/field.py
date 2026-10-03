from django.db import transaction
from django.utils.text import slugify

from core.models import FieldDefinition
from core.services.audit import log_action
from core.services.permissions import get_membership, user_can


@transaction.atomic
def create_field_for_entity(
    *,
    user,
    entity,
    name,
    field_type="text",
    slug="",
    required=False,
    unique=False,
    default_value=None,
    choices=None,
    position=0,
    is_active=True,
    is_system=False,
    ip_address=None,
):
    """
    Create a dynamic field for an entity.

    Security:
    - User must be authenticated.
    - User must be an active member of the entity's business.
    - User must have entity.manage permission.
    """

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
            "You do not have permission to manage entity fields."
        )

    name = (name or "").strip()

    if not name:
        raise ValueError("Field name is required.")

    slug = slugify(slug or name)

    if not slug:
        raise ValueError(
            "A valid field slug could not be generated."
        )

    if FieldDefinition.objects.filter(
        entity=entity,
        slug=slug,
    ).exists():
        raise ValueError(
            f"A field with slug '{slug}' already exists in this entity."
        )

    field = FieldDefinition.objects.create(
        entity=entity,
        name=name,
        slug=slug,
        field_type=field_type,
        required=required,
        unique=unique,
        default_value=default_value,
        choices=choices or [],
        position=position,
        is_active=is_active,
        is_system=is_system,
    )

    log_action(
        business=business,
        user=user,
        action="field.created",
        resource="field",
        object_id=field.pk,
        ip_address=ip_address,
        metadata={
            "entity_id": str(entity.pk),
            "entity_name": entity.name,
            "name": field.name,
            "slug": field.slug,
            "field_type": field.field_type,
        },
    )

    return field


@transaction.atomic
def update_field_for_entity(
    *,
    user,
    field,
    name=None,
    slug=None,
    field_type=None,
    required=None,
    unique=None,
    default_value=None,
    choices=None,
    position=None,
    ip_address=None,
):
    if not user or not user.is_authenticated:
        raise ValueError("Authenticated user is required.")

    if field.is_system:
        raise ValueError("System fields cannot be modified.")

    business = field.entity.business

    if not get_membership(user, business):
        raise PermissionError(
            "You are not an active member of this business."
        )

    if not user_can(user, business, "entity.manage"):
        raise PermissionError(
            "You do not have permission to manage entity fields."
        )

    old_data = {
        "name": field.name,
        "slug": field.slug,
        "field_type": field.field_type,
        "required": field.required,
        "unique": field.unique,
        "default_value": field.default_value,
        "choices": field.choices,
        "position": field.position,
    }

    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("Field name is required.")
        field.name = name

    if slug is not None:
        slug = slugify(slug)
        if not slug:
            raise ValueError("A valid field slug is required.")

        if FieldDefinition.objects.filter(
            entity=field.entity,
            slug=slug,
        ).exclude(id=field.id).exists():
            raise ValueError(
                f"A field with slug '{slug}' already exists in this entity."
            )

        field.slug = slug

    if field_type is not None:
        valid_types = {
            "text", "long_text", "number", "decimal",
            "boolean", "date", "datetime", "email",
            "url", "choice", "json",
        }
        if field_type not in valid_types:
            raise ValueError("Invalid field type.")
        field.field_type = field_type

    if required is not None:
        field.required = required

    if unique is not None:
        field.unique = unique

    if default_value is not None:
        field.default_value = default_value

    if choices is not None:
        field.choices = choices

    if position is not None:
        field.position = position

    field.save()

    log_action(
        business=business,
        user=user,
        action="field.updated",
        resource="field",
        object_id=field.pk,
        ip_address=ip_address,
        metadata={
            "entity_id": str(field.entity_id),
            "old_data": old_data,
            "new_data": {
                "name": field.name,
                "slug": field.slug,
                "field_type": field.field_type,
                "required": field.required,
                "unique": field.unique,
                "default_value": field.default_value,
                "choices": field.choices,
                "position": field.position,
            },
        },
    )

    return field


@transaction.atomic
def deactivate_field_for_entity(
    *,
    user,
    field,
    ip_address=None,
):
    if not user or not user.is_authenticated:
        raise ValueError("Authenticated user is required.")

    if field.is_system:
        raise ValueError("System fields cannot be deactivated.")

    business = field.entity.business

    if not get_membership(user, business):
        raise PermissionError(
            "You are not an active member of this business."
        )

    if not user_can(user, business, "entity.manage"):
        raise PermissionError(
            "You do not have permission to manage entity fields."
        )

    if not field.is_active:
        raise ValueError("Field is already inactive.")

    field.is_active = False
    field.save(update_fields=["is_active", "updated_at"])

    log_action(
        business=business,
        user=user,
        action="field.deactivated",
        resource="field",
        object_id=field.pk,
        ip_address=ip_address,
        metadata={
            "entity_id": str(field.entity_id),
            "name": field.name,
            "slug": field.slug,
        },
    )

    return field
