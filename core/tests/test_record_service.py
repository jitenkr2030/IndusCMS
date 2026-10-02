from django.contrib.auth.models import User
from django.test import TestCase

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
from core.services.record import (
    create_record_for_entity,
    validate_record_data,
)


class EntityRecordServiceTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="recordtest",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Record Test Business",
            slug="record-test-business",
            industry="retail",
            country="India",
        )

        self.entity = EntityDefinition.objects.create(
            business=self.business,
            name="Customers",
            slug="customers",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        permission = Permission.objects.create(
            code="entity.create",
            name="Create Entity Records",
            resource="entity",
            action="create",
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

        self.credit_field = FieldDefinition.objects.create(
            entity=self.entity,
            name="Credit Limit",
            slug="credit_limit",
            field_type="decimal",
            required=False,
            position=3,
        )

        self.active_field = FieldDefinition.objects.create(
            entity=self.entity,
            name="Active",
            slug="active",
            field_type="boolean",
            required=False,
            position=4,
        )

    def test_valid_data(self):
        data = validate_record_data(
            self.entity,
            {
                "name": "Rahul",
                "email": "rahul@example.com",
                "credit_limit": 50000,
                "active": True,
            },
        )

        self.assertEqual(
            data["name"],
            "Rahul",
        )

        self.assertEqual(
            data["credit_limit"],
            "50000",
        )

        self.assertTrue(
            data["active"]
        )

    def test_required_field(self):
        with self.assertRaises(ValueError):
            validate_record_data(
                self.entity,
                {
                    "email": "rahul@example.com",
                },
            )

    def test_unknown_field(self):
        with self.assertRaises(ValueError):
            validate_record_data(
                self.entity,
                {
                    "name": "Rahul",
                    "unknown": "value",
                },
            )

    def test_invalid_decimal(self):
        with self.assertRaises(ValueError):
            validate_record_data(
                self.entity,
                {
                    "name": "Rahul",
                    "credit_limit": "hello",
                },
            )

    def test_invalid_boolean(self):
        with self.assertRaises(ValueError):
            validate_record_data(
                self.entity,
                {
                    "name": "Rahul",
                    "active": "maybe",
                },
            )

    def test_create_record(self):
        record = create_record_for_entity(
            user=self.user,
            entity=self.entity,
            data={
                "name": "Rahul",
                "email": "rahul@example.com",
                "credit_limit": 50000,
                "active": True,
            },
        )

        self.assertEqual(
            record.data["name"],
            "Rahul",
        )

        self.assertEqual(
            record.data["credit_limit"],
            "50000",
        )

        self.assertEqual(
            record.created_by,
            self.user,
        )

        self.assertTrue(
            AuditLog.objects.filter(
                business=self.business,
                action="record.created",
                resource="entity_record",
            ).exists()
        )

    def test_user_without_permission_cannot_create_record(self):
        self.role.role_permissions.all().delete()

        with self.assertRaises(PermissionError):
            create_record_for_entity(
                user=self.user,
                entity=self.entity,
                data={
                    "name": "Rahul",
                },
            )
