from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.workflow_condition_serializers import WorkflowConditionSerializer
from core.models import WorkflowCondition
from core.services.workflow_condition_management import (
    update_workflow_condition,
    deactivate_workflow_condition,
    delete_workflow_condition,
)
from core.services.permissions import get_membership, user_can


def _get_condition(condition_id):
    return WorkflowCondition.objects.select_related(
        "transition__workflow__business",
    ).get(pk=condition_id)


class WorkflowConditionUpdateAPIView(APIView):
    def patch(self, request, condition_id):
        try:
            condition = _get_condition(condition_id)
        except WorkflowCondition.DoesNotExist:
            return Response({"detail": "Condition not found."}, status=404)
        try:
            condition = update_workflow_condition(
                user=request.user,
                condition=condition,
                field_slug=request.data.get("field_slug"),
                operator=request.data.get("operator"),
                value=request.data.get("value") if "value" in request.data else None,
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(WorkflowConditionSerializer(condition).data)


class WorkflowConditionDeactivateAPIView(APIView):
    def patch(self, request, condition_id):
        try:
            condition = _get_condition(condition_id)
        except WorkflowCondition.DoesNotExist:
            return Response({"detail": "Condition not found."}, status=404)
        try:
            condition = deactivate_workflow_condition(
                user=request.user, condition=condition
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(WorkflowConditionSerializer(condition).data)


class WorkflowConditionDeleteAPIView(APIView):
    def delete(self, request, condition_id):
        try:
            condition = _get_condition(condition_id)
        except WorkflowCondition.DoesNotExist:
            return Response({"detail": "Condition not found."}, status=404)
        try:
            delete_workflow_condition(
                user=request.user, condition=condition
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response({"success": True, "message": "Condition deleted."})
