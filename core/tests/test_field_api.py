from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import (
    AuditLog,
    Business,
    EntityDefinition,
    FieldDefinition,
    Membership,
    Permission,
    Role,
    RolePermission,
)


class FieldCreationAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="fieldtest",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Field Test Business",
            slug="field-test-business",
            industry="retail",
            country="India",
        )

        self.entity = EntityDefinition.objects.create(
            business=self.business,
            name="Customers",
            slug="customers",
            description="Customer records",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        self.permission = Permission.objects.create(
            code="entity.manage",
            name="Manage Entities",
            resource="entity",
            action="manage",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
        )

        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=self.role,
            is_active=True,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_create_field(self):
        response = self.client.post(
            "/api/entity-fields/",
            {
                "entity_id": str(self.entity.id),
                "name": "Phone",
                "slug": "phone",
                "field_type": "text",
                "required": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])

        self.assertEqual(
            response.data["field"]["name"],
            "Phone",
        )

        self.assertEqual(
            response.data["field"]["slug"],
            "phone",
        )

        self.assertEqual(
            response.data["field"]["field_type"],
            "text",
        )

        self.assertTrue(
            response.data["field"]["required"]
        )

        self.assertTrue(
            FieldDefinition.objects.filter(
                entity=self.entity,
                slug="phone",
            ).exists()
        )

        self.assertTrue(
            AuditLog.objects.filter(
                business=self.business,
                action="field.created",
                resource="field",
            ).exists()
        )

    def test_user_without_manage_permission_cannot_create_field(self):
        self.role.role_permissions.all().delete()

        response = self.client.post(
            "/api/entity-fields/",
            {
                "entity_id": str(self.entity.id),
                "name": "Email",
                "slug": "email",
                "field_type": "email",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            FieldDefinition.objects.filter(
                entity=self.entity,
                slug="email",
            ).exists()
        )

    def test_user_from_another_business_cannot_create_field(self):
        another_business = Business.objects.create(
            name="Another Field Business",
            slug="another-field-business",
            industry="restaurant",
            country="India",
        )

        another_entity = EntityDefinition.objects.create(
            business=another_business,
            name="Orders",
            slug="orders",
        )

        response = self.client.post(
            "/api/entity-fields/",
            {
                "entity_id": str(another_entity.id),
                "name": "Amount",
                "slug": "amount",
                "field_type": "decimal",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            FieldDefinition.objects.filter(
                entity=another_entity,
                slug="amount",
            ).exists()
        )

    def test_duplicate_field_slug_rejected(self):
        FieldDefinition.objects.create(
            entity=self.entity,
            name="Existing Phone",
            slug="phone",
            field_type="text",
        )

        response = self.client.post(
            "/api/entity-fields/",
            {
                "entity_id": str(self.entity.id),
                "name": "Phone Number",
                "slug": "phone",
                "field_type": "text",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            FieldDefinition.objects.filter(
                entity=self.entity,
                name="Phone Number",
            ).exists()
        )
