from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import (
    Business,
    EntityDefinition,
    EntityRecord,
    WorkflowAction,
    WorkflowDefinition,
    WorkflowHistory,
    WorkflowStep,
    WorkflowTransition,
)
from core.services.workflow_engine import (
    advance_workflow,
    cancel_workflow,
    resume_workflow,
    select_transition,
)


class WorkflowEngineTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="engine-user",
            password="testpass123",
        )

        self.business = Business.objects.create(
            name="Engine Test Business",
            slug="engine-test-business",
        )

        self.entity = EntityDefinition.objects.create(
            business=self.business,
            name="Order",
            slug="order",
        )

        self.record = EntityRecord.objects.create(
            entity=self.entity,
            data={"amount": 5000},
            created_by=self.user,
        )

        self.workflow = WorkflowDefinition.objects.create(
            business=self.business,
            entity=self.entity,
            name="Order Workflow",
            slug="order-workflow",
        )

        self.initial = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Pending",
            slug="pending",
            is_initial=True,
        )

        self.approved = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Approved",
            slug="approved",
            is_final=True,
            position=2,
        )

        self.transition = WorkflowTransition.objects.create(
            workflow=self.workflow,
            from_step=self.initial,
            to_step=self.approved,
            name="Approve",
            slug="approve",
        )

        self.instance = self.workflow.instances.create(
            record=self.record,
            current_step=self.initial,
            started_by=self.user,
            status="active",
        )

    def test_select_transition_returns_matching_transition(self):
        selected = select_transition(
            instance=self.instance,
        )

        self.assertEqual(
            selected.pk,
            self.transition.pk,
        )

    def test_select_transition_returns_none_when_inactive(self):
        self.transition.is_active = False
        self.transition.save(update_fields=["is_active"])

        selected = select_transition(
            instance=self.instance,
        )

        self.assertIsNone(selected)

    def test_advance_workflow_completes_final_step(self):
        result = advance_workflow(
            user=self.user,
            instance=self.instance,
        )

        self.instance.refresh_from_db()

        self.assertTrue(result["success"])
        self.assertTrue(result["transitioned"])
        self.assertTrue(result["completed"])
        self.assertEqual(
            self.instance.status,
            "completed",
        )
        self.assertEqual(
            self.instance.current_step_id,
            self.approved.pk,
        )

        self.assertTrue(
            WorkflowHistory.objects.filter(
                instance=self.instance,
                action="completed",
            ).exists()
        )

    def test_advance_workflow_waits_when_no_transition_matches(self):
        self.transition.is_active = False
        self.transition.save(update_fields=["is_active"])

        result = advance_workflow(
            user=self.user,
            instance=self.instance,
        )

        self.instance.refresh_from_db()

        self.assertTrue(result["success"])
        self.assertTrue(result["waiting"])
        self.assertEqual(
            self.instance.status,
            "active",
        )

    def test_cancel_workflow(self):
        instance = cancel_workflow(
            user=self.user,
            instance=self.instance,
            reason="Customer requested cancellation.",
        )

        self.assertEqual(
            instance.status,
            "cancelled",
        )
        self.assertIsNotNone(
            instance.completed_at,
        )

        self.assertTrue(
            WorkflowHistory.objects.filter(
                instance=instance,
                action="cancelled",
            ).exists()
        )

    def test_resume_workflow(self):
        cancel_workflow(
            user=self.user,
            instance=self.instance,
            reason="Temporary cancellation.",
        )

        instance = resume_workflow(
            user=self.user,
            instance=self.instance,
        )

        self.assertEqual(
            instance.status,
            "active",
        )
        self.assertIsNone(
            instance.completed_at,
        )

        self.assertTrue(
            WorkflowHistory.objects.filter(
                instance=instance,
                action="resumed",
            ).exists()
        )

    def test_cancel_completed_workflow_fails(self):
        self.instance.status = "completed"
        self.instance.save(update_fields=["status"])

        with self.assertRaises(ValueError):
            cancel_workflow(
                user=self.user,
                instance=self.instance,
            )

    def test_resume_active_workflow_fails(self):
        with self.assertRaises(ValueError):
            resume_workflow(
                user=self.user,
                instance=self.instance,
            )
