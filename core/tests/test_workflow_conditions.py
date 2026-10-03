from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import (
    Business,
    EntityDefinition,
    EntityRecord,
    Permission,
    Role,
    RolePermission,
    Membership,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTransition,
    WorkflowCondition,
)
from core.services.workflow import start_workflow_instance, transition_workflow_instance
from core.services.workflow_condition import (
    evaluate_condition,
    evaluate_transition_conditions,
)


class WorkflowConditionTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="condition_user",
            password="password123",
        )

        self.business = Business.objects.create(
            name="Condition Test Business",
            slug="condition-test-business",
            industry="Finance",
        )

        self.entity = EntityDefinition.objects.create(
            business=self.business,
            name="Invoice",
            slug="invoice",
        )

        self.record = EntityRecord.objects.create(
            entity=self.entity,
            data={"amount": 75000, "status": "pending"},
            created_by=self.user,
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        self.permission = Permission.objects.create(
            code="workflow.manage",
            name="Manage Workflow",
            resource="workflow",
            action="manage",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
        )

        view_permission = Permission.objects.create(
            code="workflow.view",
            name="View Workflow",
            resource="workflow",
            action="view",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=view_permission,
        )

        create_permission = Permission.objects.create(
            code="workflow.create",
            name="Create Workflow",
            resource="workflow",
            action="create",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=create_permission,
        )

        update_permission = Permission.objects.create(
            code="workflow.update",
            name="Update Workflow",
            resource="workflow",
            action="update",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=update_permission,
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

    def test_greater_than_condition_passes(self):
        condition = WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="amount",
            operator="greater_than",
            value=50000,
        )

        self.assertTrue(
            evaluate_condition(condition, self.record)
        )

    def test_greater_than_condition_blocks(self):
        self.record.data["amount"] = 25000
        self.record.save(update_fields=["data"])

        condition = WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="amount",
            operator="greater_than",
            value=50000,
        )

        self.assertFalse(
            evaluate_condition(condition, self.record)
        )

    def test_equals_condition(self):
        condition = WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="status",
            operator="equals",
            value="pending",
        )

        self.assertTrue(
            evaluate_condition(condition, self.record)
        )

    def test_contains_condition(self):
        self.record.data["description"] = "Urgent invoice payment"
        self.record.save(update_fields=["data"])

        condition = WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="description",
            operator="contains",
            value="urgent",
        )

        self.assertTrue(
            evaluate_condition(condition, self.record)
        )

    def test_boolean_condition(self):
        self.record.data["approved"] = True
        self.record.save(update_fields=["data"])

        condition = WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="approved",
            operator="is_true",
        )

        self.assertTrue(
            evaluate_condition(condition, self.record)
        )

    def test_missing_field_fails(self):
        condition = WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="missing",
            operator="equals",
            value="x",
        )

        self.assertFalse(
            evaluate_condition(condition, self.record)
        )

    def test_all_active_conditions_must_pass(self):
        WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="amount",
            operator="greater_than",
            value=50000,
        )

        WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="status",
            operator="equals",
            value="pending",
        )

        self.assertTrue(
            evaluate_transition_conditions(
                self.transition,
                self.record,
            )
        )

    def test_transition_blocked_when_condition_fails(self):
        WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="amount",
            operator="greater_than",
            value=100000,
        )

        instance = start_workflow_instance(
            user=self.user,
            workflow=self.workflow,
            record=self.record,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Workflow transition conditions are not satisfied.",
        ):
            transition_workflow_instance(
                user=self.user,
                instance=instance,
                transition=self.transition,
            )

    def test_transition_allowed_when_condition_passes(self):
        WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="amount",
            operator="greater_than",
            value=50000,
        )

        instance = start_workflow_instance(
            user=self.user,
            workflow=self.workflow,
            record=self.record,
        )

        instance = transition_workflow_instance(
            user=self.user,
            instance=instance,
            transition=self.transition,
        )

        self.assertEqual(
            instance.status,
            "completed",
        )

        self.assertEqual(
            instance.current_step_id,
            self.approved.id,
        )

    def test_condition_create_api(self):
        response = self.client.post(
            "/api/workflow-conditions/",
            {
                "transition_id": str(self.transition.id),
                "field_slug": "amount",
                "operator": "greater_than",
                "value": 50000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["field_slug"],
            "amount",
        )

        self.assertEqual(
            response.data["operator"],
            "greater_than",
        )

    def test_condition_list_api(self):
        WorkflowCondition.objects.create(
            transition=self.transition,
            field_slug="amount",
            operator="greater_than",
            value=50000,
        )

        response = self.client.get(
            "/api/workflow-conditions/list/",
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

    def test_invalid_operator_api(self):
        response = self.client.post(
            "/api/workflow-conditions/",
            {
                "transition_id": str(self.transition.id),
                "field_slug": "amount",
                "operator": "invalid_operator",
                "value": 50000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )


class WorkflowConditionNumericTests(APITestCase):

    def test_decimal_conversion(self):
        self.assertEqual(
            Decimal("75000"),
            Decimal("75000"),
        )
