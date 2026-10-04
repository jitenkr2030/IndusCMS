from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from core.models import (
    Business,
    EntityDefinition,
    EntityRecord,
    Membership,
    Permission,
    Role,
    RolePermission,
    WorkflowAction,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTransition,
)
from core.services.workflow import (
    start_workflow_instance,
    transition_workflow_instance,
)
from core.services.workflow_action import (
    execute_workflow_action,
    execute_transition_actions,
)


class WorkflowActionTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="action_user",
            password="password123",
        )

        self.business = Business.objects.create(
            name="Action Test Business",
            slug="action-test-business",
            industry="Finance",
        )

        self.entity = EntityDefinition.objects.create(
            business=self.business,
            name="Invoice",
            slug="invoice",
        )

        self.record = EntityRecord.objects.create(
            entity=self.entity,
            data={
                "amount": 75000,
                "status": "pending",
            },
            created_by=self.user,
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        permissions = [
            ("workflow.manage", "Manage Workflow", "manage"),
            ("workflow.view", "View Workflow", "view"),
            ("workflow.create", "Create Workflow", "create"),
            ("workflow.update", "Update Workflow", "update"),
        ]

        for code, name, action in permissions:
            permission = Permission.objects.create(
                code=code,
                name=name,
                resource="workflow",
                action=action,
            )
            RolePermission.objects.create(
                role=self.role,
                permission=permission,
            )

        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=self.role,
            is_active=True,
        )

        self.workflow = WorkflowDefinition.objects.create(
            business=self.business,
            entity=self.entity,
            name="Invoice Approval",
            slug="invoice-approval",
        )

        self.pending = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Pending",
            slug="pending",
            position=1,
            is_initial=True,
        )

        self.approved = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Approved",
            slug="approved",
            position=2,
            is_final=True,
        )

        self.transition = WorkflowTransition.objects.create(
            workflow=self.workflow,
            from_step=self.pending,
            to_step=self.approved,
            name="Approve Invoice",
            slug="approve-invoice",
        )

        self.client.force_authenticate(self.user)

    def start_instance(self):
        return start_workflow_instance(
            user=self.user,
            workflow=self.workflow,
            record=self.record,
        )

    def test_audit_action_executes(self):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Record Approval",
            action_type="audit",
            config={
                "action": "invoice.approved",
                "message": "Invoice approved.",
            },
        )

        instance = self.start_instance()

        result = execute_workflow_action(
            action=action,
            instance=instance,
            user=self.user,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "audit")

    def test_notification_action_executes(self):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Notify Manager",
            action_type="notification",
            config={
                "recipient": "manager",
                "message": "Invoice requires approval.",
                "channel": "in_app",
            },
        )

        instance = self.start_instance()

        result = execute_workflow_action(
            action=action,
            instance=instance,
            user=self.user,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "notification")

    def test_update_record_action_executes(self):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Set Status",
            action_type="update_record",
            config={
                "field_slug": "status",
                "value": "approved",
            },
        )

        instance = self.start_instance()

        result = execute_workflow_action(
            action=action,
            instance=instance,
            user=self.user,
        )

        self.assertTrue(result["success"])

        self.record.refresh_from_db()

        self.assertEqual(
            self.record.data["status"],
            "approved",
        )

    def test_webhook_action_executes_as_event(self):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Notify ERP",
            action_type="webhook",
            config={
                "url": "https://example.com/webhook",
                "method": "POST",
            },
        )

        instance = self.start_instance()

        result = execute_workflow_action(
            action=action,
            instance=instance,
            user=self.user,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "webhook")

    def test_inactive_action_is_skipped(self):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Inactive Action",
            action_type="audit",
            is_active=False,
        )

        instance = self.start_instance()

        result = execute_workflow_action(
            action=action,
            instance=instance,
            user=self.user,
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["skipped"])

    def test_multiple_actions_execute(self):
        WorkflowAction.objects.create(
            transition=self.transition,
            name="Audit",
            action_type="audit",
            position=1,
        )

        WorkflowAction.objects.create(
            transition=self.transition,
            name="Set Status",
            action_type="update_record",
            config={
                "field_slug": "status",
                "value": "approved",
            },
            position=2,
        )

        instance = self.start_instance()

        results = execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        self.assertEqual(len(results), 2)
        self.assertTrue(all(item["success"] for item in results))

        self.record.refresh_from_db()

        self.assertEqual(
            self.record.data["status"],
            "approved",
        )

    def test_transition_executes_actions(self):
        WorkflowAction.objects.create(
            transition=self.transition,
            name="Set Approved Status",
            action_type="update_record",
            config={
                "field_slug": "status",
                "value": "approved",
            },
        )

        instance = self.start_instance()

        instance = transition_workflow_instance(
            user=self.user,
            instance=instance,
            transition=self.transition,
        )

        self.record.refresh_from_db()

        self.assertEqual(
            instance.status,
            "completed",
        )

        self.assertEqual(
            self.record.data["status"],
            "approved",
        )

    def test_action_create_api(self):
        response = self.client.post(
            "/api/workflow-actions/",
            {
                "transition_id": str(self.transition.id),
                "name": "Audit Approval",
                "action_type": "audit",
                "config": {
                    "message": "Approved",
                },
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["name"],
            "Audit Approval",
        )

        self.assertEqual(
            response.data["action_type"],
            "audit",
        )

    def test_action_list_api(self):
        WorkflowAction.objects.create(
            transition=self.transition,
            name="Audit Approval",
            action_type="audit",
        )

        response = self.client.get(
            "/api/workflow-actions/list/",
            {
                "transition_id": str(self.transition.id),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.data["success"]
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )

    def test_invalid_action_type_api(self):
        response = self.client.post(
            "/api/workflow-actions/",
            {
                "transition_id": str(self.transition.id),
                "name": "Bad Action",
                "action_type": "invalid",
                "config": {},
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_non_member_cannot_create_action(self):
        other_user = User.objects.create_user(
            username="other_action_user",
            password="password123",
        )

        self.client.force_authenticate(other_user)

        response = self.client.post(
            "/api/workflow-actions/",
            {
                "transition_id": str(self.transition.id),
                "name": "Unauthorized",
                "action_type": "audit",
                "config": {},
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_action_order_uses_position(self):
        first = WorkflowAction.objects.create(
            transition=self.transition,
            name="First",
            action_type="audit",
            position=1,
        )

        second = WorkflowAction.objects.create(
            transition=self.transition,
            name="Second",
            action_type="audit",
            position=2,
        )

        actions = list(
            self.transition.actions.filter(
                is_active=True,
            ).order_by(
                "position",
                "created_at",
            )
        )

        self.assertEqual(actions[0].id, first.id)
        self.assertEqual(actions[1].id, second.id)

    def test_update_record_requires_field_slug(self):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Broken Update",
            action_type="update_record",
            config={
                "value": "approved",
            },
        )

        instance = self.start_instance()

        with self.assertRaisesMessage(
            ValueError,
            "update_record action requires field_slug.",
        ):
            execute_workflow_action(
                action=action,
                instance=instance,
                user=self.user,
            )
