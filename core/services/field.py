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
