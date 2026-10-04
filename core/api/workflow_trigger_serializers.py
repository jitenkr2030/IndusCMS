
from rest_framework import serializers

from core.models import WorkflowTrigger


class WorkflowTriggerSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(
        source="workflow.name",
        read_only=True,
    )

    class Meta:
        model = WorkflowTrigger
        fields = (
            "id",
            "workflow",
            "workflow_name",
            "name",
            "event_type",
            "is_active",
            "config",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "workflow_name",
            "created_at",
            "updated_at",
        )
