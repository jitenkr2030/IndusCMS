from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import (
    Business,
    EntityDefinition,
    Permission,
    Role,
    RolePermission,
    Membership,
    AuditLog,
)


class EntityCreationAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="entitytest",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Entity Test Business",
            slug="entity-test-business",
            industry="retail",
            country="India",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        self.permission = Permission.objects.create(
            code="entity.create",
            name="Create Entities",
            resource="entity",
            action="create",
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

    def test_create_entity(self):
        response = self.client.post(
            "/api/entities/",
            {
                "business_id": str(self.business.id),
                "name": "Customers",
                "slug": "customers",
                "description": "Business customers",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertTrue(
            response.data["success"]
        )

        self.assertEqual(
            response.data["entity"]["name"],
            "Customers",
        )

        self.assertEqual(
            response.data["entity"]["slug"],
            "customers",
        )

        self.assertTrue(
            EntityDefinition.objects.filter(
                business=self.business,
                slug="customers",
            ).exists()
        )

        self.assertTrue(
            AuditLog.objects.filter(
                business=self.business,
                action="entity.created",
                resource="entity",
            ).exists()
        )

    def test_user_without_permission_cannot_create_entity(self):
        self.role.role_permissions.all().delete()

        response = self.client.post(
            "/api/entities/",
            {
                "business_id": str(self.business.id),
                "name": "Products",
                "slug": "products",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            EntityDefinition.objects.filter(
                business=self.business,
                slug="products",
            ).exists()
        )

    def test_user_from_another_business_cannot_create_entity(self):
        another_business = Business.objects.create(
            name="Another Business",
            slug="another-business",
            industry="restaurant",
            country="India",
        )

        response = self.client.post(
            "/api/entities/",
            {
                "business_id": str(another_business.id),
                "name": "Orders",
                "slug": "orders",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            EntityDefinition.objects.filter(
                business=another_business,
                slug="orders",
            ).exists()
        )


class EntityListAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="entitylisttest",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Entity List Business",
            slug="entity-list-business",
            industry="retail",
            country="India",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        self.permission = Permission.objects.create(
            code="entity.view",
            name="View Entities",
            resource="entity",
            action="view",
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

        self.customer_entity = EntityDefinition.objects.create(
            business=self.business,
            name="Customers",
            slug="customers",
            description="Customer records",
            is_active=True,
        )

        self.product_entity = EntityDefinition.objects.create(
            business=self.business,
            name="Products",
            slug="products",
            description="Product records",
            is_active=True,
        )

    def test_list_entities(self):
        response = self.client.get(
            "/api/entities/list/",
            {
                "business_id": str(self.business.id),
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
            response.data["count"],
            2,
        )

        slugs = {
            entity["slug"]
            for entity in response.data["results"]
        }

        self.assertEqual(
            slugs,
            {
                "customers",
                "products",
            },
        )

    def test_business_id_is_required(self):
        response = self.client.get(
            "/api/entities/list/"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            response.data["success"]
        )

    def test_non_member_cannot_list_entities(self):
        another_user = User.objects.create_user(
            username="nonmember",
            password="test-password-123",
        )

        self.client.force_authenticate(
            user=another_user
        )

        response = self.client.get(
            "/api/entities/list/",
            {
                "business_id": str(self.business.id),
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            response.data["success"]
        )

    def test_user_without_view_permission_cannot_list_entities(self):
        self.role.role_permissions.all().delete()

        response = self.client.get(
            "/api/entities/list/",
            {
                "business_id": str(self.business.id),
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            response.data["success"]
        )

    def test_user_cannot_list_another_business_entities(self):
        another_business = Business.objects.create(
            name="Another Entity Business",
            slug="another-entity-business",
            industry="restaurant",
            country="India",
        )

        EntityDefinition.objects.create(
            business=another_business,
            name="Orders",
            slug="orders",
            is_active=True,
        )

        response = self.client.get(
            "/api/entities/list/",
            {
                "business_id": str(another_business.id),
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            response.data["success"]
        )

    def test_inactive_entities_are_hidden(self):
        EntityDefinition.objects.create(
            business=self.business,
            name="Inactive Entity",
            slug="inactive-entity",
            description="Should not appear",
            is_active=False,
        )

        response = self.client.get(
            "/api/entities/list/",
            {
                "business_id": str(self.business.id),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

        slugs = {
            entity["slug"]
            for entity in response.data["results"]
        }

        self.assertNotIn(
            "inactive-entity",
            slugs,
        )


class EntityDetailAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="entitydetailtest",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Entity Detail Business",
            slug="entity-detail-business",
            industry="retail",
            country="India",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        self.permission = Permission.objects.create(
            code="entity.view",
            name="View Entities",
            resource="entity",
            action="view",
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

        self.entity = EntityDefinition.objects.create(
            business=self.business,
            name="Customers",
            slug="customers",
            description="Customer records",
            is_active=True,
        )

    def test_get_entity_detail(self):
        response = self.client.get(
            f"/api/entities/{self.entity.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.data["success"]
        )

        self.assertEqual(
            response.data["entity"]["id"],
            str(self.entity.id),
        )

        self.assertEqual(
            response.data["entity"]["name"],
            "Customers",
        )

        self.assertEqual(
            response.data["entity"]["slug"],
            "customers",
        )

    def test_entity_not_found_returns_404(self):
        import uuid

        response = self.client.get(
            f"/api/entities/{uuid.uuid4()}/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertFalse(
            response.data["success"]
        )

    def test_inactive_entity_returns_404(self):
        self.entity.is_active = False
        self.entity.save(
            update_fields=["is_active", "updated_at"]
        )

        response = self.client.get(
            f"/api/entities/{self.entity.id}/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertFalse(
            response.data["success"]
        )

    def test_non_member_cannot_view_entity_detail(self):
        another_user = User.objects.create_user(
            username="detailnonmember",
            password="test-password-123",
        )

        self.client.force_authenticate(
            user=another_user
        )

        response = self.client.get(
            f"/api/entities/{self.entity.id}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            response.data["success"]
        )

    def test_user_without_view_permission_cannot_view_entity_detail(self):
        self.role.role_permissions.all().delete()

        response = self.client.get(
            f"/api/entities/{self.entity.id}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            response.data["success"]
        )

    def test_user_cannot_view_entity_from_another_business(self):
        another_business = Business.objects.create(
            name="Another Detail Business",
            slug="another-detail-business",
            industry="restaurant",
            country="India",
        )

        another_entity = EntityDefinition.objects.create(
            business=another_business,
            name="Orders",
            slug="orders",
            is_active=True,
        )

        response = self.client.get(
            f"/api/entities/{another_entity.id}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            response.data["success"]
        )
