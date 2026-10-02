from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from core.models import (
    AuditLog,
    Business,
    EntityDefinition,
    EntityRecord,
    FieldDefinition,
    Membership,
    Permission,
    Role,
    RolePermission,
)

User = get_user_model()


class EntityRecordUpdateAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="updateuser",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        self.business = Business.objects.create(
            name="Update Business",
            slug="update-business",
            is_active=True,
        )

        self.other_business = Business.objects.create(
            name="Other Business",
            slug="other-business",
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

        self.name_field = FieldDefinition.objects.create(
            entity=self.entity,
            name="Name",
            slug="name",
            field_type="text",
            required=True,
            position=1,
        )

        self.email_field = FieldDefinition.objects.create(
            entity=self.entity,
            name="Email",
            slug="email",
            field_type="email",
            required=False,
            position=2,
        )

        self.other_name_field = FieldDefinition.objects.create(
            entity=self.other_entity,
            name="Name",
            slug="name",
            field_type="text",
            required=True,
            position=1,
        )

        self.view_permission = Permission.objects.create(
            code="entity.view",
            name="View Entity",
            resource="entity",
            action="view",
        )

        self.update_permission = Permission.objects.create(
            code="entity.update",
            name="Update Entity",
            resource="entity",
            action="update",
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
            permission=self.update_permission,
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
            permission=self.update_permission,
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
                "name": "Old Name",
                "email": "old@example.com",
            },
            created_by=self.user,
        )

        self.other_record = EntityRecord.objects.create(
            entity=self.other_entity,
            data={
                "name": "Other Name",
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

    def test_authorized_patch_updates_only_supplied_fields(self):
        self.authenticate()

        response = self.client.patch(
            self.url,
            {
                "data": {
                    "name": "Updated Name",
                }
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.record.refresh_from_db()

        self.assertEqual(
            self.record.data["name"],
            "Updated Name",
        )

        self.assertEqual(
            self.record.data["email"],
            "old@example.com",
        )

        self.assertEqual(
            response.data["record"]["data"]["name"],
            "Updated Name",
        )

    def test_invalid_dynamic_field_value_returns_400(self):
        self.authenticate()

        response = self.client.patch(
            self.url,
            {
                "data": {
                    "email": "not-an-email",
                }
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.record.refresh_from_db()

        self.assertEqual(
            self.record.data["email"],
            "old@example.com",
        )

    def test_required_field_cannot_be_cleared(self):
        self.authenticate()

        response = self.client.patch(
            self.url,
            {
                "data": {
                    "name": "",
                }
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.record.refresh_from_db()

        self.assertEqual(
            self.record.data["name"],
            "Old Name",
        )

    def test_cross_business_record_is_forbidden(self):
        self.authenticate()

        url = (
            f"/api/entity-records/"
            f"{self.other_record.id}/"
        )

        response = self.client.patch(
            url,
            {
                "data": {
                    "name": "Hacked Name",
                }
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.other_record.refresh_from_db()

        self.assertEqual(
            self.other_record.data["name"],
            "Other Name",
        )

    def test_update_permission_is_required(self):
        role_permission = RolePermission.objects.get(
            role=self.role,
            permission=self.update_permission,
        )

        role_permission.delete()

        self.authenticate()

        response = self.client.patch(
            self.url,
            {
                "data": {
                    "name": "Unauthorized Update",
                }
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.record.refresh_from_db()

        self.assertEqual(
            self.record.data["name"],
            "Old Name",
        )

    def test_update_creates_audit_log(self):
        self.authenticate()

        response = self.client.patch(
            self.url,
            {
                "data": {
                    "name": "Audited Name",
                }
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        audit = AuditLog.objects.filter(
            business=self.business,
            action="record.updated",
            resource="entity_record",
            object_id=str(self.record.id),
        ).first()

        self.assertIsNotNone(audit)

        self.assertEqual(
            audit.user,
            self.user,
        )

        self.assertEqual(
            audit.metadata["old_data"]["name"],
            "Old Name",
        )

        self.assertEqual(
            audit.metadata["new_data"]["name"],
            "Audited Name",
        )
