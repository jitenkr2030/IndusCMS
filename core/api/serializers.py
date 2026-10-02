from django.utils.text import slugify
from rest_framework import serializers

from core.models import (
    Business,
    EntityDefinition,
    EntityRecord,
    FieldDefinition,
)


class BusinessCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = (
            "name",
            "industry",
            "email",
            "phone",
            "website",
            "address",
            "city",
            "state",
            "country",
        )

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Business name is required.")
        return value


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = (
            "id",
            "name",
            "slug",
            "industry",
            "email",
            "phone",
            "website",
            "address",
            "city",
            "state",
            "country",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "created_at",
            "updated_at",
        )


class EntityDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityDefinition
        fields = (
            "id",
            "business",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "business",
            "created_at",
            "updated_at",
        )

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Entity name is required.")
        return value

    def validate_slug(self, value):
        value = slugify(value)
        if not value:
            raise serializers.ValidationError(
                "A valid entity slug is required."
            )
        return value


class FieldDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldDefinition
        fields = (
            "id",
            "entity",
            "name",
            "slug",
            "field_type",
            "required",
            "unique",
            "default_value",
            "choices",
            "position",
            "is_active",
            "is_system",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "entity",
            "created_at",
            "updated_at",
        )

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Field name is required.")
        return value

    def validate_slug(self, value):
        value = slugify(value)
        if not value:
            raise serializers.ValidationError(
                "A valid field slug is required."
            )
        return value

    def validate_field_type(self, value):
        field = FieldDefinition._meta.get_field("field_type")
        valid_types = {choice[0] for choice in field.choices}

        if value not in valid_types:
            raise serializers.ValidationError("Invalid field type.")

        return value


class EntityRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityRecord
        fields = (
            "id",
            "entity",
            "data",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "entity",
            "created_by",
            "created_at",
            "updated_at",
        )

    def validate_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Record data must be a JSON object."
            )
        return value
