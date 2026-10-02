from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from core.models import (
    Business,
    EntityDefinition,
    EntityRecord,
    Membership,
    Permission,
    Role,
    RolePermission,
)

User = get_user_model()


class EntityRecordDetailAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="detailuser",
            password="password123",
        )

        self.other_user = User.objects.create_user(
            username="detailother",
            password="password123",
        )

        self.business = Business.objects.create(
            name="Detail Business",
            slug="detail-business",
        )

        self.other_business = Business.objects.create(
            name="Other Detail Business",
            slug="other-detail-business",
        )

        self.view_permission = Permission.objects.create(
            code="entity.view",
            name="View Entity Records",
            resource="entity",
            action="view",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Reader",
            slug="reader",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.view_permission,
        )

        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=self.role,
            is_active=True,
        )

        self.other_role = Role.objects.create(
            business=self.other_business,
            name="Other Reader",
            slug="other-reader",
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

        self.record = EntityRecord.objects.create(
            entity=self.entity,
            data={
                "name": "Rahul Kumar",
                "email": "rahul@example.com",
            },
            created_by=self.user,
        )

        self.url = (
            f"/api/entity-records/{self.record.id}/"
        )

    def test_authorized_user_can_view_record(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

        self.assertEqual(
            response.data["record"]["id"],
            str(self.record.id),
        )

        self.assertEqual(
            response.data["record"]["data"]["name"],
            "Rahul Kumar",
        )

    def test_other_business_user_cannot_view_record(self):
        self.client.force_authenticate(
            user=self.other_user
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_user_without_view_permission_cannot_view_record(self):
        no_permission_user = User.objects.create_user(
            username="detailnopermission",
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

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_nonexistent_record_returns_404(self):
        self.client.force_authenticate(user=self.user)

        import uuid

        response = self.client.get(
            f"/api/entity-records/{uuid.uuid4()}/"
        )

        self.assertEqual(response.status_code, 404)


    def test_deleted_record_returns_404(self):
        self.client.force_authenticate(user=self.user)

        self.record.is_deleted = True
        self.record.save(
            update_fields=[
                "is_deleted",
            ]
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
