from rest_framework import serializers

from core.models import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTransition,
    WorkflowInstance,
)


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(
        source="entity.name",
        read_only=True,
    )

    class Meta:
        model = WorkflowDefinition
        fields = (
            "id",
            "business",
            "entity",
            "entity_name",
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
            "entity_name",
            "created_at",
            "updated_at",
        )


class WorkflowStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStep
        fields = (
            "id",
            "workflow",
            "name",
            "slug",
            "description",
            "position",
            "is_initial",
            "is_final",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class WorkflowTransitionSerializer(serializers.ModelSerializer):
    from_step_name = serializers.CharField(
        source="from_step.name",
        read_only=True,
    )
    to_step_name = serializers.CharField(
        source="to_step.name",
        read_only=True,
    )

    class Meta:
        model = WorkflowTransition
        fields = (
            "id",
            "workflow",
            "from_step",
            "from_step_name",
            "to_step",
            "to_step_name",
            "name",
            "slug",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "from_step_name",
            "to_step_name",
            "created_at",
            "updated_at",
        )


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(
        source="workflow.name",
        read_only=True,
    )
    current_step_name = serializers.CharField(
        source="current_step.name",
        read_only=True,
    )

    class Meta:
        model = WorkflowInstance
        fields = (
            "id",
            "workflow",
            "workflow_name",
            "record",
            "current_step",
            "current_step_name",
            "status",
            "started_by",
            "started_at",
            "completed_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "workflow_name",
            "current_step_name",
            "status",
            "started_by",
            "started_at",
            "completed_at",
            "updated_at",
        )
