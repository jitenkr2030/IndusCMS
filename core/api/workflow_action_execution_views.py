from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import WorkflowActionExecution
from core.services.permissions import get_membership, user_can
from core.services.workflow_action import (
    retry_workflow_action_execution,
)


def _get_execution(execution_id):
    return (
        WorkflowActionExecution.objects
        .select_related(
            "workflow_instance",
            "workflow_instance__workflow",
            "workflow_instance__workflow__business",
            "workflow_instance__record",
            "workflow_action",
        )
        .get(pk=execution_id)
    )


def _serialize(execution):
    action = execution.workflow_action
    instance = execution.workflow_instance

    return {
        "id": str(execution.id),
        "workflow_instance": str(
            execution.workflow_instance_id
        ),
        "workflow_action": (
            str(execution.workflow_action_id)
            if execution.workflow_action_id
            else None
        ),
        "action_name": (
            action.name
            if action
            else None
        ),
        "action_type": (
            action.action_type
            if action
            else None
        ),
        "status": execution.status,
        "retry_count": execution.retry_count,
        "max_retries": execution.max_retries,
        "next_retry_at": (
            execution.next_retry_at.isoformat()
            if execution.next_retry_at
            else None
        ),
        "last_retry_at": (
            execution.last_retry_at.isoformat()
            if execution.last_retry_at
            else None
        ),
        "started_at": execution.started_at.isoformat(),
        "completed_at": (
            execution.completed_at.isoformat()
            if execution.completed_at
            else None
        ),
        "error": execution.error,
        "result": execution.result,
        "record_id": str(instance.record_id),
        "workflow_id": str(instance.workflow_id),
    }


class WorkflowActionExecutionListAPIView(APIView):
    def get(self, request):
        instance_id = request.query_params.get(
            "workflow_instance_id"
        )

        if not instance_id:
            return Response(
                {
                    "detail":
                    "workflow_instance_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        executions = (
            WorkflowActionExecution.objects
            .filter(
                workflow_instance_id=instance_id,
            )
            .select_related(
                "workflow_instance__workflow__business",
                "workflow_action",
            )
            .order_by("-started_at")
        )

        instance = executions.first()

        if instance:
            business = (
                instance.workflow_instance
                .workflow
                .business
            )
        else:
            from core.models import WorkflowInstance

            try:
                workflow_instance = (
                    WorkflowInstance.objects
                    .select_related(
                        "workflow__business",
                    )
                    .get(pk=instance_id)
                )
            except WorkflowInstance.DoesNotExist:
                return Response(
                    {"detail": "Workflow instance not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            business = workflow_instance.workflow.business

        if not get_membership(request.user, business):
            return Response(
                {
                    "detail":
                    "You are not an active member of this business."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            business,
            "workflow.view",
        ):
            return Response(
                {
                    "detail":
                    "You do not have permission to view workflow executions."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response({
            "success": True,
            "results": [
                _serialize(item)
                for item in executions
            ],
        })


class WorkflowActionExecutionDetailAPIView(APIView):
    def get(self, request, execution_id):
        try:
            execution = _get_execution(
                execution_id
            )
        except WorkflowActionExecution.DoesNotExist:
            return Response(
                {"detail": "Execution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        business = (
            execution.workflow_instance
            .workflow
            .business
        )

        if not get_membership(
            request.user,
            business,
        ):
            return Response(
                {
                    "detail":
                    "You are not an active member of this business."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            business,
            "workflow.view",
        ):
            return Response(
                {
                    "detail":
                    "You do not have permission to view workflow executions."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response({
            "success": True,
            "result": _serialize(execution),
        })


class WorkflowActionExecutionRetryAPIView(APIView):
    def post(self, request, execution_id):
        try:
            execution = _get_execution(
                execution_id
            )
        except WorkflowActionExecution.DoesNotExist:
            return Response(
                {"detail": "Execution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        business = (
            execution.workflow_instance
            .workflow
            .business
        )

        if not get_membership(
            request.user,
            business,
        ):
            return Response(
                {
                    "detail":
                    "You are not an active member of this business."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            business,
            "workflow.manage",
        ):
            return Response(
                {
                    "detail":
                    "You do not have permission to retry workflow actions."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            result = retry_workflow_action_execution(
                execution=execution,
                user=request.user,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            result,
            status=(
                status.HTTP_200_OK
                if result.get("success")
                else status.HTTP_200_OK
            ),
        )
