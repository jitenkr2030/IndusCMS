
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.workflow_action_serializers import (
    WorkflowActionSerializer,
)
from core.models import WorkflowAction, WorkflowTransition
from core.services.audit import log_action
from core.services.permissions import get_membership, user_can


VALID_ACTION_TYPES = {
    "audit",
    "notification",
    "webhook",
    "update_record",
}


class WorkflowActionCreateAPIView(APIView):

    def post(self, request):
        transition_id = request.data.get("transition_id")
        name = (request.data.get("name") or "").strip()
        action_type = request.data.get("action_type")
        config = request.data.get("config") or {}
        position = request.data.get("position", 0)

        if not transition_id:
            return Response(
                {"error": "transition_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transition = WorkflowTransition.objects.select_related(
                "workflow",
                "workflow__business",
            ).get(id=transition_id)
        except WorkflowTransition.DoesNotExist:
            return Response(
                {"error": "Transition not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        business = transition.workflow.business

        if not get_membership(request.user, business):
            return Response(
                {"error": "You are not an active member of this business."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            business,
            "workflow.manage",
        ):
            return Response(
                {"error": "You do not have permission to manage workflow actions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not name:
            return Response(
                {"error": "name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action_type not in VALID_ACTION_TYPES:
            return Response(
                {"error": "Invalid workflow action type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(config, dict):
            return Response(
                {"error": "config must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        action = WorkflowAction.objects.create(
            transition=transition,
            name=name,
            action_type=action_type,
            config=config,
            position=position,
        )

        log_action(
            business=business,
            user=request.user,
            action="workflow.action.created",
            resource="workflow_action",
            object_id=action.pk,
            metadata={
                "transition_id": str(transition.pk),
                "name": name,
                "action_type": action_type,
            },
        )

        return Response(
            WorkflowActionSerializer(action).data,
            status=status.HTTP_201_CREATED,
        )


class WorkflowActionListAPIView(APIView):

    def get(self, request):
        transition_id = request.query_params.get("transition_id")

        if not transition_id:
            return Response(
                {"error": "transition_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transition = WorkflowTransition.objects.select_related(
                "workflow",
                "workflow__business",
            ).get(id=transition_id)
        except WorkflowTransition.DoesNotExist:
            return Response(
                {"error": "Transition not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        business = transition.workflow.business

        if not get_membership(request.user, business):
            return Response(
                {"error": "You are not an active member of this business."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            business,
            "workflow.view",
        ):
            return Response(
                {"error": "You do not have permission to view workflow actions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        actions = WorkflowAction.objects.filter(
            transition=transition,
            is_active=True,
        ).order_by(
            "position",
            "created_at",
        )

        return Response(
            {
                "success": True,
                "transition": {
                    "id": str(transition.id),
                    "name": transition.name,
                    "slug": transition.slug,
                },
                "results": WorkflowActionSerializer(
                    actions,
                    many=True,
                ).data,
            }
        )
