from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

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
    WorkflowCondition,
    WorkflowAction,
)


class Workflow43CManagementTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="workflow43c",
            password="testpass123",
        )

        self.business = Business.objects.create(
            name="Workflow 43C Business",
            slug="workflow-43c-business",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
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
                name=code,
                resource="workflow",
                action="manage",
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

        self.entity = EntityDefinition.objects.create(
            business=self.business,
            name="Invoice",
            slug="invoice",
        )

        self.workflow = WorkflowDefinition.objects.create(
            business=self.business,
            entity=self.entity,
            name="Invoice Approval",
            slug="invoice-approval",
        )

        self.step1 = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Draft",
            slug="draft",
            position=1,
            is_initial=True,
        )

        self.step2 = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Approved",
            slug="approved",
            position=2,
            is_final=True,
        )

        self.transition = WorkflowTransition.objects.create(
            workflow=self.workflow,
            from_step=self.step1,
            to_step=self.step2,
            name="Approve",
            slug="approve",
        )

        self.condition = WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="amount",
            operator="greater_than",
            value=1000,
        )

        self.action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Approval Audit",
            action_type="audit",
            config={"message": "Invoice approved"},
            position=0,
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_condition_update(self):
        response = self.client.patch(
            f"/api/workflow-conditions/{self.condition.id}/update/",
            {
                "field_slug": "amount",
                "operator": "greater_than_or_equal",
                "value": 5000,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.condition.refresh_from_db()
        self.assertEqual(
            self.condition.operator,
            "greater_than_or_equal",
        )
        self.assertEqual(self.condition.value, 5000)

    def test_condition_deactivate(self):
        response = self.client.patch(
            f"/api/workflow-conditions/{self.condition.id}/deactivate/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.condition.refresh_from_db()
        self.assertFalse(self.condition.is_active)

    def test_condition_delete(self):
        response = self.client.delete(
            f"/api/workflow-conditions/{self.condition.id}/delete/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            WorkflowCondition.objects.filter(
                id=self.condition.id
            ).exists()
        )

    def test_action_update(self):
        response = self.client.patch(
            f"/api/workflow-actions/{self.action.id}/update/",
            {
                "name": "Updated Approval Audit",
                "config": {
                    "message": "Updated message",
                },
                "position": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.action.refresh_from_db()
        self.assertEqual(
            self.action.name,
            "Updated Approval Audit",
        )
        self.assertEqual(self.action.position, 2)

    def test_action_deactivate(self):
        response = self.client.patch(
            f"/api/workflow-actions/{self.action.id}/deactivate/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.action.refresh_from_db()
        self.assertFalse(self.action.is_active)

    def test_action_reorder(self):
        response = self.client.patch(
            f"/api/workflow-actions/{self.action.id}/reorder/",
            {"position": 10},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.action.refresh_from_db()
        self.assertEqual(self.action.position, 10)

    def test_action_delete(self):
        response = self.client.delete(
            f"/api/workflow-actions/{self.action.id}/delete/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            WorkflowAction.objects.filter(
                id=self.action.id
            ).exists()
        )

    def test_condition_requires_manage_permission(self):
        permission = Permission.objects.get(
            code="workflow.manage"
        )
        self.role.role_permissions.filter(
            permission=permission
        ).delete()

        response = self.client.patch(
            f"/api/workflow-conditions/{self.condition.id}/deactivate/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_action_requires_manage_permission(self):
        permission = Permission.objects.get(
            code="workflow.manage"
        )
        self.role.role_permissions.filter(
            permission=permission
        ).delete()

        response = self.client.patch(
            f"/api/workflow-actions/{self.action.id}/deactivate/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 403)


class Workflow43CEdgeCaseTests(Workflow43CManagementTests):

    def test_condition_cannot_deactivate_twice(self):
        url = f"/api/workflow-conditions/{self.condition.id}/deactivate/"

        first = self.client.patch(url, {}, format="json")
        second = self.client.patch(url, {}, format="json")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)

    def test_action_cannot_deactivate_twice(self):
        url = f"/api/workflow-actions/{self.action.id}/deactivate/"

        first = self.client.patch(url, {}, format="json")
        second = self.client.patch(url, {}, format="json")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)

    def test_condition_invalid_operator_rejected(self):
        response = self.client.patch(
            f"/api/workflow-conditions/{self.condition.id}/update/",
            {
                "operator": "invalid_operator",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_action_invalid_type_rejected(self):
        response = self.client.patch(
            f"/api/workflow-actions/{self.action.id}/update/",
            {
                "action_type": "invalid_action",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_action_invalid_config_rejected(self):
        response = self.client.patch(
            f"/api/workflow-actions/{self.action.id}/update/",
            {
                "config": ["not", "an", "object"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_action_negative_position_rejected(self):
        response = self.client.patch(
            f"/api/workflow-actions/{self.action.id}/reorder/",
            {
                "position": -1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_action_missing_position_rejected(self):
        response = self.client.patch(
            f"/api/workflow-actions/{self.action.id}/reorder/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_inactive_workflow_blocks_condition_update(self):
        self.workflow.is_active = False
        self.workflow.save(update_fields=["is_active", "updated_at"])

        response = self.client.patch(
            f"/api/workflow-conditions/{self.condition.id}/update/",
            {
                "field_slug": "amount",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_inactive_workflow_blocks_action_update(self):
        self.workflow.is_active = False
        self.workflow.save(update_fields=["is_active", "updated_at"])

        response = self.client.patch(
            f"/api/workflow-actions/{self.action.id}/update/",
            {
                "name": "Blocked Update",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
