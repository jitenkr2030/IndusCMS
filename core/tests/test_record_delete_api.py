from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from core.models import (
    AuditLog,
    Business,
    EntityDefinition,
    EntityRecord,
    Membership,
    Permission,
    Role,
    RolePermission,
)

User = get_user_model()


class EntityRecordDeleteAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="deleteuser",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="otherdeleteuser",
            password="testpass123",
        )

        self.business = Business.objects.create(
            name="Delete Business",
            slug="delete-business",
            is_active=True,
        )

        self.other_business = Business.objects.create(
            name="Other Delete Business",
            slug="other-delete-business",
            is_active=True,
        )

        self.entity = EntityDefinition.objects.create(
            business=self.business,
            name="Customer",
            slug="customer",
            is_active=True,
        )

        self.other_entity = EntityDefinition.objects.create(
            business=self.other_business,
            name="Customer",
            slug="customer",
            is_active=True,
        )

        self.view_permission = Permission.objects.create(
            code="entity.view",
            name="View Entity",
            resource="entity",
            action="view",
        )

        self.delete_permission = Permission.objects.create(
            code="entity.delete",
            name="Delete Entity",
            resource="entity",
            action="delete",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Manager",
            slug="manager",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.view_permission,
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.delete_permission,
        )

        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=self.role,
            is_active=True,
        )

        self.other_role = Role.objects.create(
            business=self.other_business,
            name="Manager",
            slug="manager",
        )

        RolePermission.objects.create(
            role=self.other_role,
            permission=self.view_permission,
        )

        RolePermission.objects.create(
            role=self.other_role,
            permission=self.delete_permission,
        )

        Membership.objects.create(
            user=self.other_user,
            business=self.other_business,
            role=self.other_role,
            is_active=True,
        )

        self.record = EntityRecord.objects.create(
            entity=self.entity,
            data={
                "name": "Delete Me",
            },
            created_by=self.user,
        )

        self.other_record = EntityRecord.objects.create(
            entity=self.other_entity,
            data={
                "name": "Other Record",
            },
            created_by=self.other_user,
        )

        self.url = (
            f"/api/entity-records/{self.record.id}/"
        )

    def authenticate(self):
        self.client.force_authenticate(
            user=self.user
        )

    def test_authorized_delete_soft_deletes_record(self):
        self.authenticate()

        response = self.client.delete(
            self.url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.record.refresh_from_db()

        self.assertTrue(
            self.record.is_deleted
        )

        self.assertIsNotNone(
            self.record.deleted_at
        )

        self.assertEqual(
            self.record.deleted_by,
            self.user,
        )

        self.assertTrue(
            response.data["success"]
        )

    def test_deleted_record_remains_in_database(self):
        self.authenticate()

        response = self.client.delete(
            self.url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            EntityRecord.objects.filter(
                id=self.record.id
            ).exists()
        )

        self.assertTrue(
            EntityRecord.objects.get(
                id=self.record.id
            ).is_deleted
        )

    def test_already_deleted_record_cannot_be_deleted_again(self):
        self.authenticate()

        self.record.is_deleted = True
        self.record.deleted_by = self.user
        self.record.save(
            update_fields=[
                "is_deleted",
                "deleted_by",
            ]
        )

        response = self.client.delete(
            self.url
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "already been deleted",
            response.data["message"],
        )

    def test_cross_business_record_is_forbidden(self):
        self.authenticate()

        url = (
            f"/api/entity-records/"
            f"{self.other_record.id}/"
        )

        response = self.client.delete(
            url
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.other_record.refresh_from_db()

        self.assertFalse(
            self.other_record.is_deleted
        )

    def test_delete_permission_is_required(self):
        role_permission = RolePermission.objects.get(
            role=self.role,
            permission=self.delete_permission,
        )

        role_permission.delete()

        self.authenticate()

        response = self.client.delete(
            self.url
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.record.refresh_from_db()

        self.assertFalse(
            self.record.is_deleted
        )

    def test_delete_creates_audit_log(self):
        self.authenticate()

        response = self.client.delete(
            self.url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        audit = AuditLog.objects.filter(
            business=self.business,
            action="record.deleted",
            resource="entity_record",
            object_id=str(self.record.id),
        ).first()

        self.assertIsNotNone(
            audit
        )

        self.assertEqual(
            audit.user,
            self.user,
        )

        self.assertEqual(
            audit.metadata["record_id"],
            str(self.record.id),
        )
