from rest_framework import serializers

from core.models import WorkflowCondition


class WorkflowConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowCondition
        fields = (
            "id",
            "transition",
            "field_slug",
            "operator",
            "value",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )
