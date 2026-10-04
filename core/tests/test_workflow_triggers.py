
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import (
    AuditLog,
    Business,
    EntityDefinition,
    EntityRecord,
    Membership,
    Permission,
    Role,
    RolePermission,
    WorkflowDefinition,
    WorkflowHistory,
    WorkflowInstance,
    WorkflowStep,
    WorkflowTransition,
    WorkflowTrigger,
)


class WorkflowTriggerTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="trigger-user",
            password="testpass123",
        )

        self.business = Business.objects.create(
            name="Trigger Business",
            slug="trigger-business",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        for code, action in (
            ("workflow.view", "view"),
            ("workflow.manage", "manage"),
        ):
            permission = Permission.objects.create(
                code=code,
                name=code,
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

        self.step = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Draft",
            slug="draft",
            position=1,
            is_initial=True,
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def create_trigger(self):
        return WorkflowTrigger.objects.create(
            workflow=self.workflow,
            name="On Invoice Created",
            event_type="record_created",
            config={"source": "test"},
        )

    def test_record_created_starts_workflow(self):
        from core.services.record import create_record_for_entity

        trigger = self.create_trigger()

        permission = Permission.objects.create(
            code="entity.create",
            name="entity.create",
            resource="entity",
            action="create",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=permission,
        )

        with self.captureOnCommitCallbacks(execute=True):
            record = create_record_for_entity(
                user=self.user,
                entity=self.entity,
                data={},
            )

        instance = WorkflowInstance.objects.get(
            workflow=self.workflow,
            record=record,
        )

        self.assertEqual(
            instance.current_step,
            self.step,
        )
        self.assertEqual(
            instance.status,
            "active",
        )

        history = WorkflowHistory.objects.get(
            instance=instance,
            action="started",
        )

        self.assertEqual(
            history.to_step,
            self.step,
        )
        self.assertEqual(
            history.performed_by,
            self.user,
        )

        audit = AuditLog.objects.get(
            business=self.business,
            action="workflow.trigger.fired",
            object_id=str(record.id),
        )

        self.assertEqual(
            audit.user,
            self.user,
        )
        self.assertEqual(
            audit.metadata["trigger_id"],
            str(trigger.id),
        )

    def test_record_created_does_not_duplicate_workflow_instance(self):
        from core.services.record import create_record_for_entity

        self.create_trigger()

        permission = Permission.objects.create(
            code="entity.create",
            name="entity.create",
            resource="entity",
            action="create",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=permission,
        )

        with self.captureOnCommitCallbacks(execute=True):
            record = create_record_for_entity(
                user=self.user,
                entity=self.entity,
                data={},
            )

        self.assertEqual(
            WorkflowInstance.objects.filter(
                workflow=self.workflow,
                record=record,
            ).count(),
            1,
        )

        from core.services.workflow_event import dispatch_record_event

        summary = dispatch_record_event(
            record,
            "record_created",
            user=self.user,
        )

        self.assertEqual(
            summary["started"],
            0,
        )
        self.assertEqual(
            summary["skipped"],
            1,
        )

        self.assertEqual(
            WorkflowInstance.objects.filter(
                workflow=self.workflow,
                record=record,
            ).count(),
            1,
        )

    def test_inactive_trigger_does_not_start_workflow(self):
        from core.services.record import create_record_for_entity

        trigger = self.create_trigger()
        trigger.is_active = False
        trigger.save(update_fields=["is_active"])

        permission = Permission.objects.create(
            code="entity.create",
            name="entity.create",
            resource="entity",
            action="create",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=permission,
        )

        with self.captureOnCommitCallbacks(execute=True):
            record = create_record_for_entity(
                user=self.user,
                entity=self.entity,
                data={},
            )

        self.assertFalse(
            WorkflowInstance.objects.filter(
                workflow=self.workflow,
                record=record,
            ).exists()
        )

        self.assertFalse(
            AuditLog.objects.filter(
                business=self.business,
                action="workflow.trigger.fired",
                object_id=str(record.id),
            ).exists()
        )

    def test_trigger_config_field_equals_condition(self):
        from core.services.record import create_record_for_entity
        from core.services.workflow_event import dispatch_record_event

        trigger = WorkflowTrigger.objects.create(
            workflow=self.workflow,
            name="Approved Invoice Trigger",
            event_type="record_created",
            config={
                "field": "status",
                "equals": "approved",
            },
        )

        permission = Permission.objects.create(
            code="entity.create",
            name="entity.create",
            resource="entity",
            action="create",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=permission,
        )

        with self.captureOnCommitCallbacks(execute=True):
            record = create_record_for_entity(
                user=self.user,
                entity=self.entity,
                data={},
            )

        self.assertFalse(
            WorkflowInstance.objects.filter(
                workflow=self.workflow,
                record=record,
            ).exists()
        )

        record.data = {
            "status": "approved",
        }

        summary = dispatch_record_event(
            record,
            "record_created",
            user=self.user,
        )

        self.assertEqual(
            summary["started"],
            1,
        )

        self.assertTrue(
            WorkflowInstance.objects.filter(
                workflow=self.workflow,
                record=record,
            ).exists()
        )

        self.assertTrue(
            AuditLog.objects.filter(
                business=self.business,
                action="workflow.trigger.fired",
                object_id=str(record.id),
                metadata__trigger_id=str(trigger.id),
            ).exists()
        )

    def test_record_updated_starts_workflow(self):
        from core.services.record import create_record_for_entity
        from core.services.workflow_event import dispatch_record_event

        trigger = WorkflowTrigger.objects.create(
            workflow=self.workflow,
            name="On Invoice Updated",
            event_type="record_updated",
        )

        permission = Permission.objects.create(
            code="entity.create",
            name="entity.create",
            resource="entity",
            action="create",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=permission,
        )

        with self.captureOnCommitCallbacks(execute=True):
            record = create_record_for_entity(
                user=self.user,
                entity=self.entity,
                data={},
            )

        self.assertFalse(
            WorkflowInstance.objects.filter(
                workflow=self.workflow,
                record=record,
            ).exists()
        )

        summary = dispatch_record_event(
            record,
            "record_updated",
            user=self.user,
        )

        self.assertEqual(
            summary["started"],
            1,
        )

        instance = WorkflowInstance.objects.get(
            workflow=self.workflow,
            record=record,
        )

        self.assertEqual(
            instance.current_step,
            self.step,
        )

        self.assertTrue(
            WorkflowHistory.objects.filter(
                instance=instance,
                action="started",
                performed_by=self.user,
            ).exists()
        )

        self.assertTrue(
            AuditLog.objects.filter(
                business=self.business,
                action="workflow.trigger.fired",
                object_id=str(record.id),
                metadata__trigger_id=str(trigger.id),
            ).exists()
        )

    def test_record_deleted_starts_workflow(self):
        from core.services.record import create_record_for_entity
        from core.services.workflow_event import dispatch_record_event

        trigger = WorkflowTrigger.objects.create(
            workflow=self.workflow,
            name="On Invoice Deleted",
            event_type="record_deleted",
        )

        permission = Permission.objects.create(
            code="entity.create",
            name="entity.create",
            resource="entity",
            action="create",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=permission,
        )

        with self.captureOnCommitCallbacks(execute=True):
            record = create_record_for_entity(
                user=self.user,
                entity=self.entity,
                data={},
            )

        summary = dispatch_record_event(
            record,
            "record_deleted",
            user=self.user,
        )

        self.assertEqual(
            summary["started"],
            1,
        )

        instance = WorkflowInstance.objects.get(
            workflow=self.workflow,
            record=record,
        )

        self.assertEqual(
            instance.current_step,
            self.step,
        )

        self.assertTrue(
            WorkflowHistory.objects.filter(
                instance=instance,
                action="started",
                performed_by=self.user,
            ).exists()
        )

        self.assertTrue(
            AuditLog.objects.filter(
                business=self.business,
                action="workflow.trigger.fired",
                object_id=str(record.id),
                metadata__trigger_id=str(trigger.id),
            ).exists()
        )

    def test_broken_trigger_does_not_block_valid_trigger(self):
        from core.services.record import create_record_for_entity
        from core.services.workflow_event import dispatch_record_event

        broken_workflow = WorkflowDefinition.objects.create(
            business=self.business,
            entity=self.entity,
            name="Broken Workflow",
            slug="broken-workflow",
        )

        broken_trigger = WorkflowTrigger.objects.create(
            workflow=broken_workflow,
            name="Broken Trigger",
            event_type="record_created",
        )

        WorkflowTrigger.objects.create(
            workflow=self.workflow,
            name="Valid Trigger",
            event_type="record_created",
        )

        permission = Permission.objects.create(
            code="entity.create",
            name="entity.create",
            resource="entity",
            action="create",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=permission,
        )

        with self.captureOnCommitCallbacks(execute=False):
            record = create_record_for_entity(
                user=self.user,
                entity=self.entity,
                data={},
            )

        self.assertFalse(
            WorkflowInstance.objects.filter(
                record=record,
            ).exists()
        )

        summary = dispatch_record_event(
            record,
            "record_created",
            user=self.user,
        )

        self.assertEqual(
            summary["failed"],
            1,
        )

        self.assertEqual(
            summary["started"],
            1,
        )

        self.assertTrue(
            WorkflowInstance.objects.filter(
                workflow=self.workflow,
                record=record,
            ).exists()
        )

        self.assertTrue(
            any(
                error["trigger_id"] == str(broken_trigger.id)
                for error in summary["errors"]
            )
        )

    def test_create_trigger_api(self):
        response = self.client.post(
            "/api/workflow-triggers/",
            {
                "workflow_id": str(self.workflow.id),
                "name": "Invoice Created",
                "event_type": "record_created",
                "config": {
                    "source": "api",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            WorkflowTrigger.objects.count(),
            1,
        )

    def test_list_triggers_api(self):
        trigger = self.create_trigger()

        response = self.client.get(
            f"/api/workflow-triggers/list/?workflow_id={self.workflow.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.data["results"]),
            1,
        )
        self.assertEqual(
            response.data["results"][0]["id"],
            str(trigger.id),
        )

    def test_update_trigger_api(self):
        trigger = self.create_trigger()

        response = self.client.patch(
            f"/api/workflow-triggers/{trigger.id}/update/",
            {
                "name": "Updated Trigger",
                "event_type": "record_updated",
                "config": {"field": "status"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        trigger.refresh_from_db()

        self.assertEqual(
            trigger.name,
            "Updated Trigger",
        )
        self.assertEqual(
            trigger.event_type,
            "record_updated",
        )

    def test_deactivate_trigger_api(self):
        trigger = self.create_trigger()

        response = self.client.patch(
            f"/api/workflow-triggers/{trigger.id}/deactivate/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        trigger.refresh_from_db()

        self.assertFalse(trigger.is_active)

    def test_deactivate_twice_rejected(self):
        trigger = self.create_trigger()

        url = (
            f"/api/workflow-triggers/"
            f"{trigger.id}/deactivate/"
        )

        first = self.client.patch(url, {}, format="json")
        second = self.client.patch(url, {}, format="json")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)

    def test_delete_trigger_api(self):
        trigger = self.create_trigger()

        response = self.client.delete(
            f"/api/workflow-triggers/{trigger.id}/delete/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            WorkflowTrigger.objects.filter(
                id=trigger.id,
            ).exists()
        )

    def test_invalid_event_type_rejected(self):
        response = self.client.post(
            "/api/workflow-triggers/",
            {
                "workflow_id": str(self.workflow.id),
                "name": "Invalid Trigger",
                "event_type": "something_invalid",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_config_rejected(self):
        response = self.client.post(
            "/api/workflow-triggers/",
            {
                "workflow_id": str(self.workflow.id),
                "name": "Invalid Config",
                "event_type": "record_created",
                "config": ["invalid"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_empty_name_rejected(self):
        response = self.client.post(
            "/api/workflow-triggers/",
            {
                "workflow_id": str(self.workflow.id),
                "name": "",
                "event_type": "record_created",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_missing_workflow_rejected(self):
        response = self.client.post(
            "/api/workflow-triggers/",
            {
                "name": "Trigger",
                "event_type": "record_created",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_inactive_trigger_hidden_from_list(self):
        trigger = self.create_trigger()
        trigger.is_active = False
        trigger.save(update_fields=["is_active"])

        response = self.client.get(
            f"/api/workflow-triggers/list/?workflow_id={self.workflow.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.data["results"]),
            0,
        )

    def test_inactive_workflow_blocks_create(self):
        self.workflow.is_active = False
        self.workflow.save(update_fields=["is_active"])

        response = self.client.post(
            "/api/workflow-triggers/",
            {
                "workflow_id": str(self.workflow.id),
                "name": "Blocked",
                "event_type": "record_created",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_manage_permission_required(self):
        RolePermission.objects.filter(
            role=self.role,
        ).delete()

        response = self.client.post(
            "/api/workflow-triggers/",
            {
                "workflow_id": str(self.workflow.id),
                "name": "Blocked",
                "event_type": "record_created",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_view_permission_required_for_list(self):
        RolePermission.objects.filter(
            role=self.role,
        ).delete()

        response = self.client.get(
            f"/api/workflow-triggers/list/?workflow_id={self.workflow.id}"
        )

        self.assertEqual(response.status_code, 403)

    def test_non_member_cannot_manage(self):
        other = get_user_model().objects.create_user(
            username="other-trigger-user",
            password="testpass123",
        )

        self.client.force_authenticate(user=other)

        response = self.client.post(
            "/api/workflow-triggers/",
            {
                "workflow_id": str(self.workflow.id),
                "name": "Blocked",
                "event_type": "record_created",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_delete_missing_trigger(self):
        import uuid

        response = self.client.delete(
            f"/api/workflow-triggers/{uuid.uuid4()}/delete/"
        )

        self.assertEqual(response.status_code, 404)

    def test_update_invalid_event_type(self):
        trigger = self.create_trigger()

        response = self.client.patch(
            f"/api/workflow-triggers/{trigger.id}/update/",
            {
                "event_type": "invalid",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_update_invalid_config(self):
        trigger = self.create_trigger()

        response = self.client.patch(
            f"/api/workflow-triggers/{trigger.id}/update/",
            {
                "config": ["invalid"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
