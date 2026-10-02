from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from core.models import EntityRecord
from core.services.audit import log_action
from core.services.permissions import get_membership, user_can


FIELD_TYPES = {
    "text",
    "long_text",
    "number",
    "decimal",
    "boolean",
    "date",
    "datetime",
    "email",
    "url",
    "choice",
    "json",
}


def validate_record_data(entity, data):
    if not isinstance(data, dict):
        raise ValueError("Record data must be a JSON object.")

    fields = entity.fields.filter(
        is_active=True
    ).order_by("position", "created_at")

    field_map = {field.slug: field for field in fields}

    unknown_fields = set(data.keys()) - set(field_map.keys())

    if unknown_fields:
        names = ", ".join(sorted(unknown_fields))
        raise ValueError(f"Unknown field(s): {names}")

    cleaned = {}

    for field in fields:
        value = data.get(field.slug)

        if value is None or value == "":
            if field.required:
                raise ValueError(
                    f"Field '{field.name}' is required."
                )

            if field.default_value is not None:
                cleaned[field.slug] = field.default_value

            continue

        cleaned[field.slug] = validate_field_value(
            field,
            value,
        )

    return cleaned


def validate_field_value(field, value):
    field_type = field.field_type

    if field_type not in FIELD_TYPES:
        raise ValueError(
            f"Unsupported field type '{field_type}'."
        )

    if field_type in {"text", "long_text"}:
        if not isinstance(value, str):
            raise ValueError(
                f"Field '{field.name}' must be text."
            )

        return value.strip()

    if field_type == "number":
        if isinstance(value, bool):
            raise ValueError(
                f"Field '{field.name}' must be a number."
            )

        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"Field '{field.name}' must be a number."
            )

        if number.is_integer():
            return int(number)

        return number

    if field_type == "decimal":
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                f"Field '{field.name}' must be a decimal number."
            )

        return str(decimal_value)

    if field_type == "boolean":
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in {"true", "1", "yes"}:
                return True

            if normalized in {"false", "0", "no"}:
                return False

        if value in {0, 1}:
            return bool(value)

        raise ValueError(
            f"Field '{field.name}' must be true or false."
        )

    if field_type == "date":
        if isinstance(value, date) and not isinstance(
            value,
            datetime,
        ):
            return value.isoformat()

        if not isinstance(value, str):
            raise ValueError(
                f"Field '{field.name}' must be a date in YYYY-MM-DD format."
            )

        parsed = parse_date(value)

        if not parsed:
            raise ValueError(
                f"Field '{field.name}' must be a date in YYYY-MM-DD format."
            )

        return parsed.isoformat()

    if field_type == "datetime":
        if isinstance(value, datetime):
            return value.isoformat()

        if not isinstance(value, str):
            raise ValueError(
                f"Field '{field.name}' must be a valid datetime."
            )

        parsed = parse_datetime(value)

        if not parsed:
            raise ValueError(
                f"Field '{field.name}' must be a valid datetime."
            )

        return parsed.isoformat()

    if field_type == "email":
        if not isinstance(value, str):
            raise ValueError(
                f"Field '{field.name}' must be a valid email address."
            )

        value = value.strip()

        if (
            "@" not in value
            or value.startswith("@")
            or value.endswith("@")
        ):
            raise ValueError(
                f"Field '{field.name}' must be a valid email address."
            )

        return value

    if field_type == "url":
        if not isinstance(value, str):
            raise ValueError(
                f"Field '{field.name}' must be a valid URL."
            )

        value = value.strip()

        if not (
            value.startswith("http://")
            or value.startswith("https://")
        ):
            raise ValueError(
                f"Field '{field.name}' must start with http:// or https://."
            )

        return value

    if field_type == "choice":
        choices = field.choices or []
        allowed = set()

        for choice in choices:
            if isinstance(choice, str):
                allowed.add(choice)

            elif isinstance(choice, dict):
                if "value" in choice:
                    allowed.add(str(choice["value"]))

        if value not in allowed and str(value) not in allowed:
            raise ValueError(
                f"Invalid choice for field '{field.name}'."
            )

        return value

    if field_type == "json":
        if not isinstance(
            value,
            (dict, list, str, int, float, bool),
        ):
            raise ValueError(
                f"Field '{field.name}' must contain valid JSON data."
            )

        return value

    raise ValueError(
        f"Unsupported field type '{field_type}'."
    )


@transaction.atomic
def create_record_for_entity(
    *,
    user,
    entity,
    data,
    ip_address=None,
):
    if not user or not user.is_authenticated:
        raise ValueError(
            "Authenticated user is required."
        )

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
        "entity.create",
    ):
        raise PermissionError(
            "You do not have permission to create records."
        )

    cleaned_data = validate_record_data(
        entity,
        data,
    )

    record = EntityRecord.objects.create(
        entity=entity,
        data=cleaned_data,
        created_by=user,
    )

    log_action(
        business=business,
        user=user,
        action="record.created",
        resource="entity_record",
        object_id=record.pk,
        ip_address=ip_address,
        metadata={
            "entity_id": str(entity.pk),
            "entity_name": entity.name,
            "record_id": str(record.pk),
        },
    )

    return record


@transaction.atomic
def update_record_for_entity(
    *,
    user,
    record,
    data,
    ip_address=None,
):
    if not user or not user.is_authenticated:
        raise ValueError(
            "Authenticated user is required."
        )

    entity = record.entity
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
        "entity.update",
    ):
        raise PermissionError(
            "You do not have permission to update records."
        )

    if not isinstance(data, dict):
        raise ValueError(
            "Record data must be a JSON object."
        )

    merged_data = dict(record.data or {})
    merged_data.update(data)

    cleaned_data = validate_record_data(
        entity,
        merged_data,
    )

    old_data = dict(record.data or {})

    record.data = cleaned_data
    record.save(
        update_fields=[
            "data",
            "updated_at",
        ]
    )

    log_action(
        business=business,
        user=user,
        action="record.updated",
        resource="entity_record",
        object_id=record.pk,
        ip_address=ip_address,
        metadata={
            "entity_id": str(entity.pk),
            "entity_name": entity.name,
            "record_id": str(record.pk),
            "old_data": old_data,
            "new_data": cleaned_data,
        },
    )

    return record


@transaction.atomic
def delete_record_for_entity(
    *,
    user,
    record,
    ip_address=None,
):
    if not user or not user.is_authenticated:
        raise ValueError(
            "Authenticated user is required."
        )

    entity = record.entity
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
        "entity.delete",
    ):
        raise PermissionError(
            "You do not have permission to delete records."
        )

    if record.is_deleted:
        raise ValueError(
            "Entity record has already been deleted."
        )

    record.is_deleted = True
    record.deleted_at = timezone.now()
    record.deleted_by = user

    record.save(
        update_fields=[
            "is_deleted",
            "deleted_at",
            "deleted_by",
            "updated_at",
        ]
    )

    log_action(
        business=business,
        user=user,
        action="record.deleted",
        resource="entity_record",
        object_id=record.pk,
        ip_address=ip_address,
        metadata={
            "entity_id": str(entity.pk),
            "entity_name": entity.name,
            "record_id": str(record.pk),
        },
    )

    return record
