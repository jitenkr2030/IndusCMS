
from rest_framework import serializers

from core.models import WorkflowAction


class WorkflowActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAction
        fields = (
            "id",
            "transition",
            "name",
            "action_type",
            "config",
            "position",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )
