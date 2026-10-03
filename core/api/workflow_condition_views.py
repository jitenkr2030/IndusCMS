from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.workflow_condition_serializers import (
    WorkflowConditionSerializer,
)
from core.models import WorkflowCondition, WorkflowTransition
from core.services.audit import log_action
from core.services.permissions import get_membership, user_can


VALID_OPERATORS = {
    "equals",
    "not_equals",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "contains",
    "is_true",
    "is_false",
}


class WorkflowConditionCreateAPIView(APIView):

    def post(self, request):
        transition_id = request.data.get("transition_id")
        field_slug = request.data.get("field_slug")
        operator = request.data.get("operator")
        value = request.data.get("value")

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
                {
                    "error": (
                        "You are not an active member "
                        "of this business."
                    )
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
                    "error": (
                        "You do not have permission "
                        "to manage workflow conditions."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        field_slug = (field_slug or "").strip()

        if not field_slug:
            return Response(
                {"error": "field_slug is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if operator not in VALID_OPERATORS:
            return Response(
                {"error": "Invalid condition operator."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        condition = WorkflowCondition.objects.create(
            transition=transition,
            field_slug=field_slug,
            operator=operator,
            value=value,
        )

        log_action(
            business=business,
            user=request.user,
            action="workflow.condition.created",
            resource="workflow_condition",
            object_id=condition.pk,
            metadata={
                "transition_id": str(transition.pk),
                "field_slug": field_slug,
                "operator": operator,
            },
        )

        return Response(
            WorkflowConditionSerializer(condition).data,
            status=status.HTTP_201_CREATED,
        )


class WorkflowConditionListAPIView(APIView):

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
                {
                    "error": (
                        "You are not an active member "
                        "of this business."
                    )
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
                    "error": (
                        "You do not have permission "
                        "to view workflow conditions."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        conditions = WorkflowCondition.objects.filter(
            transition=transition,
            is_active=True,
        )

        return Response(
            {
                "success": True,
                "transition": {
                    "id": str(transition.id),
                    "name": transition.name,
                    "slug": transition.slug,
                },
                "results": WorkflowConditionSerializer(
                    conditions,
                    many=True,
                ).data,
            }
        )
