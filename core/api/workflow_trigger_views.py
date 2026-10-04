
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.workflow_trigger_serializers import (
    WorkflowTriggerSerializer,
)
from core.models import WorkflowDefinition, WorkflowTrigger
from core.services.permissions import get_membership, user_can
from core.services.workflow_trigger import (
    VALID_EVENT_TYPES,
    create_workflow_trigger,
    update_workflow_trigger,
    deactivate_workflow_trigger,
    delete_workflow_trigger,
)


class WorkflowTriggerCreateAPIView(APIView):

    def post(self, request):
        workflow_id = request.data.get("workflow_id")

        if not workflow_id:
            return Response(
                {"detail": "workflow_id is required."},
                status=400,
            )

        try:
            workflow = WorkflowDefinition.objects.select_related(
                "business",
            ).get(pk=workflow_id)
        except WorkflowDefinition.DoesNotExist:
            return Response(
                {"detail": "Workflow not found."},
                status=404,
            )

        try:
            trigger = create_workflow_trigger(
                user=request.user,
                workflow=workflow,
                name=request.data.get("name"),
                event_type=request.data.get("event_type"),
                config=request.data.get("config"),
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        return Response(
            WorkflowTriggerSerializer(trigger).data,
            status=status.HTTP_201_CREATED,
        )


class WorkflowTriggerListAPIView(APIView):

    def get(self, request):
        workflow_id = request.query_params.get("workflow_id")

        if not workflow_id:
            return Response(
                {"detail": "workflow_id is required."},
                status=400,
            )

        try:
            workflow = WorkflowDefinition.objects.select_related(
                "business",
            ).get(pk=workflow_id)
        except WorkflowDefinition.DoesNotExist:
            return Response(
                {"detail": "Workflow not found."},
                status=404,
            )

        business = workflow.business

        if not get_membership(request.user, business):
            return Response(
                {"detail": "You are not an active member of this business."},
                status=403,
            )

        if not user_can(
            request.user,
            business,
            "workflow.view",
        ):
            return Response(
                {"detail": "You do not have permission to view workflow triggers."},
                status=403,
            )

        triggers = WorkflowTrigger.objects.filter(
            workflow=workflow,
            is_active=True,
        ).order_by("name")

        return Response({
            "success": True,
            "workflow": {
                "id": str(workflow.id),
                "name": workflow.name,
            },
            "results": WorkflowTriggerSerializer(
                triggers,
                many=True,
            ).data,
        })


def _get_trigger(trigger_id):
    return WorkflowTrigger.objects.select_related(
        "workflow__business",
    ).get(pk=trigger_id)


class WorkflowTriggerUpdateAPIView(APIView):

    def patch(self, request, trigger_id):
        try:
            trigger = _get_trigger(trigger_id)
        except WorkflowTrigger.DoesNotExist:
            return Response(
                {"detail": "Trigger not found."},
                status=404,
            )

        try:
            trigger = update_workflow_trigger(
                user=request.user,
                trigger=trigger,
                name=request.data.get("name"),
                event_type=request.data.get("event_type"),
                config=request.data.get("config"),
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        return Response(
            WorkflowTriggerSerializer(trigger).data
        )


class WorkflowTriggerDeactivateAPIView(APIView):

    def patch(self, request, trigger_id):
        try:
            trigger = _get_trigger(trigger_id)
        except WorkflowTrigger.DoesNotExist:
            return Response(
                {"detail": "Trigger not found."},
                status=404,
            )

        try:
            trigger = deactivate_workflow_trigger(
                user=request.user,
                trigger=trigger,
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        return Response(
            WorkflowTriggerSerializer(trigger).data
        )


class WorkflowTriggerDeleteAPIView(APIView):

    def delete(self, request, trigger_id):
        try:
            trigger = _get_trigger(trigger_id)
        except WorkflowTrigger.DoesNotExist:
            return Response(
                {"detail": "Trigger not found."},
                status=404,
            )

        try:
            delete_workflow_trigger(
                user=request.user,
                trigger=trigger,
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        return Response({
            "success": True,
            "message": "Trigger deleted.",
        })
