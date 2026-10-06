from unittest.mock import patch, MagicMock
from datetime import timedelta
from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from django.utils import timezone
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
    WorkflowActionExecution,
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

    @patch("core.services.workflow_action.build_opener")
    def test_webhook_action_executes_successfully(
        self,
        mock_build_opener,
    ):
        response = MagicMock()
        response.status = 200
        response.read.return_value = b'{"ok": true}'

        mock_opener = MagicMock()
        mock_opener.open.return_value.__enter__.return_value = response
        mock_build_opener.return_value = mock_opener

        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Notify ERP",
            action_type="webhook",
            config={
                "url": "https://example.com/webhook",
                "method": "POST",
                "payload": {
                    "event": "invoice.approved",
                    "amount": 75000,
                },
            },
        )

        instance = self.start_instance()

        result = execute_workflow_action(
            action=action,
            instance=instance,
            user=self.user,
        )

        self.assertTrue(result["success"])
        self.assertEqual(
            result["action"],
            "webhook",
        )
        self.assertTrue(
            result["delivered"]
        )
        self.assertEqual(
            result["status_code"],
            200,
        )

        mock_build_opener.return_value.open.assert_called_once()

        request = mock_build_opener.return_value.open.call_args.args[0]

        self.assertEqual(
            request.full_url,
            "https://example.com/webhook",
        )
        self.assertEqual(
            request.get_method(),
            "POST",
        )

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

    def test_action_execution_record_is_persisted(self):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Audit Execution",
            action_type="audit",
            config={
                "message": "Execution persisted",
            },
        )

        instance = self.start_instance()

        results = execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        self.assertEqual(
            len(results),
            1,
        )

        execution = (
            WorkflowActionExecution.objects.get(
                workflow_instance=instance,
                workflow_action=action,
            )
        )

        self.assertEqual(
            execution.status,
            "success",
        )

        self.assertIsNotNone(
            execution.started_at
        )

        self.assertIsNotNone(
            execution.completed_at
        )

        self.assertTrue(
            execution.result["success"]
        )

    def test_failed_action_does_not_block_next_action(
        self,
    ):
        broken = WorkflowAction.objects.create(
            transition=self.transition,
            name="Broken Update",
            action_type="update_record",
            config={
                "value": "approved",
            },
            position=1,
        )

        valid = WorkflowAction.objects.create(
            transition=self.transition,
            name="Valid Update",
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

        self.assertEqual(
            len(results),
            2,
        )

        self.assertTrue(
            results[0]["failed"]
        )

        self.assertTrue(
            results[1]["success"]
        )

        self.record.refresh_from_db()

        self.assertEqual(
            self.record.data["status"],
            "approved",
        )

        failed_execution = (
            WorkflowActionExecution.objects.get(
                workflow_instance=instance,
                workflow_action=broken,
            )
        )

        successful_execution = (
            WorkflowActionExecution.objects.get(
                workflow_instance=instance,
                workflow_action=valid,
            )
        )

        self.assertEqual(
            failed_execution.status,
            "failed",
        )

        self.assertTrue(
            failed_execution.error
        )

        self.assertEqual(
            successful_execution.status,
            "success",
        )

    def test_inactive_action_is_not_executed_by_transition(
        self,
    ):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Inactive Audit",
            action_type="audit",
            is_active=False,
        )

        instance = self.start_instance()

        results = execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        self.assertEqual(
            results,
            [],
        )

        self.assertEqual(
            WorkflowActionExecution.objects.filter(
                workflow_instance=instance,
                workflow_action=action,
            ).count(),
            0,
        )

    @patch("core.services.workflow_action.urlopen")
    def test_webhook_invalid_url_is_recorded_as_failed(
        self,
        mock_urlopen,
    ):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Invalid Webhook",
            action_type="webhook",
            config={
                "url": "ftp://example.com/hook",
            },
        )

        instance = self.start_instance()

        results = execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertTrue(
            results[0]["failed"]
        )

        execution = (
            WorkflowActionExecution.objects.get(
                workflow_instance=instance,
                workflow_action=action,
            )
        )

        self.assertEqual(
            execution.status,
            "failed",
        )

        self.assertIn(
            "http or https",
            execution.error,
        )

        mock_urlopen.assert_not_called()

    @patch("core.services.workflow_action.build_opener")
    def test_webhook_http_failure_is_recorded(
        self,
        mock_build_opener,
    ):
        from urllib.error import HTTPError

        mock_opener = MagicMock()

        mock_opener.open.side_effect = HTTPError(
            url="https://example.com/hook",
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=MagicMock(
                read=lambda limit: b"server failed"
            ),
        )

        mock_build_opener.return_value = mock_opener

        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Failing Webhook",
            action_type="webhook",
            config={
                "url": "https://example.com/hook",
            },
        )

        instance = self.start_instance()

        results = execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertTrue(
            results[0]["failed"]
        )

        execution = (
            WorkflowActionExecution.objects.get(
                workflow_instance=instance,
                workflow_action=action,
            )
        )

        self.assertEqual(
            execution.status,
            "failed",
        )

        self.assertIn(
            "HTTP 500",
            execution.error,
        )

    def test_notification_execution_stores_result(
        self,
    ):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Notify Manager",
            action_type="notification",
            config={
                "recipient": "manager",
                "message": "Invoice approved.",
                "channel": "in_app",
            },
        )

        instance = self.start_instance()

        execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        execution = (
            WorkflowActionExecution.objects.get(
                workflow_instance=instance,
                workflow_action=action,
            )
        )

        self.assertEqual(
            execution.status,
            "success",
        )

        self.assertEqual(
            execution.result["action"],
            "notification",
        )

        self.assertEqual(
            execution.result["recipient"],
            "manager",
        )

        self.assertEqual(
            execution.result["channel"],
            "in_app",
        )

    def test_multiple_execution_records_are_created(
        self,
    ):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Audit",
            action_type="audit",
        )

        instance = self.start_instance()

        execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        self.assertEqual(
            WorkflowActionExecution.objects.filter(
                workflow_instance=instance,
                workflow_action=action,
            ).count(),
            2,
        )


class WorkflowActionExecutionTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="execution_user",
            password="password123",
        )

        self.business = Business.objects.create(
            name="Execution Test Business",
            slug="execution-test-business",
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
                "amount": 5000,
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
            name="Execution Workflow",
            slug="execution-workflow",
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
            name="Approve",
            slug="approve",
        )

        self.action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Audit Action",
            action_type="audit",
            config={
                "message": "Execution test",
            },
        )

        self.client.force_authenticate(self.user)

    def start_instance(self):
        return start_workflow_instance(
            user=self.user,
            workflow=self.workflow,
            record=self.record,
        )

    def create_execution(self, status="success"):
        instance = self.start_instance()

        return WorkflowActionExecution.objects.create(
            workflow_instance=instance,
            workflow_action=self.action,
            status=status,
            result={
                "action": "audit",
            },
        )

    def test_execution_list_requires_workflow_instance_id(self):
        response = self.client.get(
            "/api/workflow-action-executions/"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "workflow_instance_id",
            response.data["detail"],
        )

    def test_execution_list_api(self):
        execution = self.create_execution()

        response = self.client.get(
            "/api/workflow-action-executions/",
            {
                "workflow_instance_id": str(
                    execution.workflow_instance_id
                ),
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

        self.assertEqual(
            response.data["results"][0]["id"],
            str(execution.pk),
        )

    def test_execution_detail_api(self):
        execution = self.create_execution()

        response = self.client.get(
            f"/api/workflow-action-executions/{execution.pk}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.data["success"]
        )

        self.assertEqual(
            response.data["result"]["id"],
            str(execution.pk),
        )

        self.assertEqual(
            response.data["result"]["action_name"],
            "Audit Action",
        )

    def test_execution_detail_not_found(self):
        import uuid

        response = self.client.get(
            f"/api/workflow-action-executions/{uuid.uuid4()}/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_execution_list_requires_permission(self):
        execution = self.create_execution()

        Permission.objects.filter(
            code="workflow.view"
        ).delete()

        response = self.client.get(
            "/api/workflow-action-executions/",
            {
                "workflow_instance_id": str(
                    execution.workflow_instance_id
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_execution_detail_requires_permission(self):
        execution = self.create_execution()

        Permission.objects.filter(
            code="workflow.view"
        ).delete()

        response = self.client.get(
            f"/api/workflow-action-executions/{execution.pk}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_retry_requires_manage_permission(self):
        execution = self.create_execution(
            status="failed"
        )

        Permission.objects.filter(
            code="workflow.manage"
        ).delete()

        response = self.client.post(
            f"/api/workflow-action-executions/{execution.pk}/retry/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_retry_success_reuses_execution(self):
        execution = self.create_execution(
            status="failed"
        )

        execution.error = "Previous failure"
        execution.save(
            update_fields=["error"]
        )

        original_id = execution.pk

        response = self.client.post(
            f"/api/workflow-action-executions/{execution.pk}/retry/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.data["success"]
        )

        execution.refresh_from_db()

        self.assertEqual(
            execution.pk,
            original_id,
        )

        self.assertEqual(
            execution.status,
            "success",
        )

        self.assertEqual(
            execution.retry_count,
            1,
        )

        self.assertIsNotNone(
            execution.last_retry_at
        )

        self.assertIsNone(
            execution.next_retry_at
        )

        self.assertEqual(
            execution.error,
            "",
        )

    def test_retry_failure_schedules_next_retry(self):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Broken Action",
            action_type="invalid",
        )

        instance = self.start_instance()

        execution = WorkflowActionExecution.objects.create(
            workflow_instance=instance,
            workflow_action=action,
            status="failed",
            retry_count=0,
            max_retries=3,
        )

        before = timezone.now()

        response = self.client.post(
            f"/api/workflow-action-executions/{execution.pk}/retry/"
        )

        after = timezone.now()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            response.data["success"]
        )

        execution.refresh_from_db()

        self.assertEqual(
            execution.status,
            "failed",
        )

        self.assertEqual(
            execution.retry_count,
            1,
        )

        self.assertIsNotNone(
            execution.next_retry_at
        )

        self.assertGreaterEqual(
            execution.next_retry_at,
            before + timedelta(seconds=30),
        )

        self.assertLessEqual(
            execution.next_retry_at,
            after + timedelta(seconds=30),
        )

    def test_retry_before_next_retry_at_is_blocked(self):
        action = WorkflowAction.objects.create(
            transition=self.transition,
            name="Retry Later",
            action_type="invalid",
        )

        instance = self.start_instance()

        execution = WorkflowActionExecution.objects.create(
            workflow_instance=instance,
            workflow_action=action,
            status="failed",
            retry_count=1,
            max_retries=3,
            next_retry_at=timezone.now() + timedelta(
                minutes=10
            ),
        )

        response = self.client.post(
            f"/api/workflow-action-executions/{execution.pk}/retry/"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "Retry is not available yet",
            response.data["detail"],
        )

        execution.refresh_from_db()

        self.assertEqual(
            execution.retry_count,
            1,
        )

    def test_max_retry_limit_is_enforced(self):
        execution = self.create_execution(
            status="failed"
        )

        execution.retry_count = 3
        execution.max_retries = 3
        execution.save(
            update_fields=[
                "retry_count",
                "max_retries",
            ]
        )

        response = self.client.post(
            f"/api/workflow-action-executions/{execution.pk}/retry/"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "Maximum retry limit",
            response.data["detail"],
        )

    @patch("core.services.workflow_action.build_opener")
    def test_retry_webhook_uses_idempotency_header(
        self,
        mock_build_opener,
    ):
        from unittest.mock import MagicMock

        mock_opener = MagicMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"ok"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False

        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        webhook = WorkflowAction.objects.create(
            transition=self.transition,
            name="Webhook",
            action_type="webhook",
            config={
                "url": "https://example.com/hook",
            },
        )

        instance = self.start_instance()

        execution = WorkflowActionExecution.objects.create(
            workflow_instance=instance,
            workflow_action=webhook,
            status="failed",
        )

        response = self.client.post(
            f"/api/workflow-action-executions/{execution.pk}/retry/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.data["success"]
        )

        request = mock_opener.open.call_args.args[0]

        header = request.get_header(
            "X-induscms-idempotency-key"
        )

        self.assertTrue(
            header
        )

        self.assertIn(
            str(execution.pk),
            header,
        )

    @patch("core.services.workflow_action.build_opener")
    def test_configured_idempotency_key_is_used(
        self,
        mock_build_opener,
    ):
        mock_opener = MagicMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"ok"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False

        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        webhook = WorkflowAction.objects.create(
            transition=self.transition,
            name="Configured Webhook",
            action_type="webhook",
            config={
                "url": "https://example.com/hook",
                "idempotency_key": "my-fixed-key",
            },
        )

        instance = self.start_instance()

        execution = WorkflowActionExecution.objects.create(
            workflow_instance=instance,
            workflow_action=webhook,
            status="failed",
        )

        response = self.client.post(
            f"/api/workflow-action-executions/{execution.pk}/retry/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        request = mock_opener.open.call_args.args[0]

        self.assertEqual(
            request.get_header(
                "X-induscms-idempotency-key"
            ),
            "my-fixed-key",
        )

    def test_webhook_payload_limit(self):
        from core.services.workflow_action import (
            execute_transition_actions,
        )

        webhook = WorkflowAction.objects.create(
            transition=self.transition,
            name="Large Webhook",
            action_type="webhook",
            config={
                "url": "https://example.com/hook",
                "payload": "x" * (
                    256 * 1024 + 1
                ),
            },
        )

        instance = self.start_instance()

        results = execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        self.assertEqual(
            len(results),
            2,
        )

        failed = [
            item
            for item in results
            if item.get("failed")
        ]

        self.assertEqual(
            len(failed),
            1,
        )

        execution = WorkflowActionExecution.objects.get(
            workflow_instance=instance,
            workflow_action=webhook,
        )

        self.assertEqual(
            execution.status,
            "failed",
        )

        self.assertIn(
            "256 KB",
            execution.error,
        )

    def test_webhook_credentials_are_blocked(self):
        webhook = WorkflowAction.objects.create(
            transition=self.transition,
            name="Credential URL",
            action_type="webhook",
            config={
                "url": "https://user:password@example.com/hook",
            },
        )

        instance = self.start_instance()

        results = execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        execution = WorkflowActionExecution.objects.get(
            workflow_instance=instance,
            workflow_action=webhook,
        )

        self.assertEqual(
            execution.status,
            "failed",
        )

        self.assertIn(
            "credentials",
            execution.error.lower(),
        )

    def test_webhook_localhost_is_blocked(self):
        webhook = WorkflowAction.objects.create(
            transition=self.transition,
            name="Local Webhook",
            action_type="webhook",
            config={
                "url": "http://localhost:8000/hook",
            },
        )

        instance = self.start_instance()

        execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        execution = WorkflowActionExecution.objects.get(
            workflow_instance=instance,
            workflow_action=webhook,
        )

        self.assertEqual(
            execution.status,
            "failed",
        )

        self.assertIn(
            "private",
            execution.error.lower(),
        )

    def test_webhook_loopback_ip_is_blocked(self):
        webhook = WorkflowAction.objects.create(
            transition=self.transition,
            name="Loopback Webhook",
            action_type="webhook",
            config={
                "url": "http://127.0.0.1:8000/hook",
            },
        )

        instance = self.start_instance()

        execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        execution = WorkflowActionExecution.objects.get(
            workflow_instance=instance,
            workflow_action=webhook,
        )

        self.assertEqual(
            execution.status,
            "failed",
        )

        self.assertIn(
            "private",
            execution.error.lower(),
        )

    def test_webhook_private_ip_is_blocked(self):
        webhook = WorkflowAction.objects.create(
            transition=self.transition,
            name="Private Webhook",
            action_type="webhook",
            config={
                "url": "http://192.168.1.10/hook",
            },
        )

        instance = self.start_instance()

        execute_transition_actions(
            transition=self.transition,
            instance=instance,
            user=self.user,
        )

        execution = WorkflowActionExecution.objects.get(
            workflow_instance=instance,
            workflow_action=webhook,
        )

        self.assertEqual(
            execution.status,
            "failed",
        )

        self.assertIn(
            "private",
            execution.error.lower(),
        )

    def test_webhook_redirect_is_blocked(self):
        webhook = WorkflowAction.objects.create(
            transition=self.transition,
            name="Redirect Webhook",
            action_type="webhook",
            config={
                "url": "https://example.com/hook",
            },
        )

        instance = self.start_instance()

        with patch(
            "core.services.workflow_action.build_opener"
        ) as mock_build_opener:

            mock_opener = MagicMock()

            mock_opener.open.side_effect = Exception(
                "redirect should not be followed"
            )

            mock_build_opener.return_value = mock_opener

            execute_transition_actions(
                transition=self.transition,
                instance=instance,
                user=self.user,
            )

        execution = WorkflowActionExecution.objects.get(
            workflow_instance=instance,
            workflow_action=webhook,
        )

        self.assertEqual(
            execution.status,
            "failed",
        )

    def test_execution_serializer_contains_retry_fields(self):
        execution = self.create_execution(
            status="failed"
        )

        execution.retry_count = 2
        execution.max_retries = 5
        execution.next_retry_at = timezone.now()
        execution.last_retry_at = timezone.now()
        execution.save()

        response = self.client.get(
            f"/api/workflow-action-executions/{execution.pk}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        result = response.data["result"]

        self.assertEqual(
            result["retry_count"],
            2,
        )

        self.assertEqual(
            result["max_retries"],
            5,
        )

        self.assertIsNotNone(
            result["next_retry_at"]
        )

        self.assertIsNotNone(
            result["last_retry_at"]
        )
