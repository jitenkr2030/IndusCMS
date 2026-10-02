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


class EntityRecordListAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="listuser",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="listother",
            password="password123",
        )

        self.business = Business.objects.create(
            name="List Business",
            slug="list-business",
        )
        self.other_business = Business.objects.create(
            name="Other List Business",
            slug="other-list-business",
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

        EntityRecord.objects.create(
            entity=self.entity,
            data={"name": "Rahul Kumar"},
            created_by=self.user,
        )
        EntityRecord.objects.create(
            entity=self.entity,
            data={"name": "Priya Sharma"},
            created_by=self.user,
        )

        self.url = "/api/entity-records/"

    def test_authorized_user_can_list_records(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            self.url,
            {"entity_id": str(self.entity.id)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["pagination"]["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

    def test_user_without_view_permission_is_forbidden(self):
        no_permission_user = User.objects.create_user(
            username="listnopermission",
            password="password123",
        )
        Membership.objects.create(
            user=no_permission_user,
            business=self.business,
            role=None,
            is_active=True,
        )

        self.client.force_authenticate(user=no_permission_user)

        response = self.client.get(
            self.url,
            {"entity_id": str(self.entity.id)},
        )

        self.assertEqual(response.status_code, 403)

    def test_other_business_user_cannot_list_records(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(
            self.url,
            {"entity_id": str(self.entity.id)},
        )

        self.assertEqual(response.status_code, 403)

    def test_pagination_limits_page_size(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            self.url,
            {
                "entity_id": str(self.entity.id),
                "page_size": 101,
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_missing_entity_id_returns_400(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 400)


    def test_deleted_record_is_hidden_from_list(self):
        self.client.force_authenticate(user=self.user)

        record = EntityRecord.objects.create(
            entity=self.entity,
            data={"name": "Deleted Customer"},
            created_by=self.user,
            is_deleted=True,
        )

        response = self.client.get(
            f"/api/entity-records/?entity_id={self.entity.id}"
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertNotIn(
            str(record.id),
            returned_ids,
        )
