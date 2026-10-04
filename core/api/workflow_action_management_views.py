from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.workflow_action_serializers import WorkflowActionSerializer
from core.models import WorkflowAction
from core.services.workflow_action_management import (
    update_workflow_action,
    deactivate_workflow_action,
    delete_workflow_action,
    reorder_workflow_action,
)


def _get_action(action_id):
    return WorkflowAction.objects.select_related(
        "transition__workflow__business",
    ).get(pk=action_id)


class WorkflowActionUpdateAPIView(APIView):
    def patch(self, request, action_id):
        try:
            action = _get_action(action_id)
        except WorkflowAction.DoesNotExist:
            return Response({"detail": "Action not found."}, status=404)
        try:
            action = update_workflow_action(
                user=request.user,
                action=action,
                name=request.data.get("name"),
                action_type=request.data.get("action_type"),
                config=request.data.get("config"),
                position=request.data.get("position"),
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(WorkflowActionSerializer(action).data)


class WorkflowActionDeactivateAPIView(APIView):
    def patch(self, request, action_id):
        try:
            action = _get_action(action_id)
        except WorkflowAction.DoesNotExist:
            return Response({"detail": "Action not found."}, status=404)
        try:
            action = deactivate_workflow_action(
                user=request.user, action=action
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(WorkflowActionSerializer(action).data)


class WorkflowActionDeleteAPIView(APIView):
    def delete(self, request, action_id):
        try:
            action = _get_action(action_id)
        except WorkflowAction.DoesNotExist:
            return Response({"detail": "Action not found."}, status=404)
        try:
            delete_workflow_action(
                user=request.user, action=action
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response({"success": True, "message": "Action deleted."})


class WorkflowActionReorderAPIView(APIView):
    def patch(self, request, action_id):
        try:
            action = _get_action(action_id)
        except WorkflowAction.DoesNotExist:
            return Response({"detail": "Action not found."}, status=404)

        if "position" not in request.data:
            return Response(
                {"detail": "position is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            action = reorder_workflow_action(
                user=request.user,
                action=action,
                position=request.data.get("position"),
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        return Response(WorkflowActionSerializer(action).data)
