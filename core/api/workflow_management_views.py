from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTransition,
    WorkflowInstance,
    WorkflowHistory,
)
from core.services.permissions import get_membership, user_can
from core.services.workflow_management import (
    update_workflow,
    deactivate_workflow,
    delete_workflow,
)


class WorkflowManagementSerializer(serializers.ModelSerializer):
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
            "entity",
            "entity_name",
            "created_at",
            "updated_at",
        )


class WorkflowHistorySerializer(serializers.ModelSerializer):
    transition_name = serializers.CharField(
        source="transition.name",
        read_only=True,
        allow_null=True,
    )
    from_step_name = serializers.CharField(
        source="from_step.name",
        read_only=True,
        allow_null=True,
    )
    to_step_name = serializers.CharField(
        source="to_step.name",
        read_only=True,
        allow_null=True,
    )
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowHistory
        fields = (
            "id",
            "instance",
            "transition",
            "transition_name",
            "from_step",
            "from_step_name",
            "to_step",
            "to_step_name",
            "action",
            "performed_by",
            "performed_by_name",
            "note",
            "created_at",
        )

    def get_performed_by_name(self, obj):
        if not obj.performed_by:
            return None
        return obj.performed_by.get_username()


class WorkflowUpdateAPIView(APIView):
    def patch(self, request, workflow_id):
        try:
            workflow = WorkflowDefinition.objects.select_related(
                "business",
                "entity",
            ).get(
                pk=workflow_id,
                business__is_active=True,
            )
        except WorkflowDefinition.DoesNotExist:
            return Response(
                {"detail": "Workflow not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            workflow = update_workflow(
                user=request.user,
                workflow=workflow,
                name=request.data.get("name"),
                slug=request.data.get("slug"),
                description=request.data.get("description"),
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            WorkflowManagementSerializer(workflow).data,
            status=status.HTTP_200_OK,
        )


class WorkflowDeactivateAPIView(APIView):
    def patch(self, request, workflow_id):
        try:
            workflow = WorkflowDefinition.objects.select_related(
                "business",
                "entity",
            ).get(
                pk=workflow_id,
                business__is_active=True,
            )
        except WorkflowDefinition.DoesNotExist:
            return Response(
                {"detail": "Workflow not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            workflow = deactivate_workflow(
                user=request.user,
                workflow=workflow,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            WorkflowManagementSerializer(workflow).data,
            status=status.HTTP_200_OK,
        )


class WorkflowDeleteAPIView(APIView):
    def delete(self, request, workflow_id):
        try:
            workflow = WorkflowDefinition.objects.select_related(
                "business",
            ).get(
                pk=workflow_id,
                business__is_active=True,
            )
        except WorkflowDefinition.DoesNotExist:
            return Response(
                {"detail": "Workflow not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            delete_workflow(
                user=request.user,
                workflow=workflow,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"success": True, "message": "Workflow deleted."},
            status=status.HTTP_200_OK,
        )


class WorkflowStepListAPIView(APIView):
    def get(self, request):
        workflow_id = request.query_params.get("workflow_id")

        if not workflow_id:
            return Response(
                {"detail": "workflow_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            workflow = WorkflowDefinition.objects.select_related(
                "business",
            ).get(
                pk=workflow_id,
                business__is_active=True,
            )
        except WorkflowDefinition.DoesNotExist:
            return Response(
                {"detail": "Workflow not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not get_membership(request.user, workflow.business):
            return Response(
                {"detail": "You are not an active member of this business."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            workflow.business,
            "workflow.view",
        ):
            return Response(
                {"detail": "You do not have permission to view workflows."},
                status=status.HTTP_403_FORBIDDEN,
            )

        steps = workflow.steps.filter(
            is_active=True,
        ).order_by("position", "created_at")

        return Response({
            "success": True,
            "workflow": {
                "id": str(workflow.id),
                "name": workflow.name,
                "slug": workflow.slug,
            },
            "results": [
                {
                    "id": str(step.id),
                    "name": step.name,
                    "slug": step.slug,
                    "description": step.description,
                    "position": step.position,
                    "is_initial": step.is_initial,
                    "is_final": step.is_final,
                    "is_active": step.is_active,
                }
                for step in steps
            ],
        })


class WorkflowTransitionListAPIView(APIView):
    def get(self, request):
        workflow_id = request.query_params.get("workflow_id")

        if not workflow_id:
            return Response(
                {"detail": "workflow_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            workflow = WorkflowDefinition.objects.select_related(
                "business",
            ).get(
                pk=workflow_id,
                business__is_active=True,
            )
        except WorkflowDefinition.DoesNotExist:
            return Response(
                {"detail": "Workflow not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not get_membership(request.user, workflow.business):
            return Response(
                {"detail": "You are not an active member of this business."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            workflow.business,
            "workflow.view",
        ):
            return Response(
                {"detail": "You do not have permission to view workflows."},
                status=status.HTTP_403_FORBIDDEN,
            )

        transitions = workflow.transitions.filter(
            is_active=True,
        ).select_related(
            "from_step",
            "to_step",
        )

        return Response({
            "success": True,
            "workflow": {
                "id": str(workflow.id),
                "name": workflow.name,
                "slug": workflow.slug,
            },
            "results": [
                {
                    "id": str(item.id),
                    "name": item.name,
                    "slug": item.slug,
                    "from_step": str(item.from_step_id),
                    "from_step_name": item.from_step.name,
                    "to_step": str(item.to_step_id),
                    "to_step_name": item.to_step.name,
                    "is_active": item.is_active,
                }
                for item in transitions
            ],
        })


class WorkflowInstanceListAPIView(APIView):
    def get(self, request):
        workflow_id = request.query_params.get("workflow_id")
        selected_status = request.query_params.get("status")

        if not workflow_id:
            return Response(
                {"detail": "workflow_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            workflow = WorkflowDefinition.objects.select_related(
                "business",
            ).get(
                pk=workflow_id,
                business__is_active=True,
            )
        except WorkflowDefinition.DoesNotExist:
            return Response(
                {"detail": "Workflow not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not get_membership(request.user, workflow.business):
            return Response(
                {"detail": "You are not an active member of this business."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            workflow.business,
            "workflow.view",
        ):
            return Response(
                {"detail": "You do not have permission to view workflows."},
                status=status.HTTP_403_FORBIDDEN,
            )

        instances = workflow.instances.select_related(
            "record",
            "current_step",
            "started_by",
        ).order_by("-started_at")

        if selected_status:
            if selected_status not in {
                "active",
                "completed",
                "cancelled",
            }:
                return Response(
                    {"detail": "Invalid workflow status."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            instances = instances.filter(status=selected_status)

        return Response({
            "success": True,
            "workflow": {
                "id": str(workflow.id),
                "name": workflow.name,
                "slug": workflow.slug,
            },
            "results": [
                {
                    "id": str(item.id),
                    "record": str(item.record_id),
                    "current_step": str(item.current_step_id),
                    "current_step_name": item.current_step.name,
                    "status": item.status,
                    "started_by": (
                        item.started_by.get_username()
                        if item.started_by else None
                    ),
                    "started_at": item.started_at,
                    "completed_at": item.completed_at,
                    "updated_at": item.updated_at,
                }
                for item in instances
            ],
        })


class WorkflowInstanceHistoryAPIView(APIView):
    def get(self, request, instance_id):
        try:
            instance = WorkflowInstance.objects.select_related(
                "workflow__business",
            ).get(
                pk=instance_id,
                workflow__business__is_active=True,
            )
        except WorkflowInstance.DoesNotExist:
            return Response(
                {"detail": "Workflow instance not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        business = instance.workflow.business

        if not get_membership(request.user, business):
            return Response(
                {"detail": "You are not an active member of this business."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            business,
            "workflow.view",
        ):
            return Response(
                {"detail": "You do not have permission to view workflows."},
                status=status.HTTP_403_FORBIDDEN,
            )

        history = instance.history.select_related(
            "transition",
            "from_step",
            "to_step",
            "performed_by",
        ).all()

        return Response({
            "success": True,
            "instance": {
                "id": str(instance.id),
                "workflow": str(instance.workflow_id),
                "record": str(instance.record_id),
                "status": instance.status,
            },
            "results": WorkflowHistorySerializer(
                history,
                many=True,
            ).data,
        })
