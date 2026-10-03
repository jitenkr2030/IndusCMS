from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.models import (
    Business,
    EntityDefinition,
    EntityRecord,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTransition,
    WorkflowInstance,
)
from core.api.workflow_serializers import (
    WorkflowDefinitionSerializer,
    WorkflowStepSerializer,
    WorkflowTransitionSerializer,
    WorkflowInstanceSerializer,
)
from core.services.workflow import (
    create_workflow,
    create_workflow_step,
    create_workflow_transition,
    start_workflow_instance,
    transition_workflow_instance,
)
from core.services.permissions import get_membership, user_can


class WorkflowCreateAPIView(APIView):
    def post(self, request):
        business_id = request.data.get("business_id")
        entity_id = request.data.get("entity_id")

        try:
            business = Business.objects.get(
                id=business_id,
                is_active=True,
            )
            entity = EntityDefinition.objects.get(
                id=entity_id,
                business=business,
                is_active=True,
            )

            workflow = create_workflow(
                user=request.user,
                business=business,
                entity=entity,
                name=request.data.get("name"),
                slug=request.data.get("slug", ""),
                description=request.data.get("description", ""),
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            return Response(
                WorkflowDefinitionSerializer(workflow).data,
                status=status.HTTP_201_CREATED,
            )

        except Business.DoesNotExist:
            return Response(
                {"detail": "Business not found."},
                status=404,
            )
        except EntityDefinition.DoesNotExist:
            return Response(
                {"detail": "Entity not found."},
                status=404,
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)


class WorkflowListAPIView(APIView):
    def get(self, request):
        business_id = request.query_params.get("business_id")

        try:
            business = Business.objects.get(
                id=business_id,
                is_active=True,
            )
        except Business.DoesNotExist:
            return Response(
                {"detail": "Business not found."},
                status=404,
            )

        if not get_membership(request.user, business):
            return Response(
                {"detail": "You are not an active member of this business."},
                status=403,
            )

        if not user_can(request.user, business, "workflow.view"):
            return Response(
                {"detail": "You do not have permission to view workflows."},
                status=403,
            )

        workflows = WorkflowDefinition.objects.filter(
            business=business,
            is_active=True,
        ).select_related("entity")

        return Response(
            {
                "count": workflows.count(),
                "results": WorkflowDefinitionSerializer(
                    workflows,
                    many=True,
                ).data,
            }
        )


class WorkflowDetailAPIView(APIView):
    def get(self, request, workflow_id):
        try:
            workflow = WorkflowDefinition.objects.select_related(
                "business",
                "entity",
            ).get(
                id=workflow_id,
                is_active=True,
                business__is_active=True,
            )
        except WorkflowDefinition.DoesNotExist:
            return Response(
                {"detail": "Workflow not found."},
                status=404,
            )

        if not get_membership(request.user, workflow.business):
            return Response(
                {"detail": "You are not an active member of this business."},
                status=403,
            )

        if not user_can(
            request.user,
            workflow.business,
            "workflow.view",
        ):
            return Response(
                {"detail": "You do not have permission to view workflows."},
                status=403,
            )

        return Response(
            {
                "workflow": WorkflowDefinitionSerializer(workflow).data,
                "steps": WorkflowStepSerializer(
                    workflow.steps.filter(is_active=True),
                    many=True,
                ).data,
                "transitions": WorkflowTransitionSerializer(
                    workflow.transitions.filter(is_active=True),
                    many=True,
                ).data,
            }
        )


class WorkflowStepCreateAPIView(APIView):
    def post(self, request):
        try:
            workflow = WorkflowDefinition.objects.get(
                id=request.data.get("workflow_id"),
                is_active=True,
                business__is_active=True,
            )

            step = create_workflow_step(
                user=request.user,
                workflow=workflow,
                name=request.data.get("name"),
                slug=request.data.get("slug", ""),
                description=request.data.get("description", ""),
                position=int(request.data.get("position", 0)),
                is_initial=bool(request.data.get("is_initial", False)),
                is_final=bool(request.data.get("is_final", False)),
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            return Response(
                WorkflowStepSerializer(step).data,
                status=201,
            )

        except WorkflowDefinition.DoesNotExist:
            return Response({"detail": "Workflow not found."}, status=404)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)


class WorkflowTransitionCreateAPIView(APIView):
    def post(self, request):
        try:
            workflow = WorkflowDefinition.objects.get(
                id=request.data.get("workflow_id"),
                is_active=True,
                business__is_active=True,
            )
            from_step = WorkflowStep.objects.get(
                id=request.data.get("from_step_id"),
                workflow=workflow,
                is_active=True,
            )
            to_step = WorkflowStep.objects.get(
                id=request.data.get("to_step_id"),
                workflow=workflow,
                is_active=True,
            )

            transition = create_workflow_transition(
                user=request.user,
                workflow=workflow,
                from_step=from_step,
                to_step=to_step,
                name=request.data.get("name"),
                slug=request.data.get("slug", ""),
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            return Response(
                WorkflowTransitionSerializer(transition).data,
                status=201,
            )

        except WorkflowDefinition.DoesNotExist:
            return Response({"detail": "Workflow not found."}, status=404)
        except WorkflowStep.DoesNotExist:
            return Response({"detail": "Workflow step not found."}, status=404)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)


class WorkflowInstanceCreateAPIView(APIView):
    def post(self, request):
        try:
            workflow = WorkflowDefinition.objects.get(
                id=request.data.get("workflow_id"),
                is_active=True,
                business__is_active=True,
            )
            record = EntityRecord.objects.get(
                id=request.data.get("record_id"),
                entity=workflow.entity,
                is_deleted=False,
            )

            instance = start_workflow_instance(
                user=request.user,
                workflow=workflow,
                record=record,
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            return Response(
                WorkflowInstanceSerializer(instance).data,
                status=201,
            )

        except WorkflowDefinition.DoesNotExist:
            return Response({"detail": "Workflow not found."}, status=404)
        except EntityRecord.DoesNotExist:
            return Response({"detail": "Record not found."}, status=404)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)


class WorkflowInstanceDetailAPIView(APIView):
    def get(self, request, instance_id):
        try:
            instance = WorkflowInstance.objects.select_related(
                "workflow",
                "workflow__business",
                "current_step",
                "record",
            ).get(
                id=instance_id,
                workflow__business__is_active=True,
            )
        except WorkflowInstance.DoesNotExist:
            return Response(
                {"detail": "Workflow instance not found."},
                status=404,
            )

        business = instance.workflow.business

        if not get_membership(request.user, business):
            return Response(
                {"detail": "You are not an active member of this business."},
                status=403,
            )

        if not user_can(request.user, business, "workflow.view"):
            return Response(
                {"detail": "You do not have permission to view workflows."},
                status=403,
            )

        return Response(
            WorkflowInstanceSerializer(instance).data
        )


class WorkflowTransitionAPIView(APIView):
    def post(self, request, instance_id):
        try:
            instance = WorkflowInstance.objects.select_related(
                "workflow",
                "workflow__business",
                "current_step",
            ).get(
                id=instance_id,
                workflow__business__is_active=True,
            )

            transition = WorkflowTransition.objects.get(
                id=request.data.get("transition_id"),
                workflow=instance.workflow,
                is_active=True,
            )

            instance = transition_workflow_instance(
                user=request.user,
                instance=instance,
                transition=transition,
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            return Response(
                WorkflowInstanceSerializer(instance).data
            )

        except WorkflowInstance.DoesNotExist:
            return Response(
                {"detail": "Workflow instance not found."},
                status=404,
            )
        except WorkflowTransition.DoesNotExist:
            return Response(
                {"detail": "Transition not found."},
                status=404,
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
