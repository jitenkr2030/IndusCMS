from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import (
    Business,
    EntityDefinition,
    EntityRecord,
    Membership,
    Permission,
    Role,
    RolePermission,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTransition,
    WorkflowInstance,
    WorkflowHistory,
)


class WorkflowAPITestBase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="workflowuser",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="otherworkflowuser",
            password="testpass123",
        )

        self.business = Business.objects.create(
            name="Workflow Business",
            slug="workflow-business",
            industry="IT",
        )

        self.entity = EntityDefinition.objects.create(
            business=self.business,
            name="Task",
            slug="task",
        )

        self.record = EntityRecord.objects.create(
            entity=self.entity,
            data={"title": "Test Task"},
            created_by=self.user,
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        self.membership = Membership.objects.create(
            user=self.user,
            business=self.business,
            role=self.role,
            is_active=True,
        )

        permission_codes = [
            "workflow.view",
            "workflow.create",
            "workflow.update",
            "workflow.delete",
            "workflow.manage",
        ]

        for code in permission_codes:
            permission = Permission.objects.create(
                code=code,
                name=code.replace(".", " ").title(),
                resource="workflow",
                action="manage",
            )
            RolePermission.objects.create(
                role=self.role,
                permission=permission,
            )

        self.client.force_authenticate(user=self.user)

    def create_workflow(self, slug="task-workflow"):
        return WorkflowDefinition.objects.create(
            business=self.business,
            entity=self.entity,
            name="Task Workflow",
            slug=slug,
            description="Test workflow",
        )

    def create_steps(self, workflow):
        pending = WorkflowStep.objects.create(
            workflow=workflow,
            name="Pending",
            slug="pending",
            position=1,
            is_initial=True,
        )

        approved = WorkflowStep.objects.create(
            workflow=workflow,
            name="Approved",
            slug="approved",
            position=2,
            is_final=True,
        )

        return pending, approved

    def create_transition(self, workflow, pending, approved):
        return WorkflowTransition.objects.create(
            workflow=workflow,
            from_step=pending,
            to_step=approved,
            name="Approve",
            slug="approve",
        )


class WorkflowCreationAPITests(WorkflowAPITestBase):

    def test_create_workflow(self):
        response = self.client.post(
            "/api/workflows/",
            {
                "business_id": str(self.business.id),
                "entity_id": str(self.entity.id),
                "name": "Approval Workflow",
                "slug": "approval-workflow",
                "description": "Approval flow",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            WorkflowDefinition.objects.filter(
                business=self.business,
                slug="approval-workflow",
            ).exists()
        )

    def test_list_workflows(self):
        workflow = self.create_workflow()

        response = self.client.get(
            f"/api/workflows/list/?business_id={self.business.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], str(workflow.id))

    def test_workflow_detail(self):
        workflow = self.create_workflow()

        response = self.client.get(
            f"/api/workflows/{workflow.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["workflow"]["name"],
            "Task Workflow",
        )


class WorkflowStructureAPITests(WorkflowAPITestBase):

    def test_create_step(self):
        workflow = self.create_workflow()

        response = self.client.post(
            "/api/workflow-steps/",
            {
                "workflow_id": str(workflow.id),
                "name": "Pending",
                "slug": "pending",
                "position": 1,
                "is_initial": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            WorkflowStep.objects.filter(
                workflow=workflow,
                slug="pending",
            ).exists()
        )

    def test_create_transition(self):
        workflow = self.create_workflow()
        pending, approved = self.create_steps(workflow)

        response = self.client.post(
            "/api/workflow-transitions/",
            {
                "workflow_id": str(workflow.id),
                "from_step_id": str(pending.id),
                "to_step_id": str(approved.id),
                "name": "Approve",
                "slug": "approve",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            WorkflowTransition.objects.filter(
                workflow=workflow,
                slug="approve",
            ).exists()
        )

    def test_step_list(self):
        workflow = self.create_workflow()
        self.create_steps(workflow)

        response = self.client.get(
            f"/api/workflow-steps/list/?workflow_id={workflow.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_transition_list(self):
        workflow = self.create_workflow()
        pending, approved = self.create_steps(workflow)
        self.create_transition(workflow, pending, approved)

        response = self.client.get(
            f"/api/workflow-transitions/list/?workflow_id={workflow.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)


class WorkflowInstanceAPITests(WorkflowAPITestBase):

    def test_start_workflow_instance(self):
        workflow = self.create_workflow()
        pending, approved = self.create_steps(workflow)

        response = self.client.post(
            "/api/workflow-instances/",
            {
                "workflow_id": str(workflow.id),
                "record_id": str(self.record.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        instance = WorkflowInstance.objects.get(
            workflow=workflow,
            record=self.record,
        )

        self.assertEqual(
            instance.current_step_id,
            pending.id,
        )
        self.assertEqual(instance.status, "active")

        self.assertTrue(
            WorkflowHistory.objects.filter(
                instance=instance,
                action="started",
            ).exists()
        )

    def test_start_workflow_creates_completed_history_for_final_initial_step(self):
        workflow = self.create_workflow()

        final_step = WorkflowStep.objects.create(
            workflow=workflow,
            name="Completed",
            slug="completed",
            position=1,
            is_initial=True,
            is_final=True,
        )

        response = self.client.post(
            "/api/workflow-instances/",
            {
                "workflow_id": str(workflow.id),
                "record_id": str(self.record.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        instance = WorkflowInstance.objects.get(
            workflow=workflow,
            record=self.record,
        )

        self.assertEqual(instance.status, "completed")
        self.assertEqual(
            instance.current_step_id,
            final_step.id,
        )

        self.assertTrue(
            WorkflowHistory.objects.filter(
                instance=instance,
                action="completed",
            ).exists()
        )

    def test_transition_workflow_instance(self):
        workflow = self.create_workflow()
        pending, approved = self.create_steps(workflow)
        transition = self.create_transition(
            workflow,
            pending,
            approved,
        )

        instance = WorkflowInstance.objects.create(
            workflow=workflow,
            record=self.record,
            current_step=pending,
            started_by=self.user,
            status="active",
        )

        response = self.client.post(
            f"/api/workflow-instances/{instance.id}/transition/",
            {
                "transition_id": str(transition.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        instance.refresh_from_db()

        self.assertEqual(
            instance.current_step_id,
            approved.id,
        )
        self.assertEqual(instance.status, "completed")

        self.assertTrue(
            WorkflowHistory.objects.filter(
                instance=instance,
                transition=transition,
                action="completed",
            ).exists()
        )

    def test_instance_detail(self):
        workflow = self.create_workflow()
        pending, _ = self.create_steps(workflow)

        instance = WorkflowInstance.objects.create(
            workflow=workflow,
            record=self.record,
            current_step=pending,
            started_by=self.user,
            status="active",
        )

        response = self.client.get(
            f"/api/workflow-instances/{instance.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["id"],
            str(instance.id),
        )

    def test_instance_list(self):
        workflow = self.create_workflow()
        pending, _ = self.create_steps(workflow)

        instance = WorkflowInstance.objects.create(
            workflow=workflow,
            record=self.record,
            current_step=pending,
            started_by=self.user,
            status="active",
        )

        response = self.client.get(
            f"/api/workflow-instances/list/?workflow_id={workflow.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            str(instance.id),
        )

    def test_instance_history(self):
        workflow = self.create_workflow()
        pending, _ = self.create_steps(workflow)

        instance = WorkflowInstance.objects.create(
            workflow=workflow,
            record=self.record,
            current_step=pending,
            started_by=self.user,
            status="active",
        )

        WorkflowHistory.objects.create(
            instance=instance,
            to_step=pending,
            action="started",
            performed_by=self.user,
            note="Workflow started.",
        )

        response = self.client.get(
            f"/api/workflow-instances/{instance.id}/history/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["action"],
            "started",
        )


class WorkflowManagementAPITests(WorkflowAPITestBase):

    def test_update_workflow(self):
        workflow = self.create_workflow()

        response = self.client.patch(
            f"/api/workflows/{workflow.id}/update/",
            {
                "name": "Updated Workflow",
                "description": "Updated description",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        workflow.refresh_from_db()

        self.assertEqual(
            workflow.name,
            "Updated Workflow",
        )

    def test_deactivate_workflow(self):
        workflow = self.create_workflow()

        response = self.client.patch(
            f"/api/workflows/{workflow.id}/deactivate/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        workflow.refresh_from_db()

        self.assertFalse(workflow.is_active)

    def test_deactivate_workflow_twice_fails(self):
        workflow = self.create_workflow()

        self.client.patch(
            f"/api/workflows/{workflow.id}/deactivate/",
            {},
            format="json",
        )

        response = self.client.patch(
            f"/api/workflows/{workflow.id}/deactivate/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_delete_workflow_without_instances(self):
        workflow = self.create_workflow()

        response = self.client.delete(
            f"/api/workflows/{workflow.id}/delete/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            WorkflowDefinition.objects.filter(
                id=workflow.id
            ).exists()
        )

    def test_delete_workflow_with_instance_is_blocked(self):
        workflow = self.create_workflow()
        pending, _ = self.create_steps(workflow)

        WorkflowInstance.objects.create(
            workflow=workflow,
            record=self.record,
            current_step=pending,
            started_by=self.user,
            status="active",
        )

        response = self.client.delete(
            f"/api/workflows/{workflow.id}/delete/"
        )

        self.assertEqual(response.status_code, 400)

        self.assertTrue(
            WorkflowDefinition.objects.filter(
                id=workflow.id
            ).exists()
        )
