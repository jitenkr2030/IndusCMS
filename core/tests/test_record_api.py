from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from core.models import (
    AuditLog,
    Business,
    EntityDefinition,
    FieldDefinition,
    Membership,
    Role,
    Permission,
    RolePermission,
    EntityRecord,
)


User = get_user_model()


class EntityRecordCreateAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="recordapi",
            password="password123",
        )

        self.other_user = User.objects.create_user(
            username="otherrecordapi",
            password="password123",
        )

        self.business = Business.objects.create(
            name="Record API Business",
            slug="record-api-business",
        )

        self.other_business = Business.objects.create(
            name="Other Record Business",
            slug="other-record-business",
        )

        self.permission = Permission.objects.create(
            code="entity.create",
            name="Create Entity Records",
            resource="entity",
            action="create",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Manager",
            slug="manager",
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

        self.other_role = Role.objects.create(
            business=self.other_business,
            name="Other Manager",
            slug="other-manager",
        )

        Membership.objects.create(
            user=self.other_user,
            business=self.other_business,
            role=self.other_role,
            is_active=True,
        )

        self.entity = EntityDefinition.objects.create(
            business=self.business,
            name="Customer",
            slug="customer",
        )

        FieldDefinition.objects.create(
            entity=self.entity,
            name="Name",
            slug="name",
            field_type="text",
            required=True,
        )

        FieldDefinition.objects.create(
            entity=self.entity,
            name="Email",
            slug="email",
            field_type="email",
        )

        FieldDefinition.objects.create(
            entity=self.entity,
            name="Credit Limit",
            slug="credit_limit",
            field_type="decimal",
        )

        self.url = "/api/entity-records/"

    def test_create_record(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {
                "entity_id": str(self.entity.id),
                "data": {
                    "name": "Rahul Kumar",
                    "email": "rahul@example.com",
                    "credit_limit": 50000,
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["message"],
            "Record created successfully.",
        )

        record = EntityRecord.objects.get(
            id=response.data["record"]["id"]
        )

        self.assertEqual(
            record.data["name"],
            "Rahul Kumar",
        )

        self.assertEqual(
            record.data["email"],
            "rahul@example.com",
        )

        self.assertEqual(
            record.data["credit_limit"],
            "50000",
        )

        self.assertTrue(
            AuditLog.objects.filter(
                action="record.created",
                resource="entity_record",
                object_id=str(record.id),
            ).exists()
        )

    def test_invalid_record_data_returns_400(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {
                "entity_id": str(self.entity.id),
                "data": {
                    "email": "invalid-email",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            EntityRecord.objects.filter(
                entity=self.entity
            ).count(),
            0,
        )

    def test_cross_business_user_cannot_create_record(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            self.url,
            {
                "entity_id": str(self.entity.id),
                "data": {
                    "name": "Rahul Kumar",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            EntityRecord.objects.filter(
                entity=self.entity
            ).count(),
            0,
        )

    def test_user_without_create_permission_cannot_create_record(self):
        no_permission_user = User.objects.create_user(
            username="nopermission",
            password="password123",
        )

        Membership.objects.create(
            user=no_permission_user,
            business=self.business,
            role=None,
            is_active=True,
        )

        self.client.force_authenticate(
            user=no_permission_user
        )

        response = self.client.post(
            self.url,
            {
                "entity_id": str(self.entity.id),
                "data": {
                    "name": "Rahul Kumar",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            EntityRecord.objects.filter(
                entity=self.entity
            ).count(),
            0,
        )
