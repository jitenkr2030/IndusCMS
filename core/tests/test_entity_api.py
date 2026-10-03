from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import (
    Business,
    EntityDefinition,
    EntityRecord,
    FieldDefinition,
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


class EntityUpdateAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="entityupdatetest",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Entity Update Business",
            slug="entity-update-business",
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

        self.entity = EntityDefinition.objects.create(
            business=self.business,
            name="Customers",
            slug="customers",
            description="Customer records",
            is_active=True,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_update_entity(self):
        response = self.client.patch(
            f"/api/entities/{self.entity.id}/",
            {
                "name": "Clients",
                "slug": "clients",
                "description": "Updated client records",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.data["success"]
        )

        self.entity.refresh_from_db()

        self.assertEqual(
            self.entity.name,
            "Clients",
        )

        self.assertEqual(
            self.entity.slug,
            "clients",
        )

        self.assertEqual(
            self.entity.description,
            "Updated client records",
        )

    def test_partial_update_preserves_other_fields(self):
        response = self.client.patch(
            f"/api/entities/{self.entity.id}/",
            {
                "name": "Clients",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.entity.refresh_from_db()

        self.assertEqual(
            self.entity.name,
            "Clients",
        )

        self.assertEqual(
            self.entity.slug,
            "customers",
        )

        self.assertEqual(
            self.entity.description,
            "Customer records",
        )

    def test_update_creates_audit_log(self):
        response = self.client.patch(
            f"/api/entities/{self.entity.id}/",
            {
                "name": "Clients",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        audit = AuditLog.objects.filter(
            business=self.business,
            action="entity.updated",
            resource="entity",
            object_id=str(self.entity.id),
        ).first()

        self.assertIsNotNone(audit)

        self.assertEqual(
            audit.metadata["old_data"]["name"],
            "Customers",
        )

        self.assertEqual(
            audit.metadata["new_data"]["name"],
            "Clients",
        )

    def test_user_without_manage_permission_cannot_update(self):
        self.role.role_permissions.all().delete()

        response = self.client.patch(
            f"/api/entities/{self.entity.id}/",
            {
                "name": "Clients",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.entity.refresh_from_db()

        self.assertEqual(
            self.entity.name,
            "Customers",
        )

    def test_non_member_cannot_update(self):
        other_user = User.objects.create_user(
            username="otherentityuser",
            password="test-password-123",
        )

        self.client.force_authenticate(
            user=other_user
        )

        response = self.client.patch(
            f"/api/entities/{self.entity.id}/",
            {
                "name": "Clients",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.entity.refresh_from_db()

        self.assertEqual(
            self.entity.name,
            "Customers",
        )

    def test_entity_from_another_business_cannot_be_updated(self):
        another_business = Business.objects.create(
            name="Another Entity Business",
            slug="another-entity-business",
            industry="restaurant",
            country="India",
        )

        another_entity = EntityDefinition.objects.create(
            business=another_business,
            name="Orders",
            slug="orders",
            description="Order records",
            is_active=True,
        )

        response = self.client.patch(
            f"/api/entities/{another_entity.id}/",
            {
                "name": "Updated Orders",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        another_entity.refresh_from_db()

        self.assertEqual(
            another_entity.name,
            "Orders",
        )

    def test_inactive_entity_returns_404(self):
        self.entity.is_active = False
        self.entity.save(
            update_fields=["is_active"]
        )

        response = self.client.patch(
            f"/api/entities/{self.entity.id}/",
            {
                "name": "Clients",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_nonexistent_entity_returns_404(self):
        import uuid

        response = self.client.patch(
            f"/api/entities/{uuid.uuid4()}/",
            {
                "name": "Clients",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_duplicate_slug_returns_400(self):
        EntityDefinition.objects.create(
            business=self.business,
            name="Products",
            slug="products",
            description="Product records",
            is_active=True,
        )

        response = self.client.patch(
            f"/api/entities/{self.entity.id}/",
            {
                "slug": "products",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.entity.refresh_from_db()

        self.assertEqual(
            self.entity.slug,
            "customers",
        )

    def test_empty_name_returns_400(self):
        response = self.client.patch(
            f"/api/entities/{self.entity.id}/",
            {
                "name": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.entity.refresh_from_db()

        self.assertEqual(
            self.entity.name,
            "Customers",
        )

    def test_empty_slug_returns_400(self):
        response = self.client.patch(
            f"/api/entities/{self.entity.id}/",
            {
                "slug": "!!!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.entity.refresh_from_db()

        self.assertEqual(
            self.entity.slug,
            "customers",
        )

    def test_is_active_is_not_allowed(self):
        response = self.client.patch(
            f"/api/entities/{self.entity.id}/",
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.entity.refresh_from_db()

        self.assertTrue(
            self.entity.is_active
        )


class EntityDeactivateAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="deactivate_test_user",
            password="test-password-123",
        )
        self.business = Business.objects.create(
            name="Deactivate Test Business",
            slug="deactivate-test-business",
            industry="retail",
            country="India",
        )
        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )
        permission = Permission.objects.create(
            code="entity.manage",
            name="Manage Entities",
            resource="entity",
            action="manage",
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
            name="Customers",
            slug="customers",
        )
        self.url = f"/api/entities/{self.entity.id}/deactivate/"
        self.client.force_authenticate(user=self.user)

    def test_deactivate_entity(self):
        response = self.client.patch(self.url)
        self.entity.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.entity.is_active)

    def test_deactivation_creates_audit_log(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AuditLog.objects.filter(
            business=self.business,
            action="entity.deactivated",
            object_id=str(self.entity.id),
        ).exists())

    def test_user_without_manage_permission_gets_403(self):
        self.role.role_permissions.all().delete()
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 403)
        self.entity.refresh_from_db()
        self.assertTrue(self.entity.is_active)

    def test_non_member_gets_403(self):
        outsider = User.objects.create_user(
            username="deactivate_outsider",
            password="test-password-123",
        )
        self.client.force_authenticate(user=outsider)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 403)

    def test_already_inactive_entity_gets_400(self):
        self.entity.is_active = False
        self.entity.save(update_fields=["is_active"])
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 400)

    def test_missing_entity_gets_404(self):
        import uuid
        response = self.client.patch(
            f"/api/entities/{uuid.uuid4()}/deactivate/"
        )
        self.assertEqual(response.status_code, 404)


class FieldManagementAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="fieldmanagement",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Field Management Business",
            slug="field-management-business",
            industry="retail",
            country="India",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        for code, action in [
            ("entity.view", "view"),
            ("entity.manage", "manage"),
        ]:
            permission = Permission.objects.create(
                code=code,
                name=code,
                resource="entity",
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
            name="Customers",
            slug="customers",
        )

        self.field = self.entity.fields.create(
            name="Phone",
            slug="phone",
            field_type="text",
            position=1,
        )

        self.client.force_authenticate(user=self.user)

    def test_field_list(self):
        response = self.client.get(
            f"/api/entity-fields/list/?entity_id={self.entity.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_field_detail(self):
        response = self.client.get(
            f"/api/entity-fields/{self.field.id}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["field"]["slug"], "phone")

    def test_field_update(self):
        response = self.client.patch(
            f"/api/entity-fields/{self.field.id}/update/",
            {"name": "Mobile", "required": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.field.refresh_from_db()
        self.assertEqual(self.field.name, "Mobile")
        self.assertTrue(self.field.required)

    def test_field_deactivate(self):
        response = self.client.patch(
            f"/api/entity-fields/{self.field.id}/deactivate/"
        )
        self.assertEqual(response.status_code, 200)
        self.field.refresh_from_db()
        self.assertFalse(self.field.is_active)

    def test_inactive_field_hidden_from_list(self):
        self.field.is_active = False
        self.field.save(update_fields=["is_active"])
        response = self.client.get(
            f"/api/entity-fields/list/?entity_id={self.entity.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_update_creates_audit_log(self):
        response = self.client.patch(
            f"/api/entity-fields/{self.field.id}/update/",
            {"name": "Mobile"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(
                action="field.updated",
                resource="field",
                object_id=str(self.field.id),
            ).exists()
        )

    def test_deactivate_creates_audit_log(self):
        response = self.client.patch(
            f"/api/entity-fields/{self.field.id}/deactivate/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(
                action="field.deactivated",
                resource="field",
                object_id=str(self.field.id),
            ).exists()
        )


class FieldManagementAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="fieldmanagement",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Field Management Business",
            slug="field-management-business",
            industry="retail",
            country="India",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        for code, action in [
            ("entity.view", "view"),
            ("entity.manage", "manage"),
        ]:
            permission = Permission.objects.create(
                code=code,
                name=code,
                resource="entity",
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
            name="Customers",
            slug="customers",
        )

        self.field = self.entity.fields.create(
            name="Phone",
            slug="phone",
            field_type="text",
            position=1,
        )

        self.client.force_authenticate(user=self.user)

    def test_field_list(self):
        response = self.client.get(
            f"/api/entity-fields/list/?entity_id={self.entity.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_field_detail(self):
        response = self.client.get(
            f"/api/entity-fields/{self.field.id}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["field"]["slug"], "phone")

    def test_field_update(self):
        response = self.client.patch(
            f"/api/entity-fields/{self.field.id}/update/",
            {"name": "Mobile", "required": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.field.refresh_from_db()
        self.assertEqual(self.field.name, "Mobile")
        self.assertTrue(self.field.required)

    def test_field_deactivate(self):
        response = self.client.patch(
            f"/api/entity-fields/{self.field.id}/deactivate/"
        )
        self.assertEqual(response.status_code, 200)
        self.field.refresh_from_db()
        self.assertFalse(self.field.is_active)

    def test_inactive_field_hidden_from_list(self):
        self.field.is_active = False
        self.field.save(update_fields=["is_active"])
        response = self.client.get(
            f"/api/entity-fields/list/?entity_id={self.entity.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_update_creates_audit_log(self):
        response = self.client.patch(
            f"/api/entity-fields/{self.field.id}/update/",
            {"name": "Mobile"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(
                action="field.updated",
                resource="field",
                object_id=str(self.field.id),
            ).exists()
        )

    def test_deactivate_creates_audit_log(self):
        response = self.client.patch(
            f"/api/entity-fields/{self.field.id}/deactivate/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(
                action="field.deactivated",
                resource="field",
                object_id=str(self.field.id),
            ).exists()
        )


class EntityDeleteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="entitydelete",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Entity Delete Business",
            slug="entity-delete-business",
            industry="retail",
            country="India",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        permission = Permission.objects.create(
            code="entity.manage",
            name="Manage Entities",
            resource="entity",
            action="manage",
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
            name="Temporary Entity",
            slug="temporary-entity",
        )

        self.client.force_authenticate(user=self.user)

    def test_entity_delete(self):
        response = self.client.delete(
            f"/api/entities/{self.entity.id}/delete/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            EntityDefinition.objects.filter(
                id=self.entity.id
            ).exists()
        )

    def test_entity_delete_audit_log(self):
        entity_id = str(self.entity.id)

        response = self.client.delete(
            f"/api/entities/{entity_id}/delete/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(
                action="entity.deleted",
                resource="entity",
                object_id=entity_id,
            ).exists()
        )


class DynamicFormAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="dynamicform",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Dynamic Form Business",
            slug="dynamic-form-business",
            industry="retail",
            country="India",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
            is_system=True,
        )

        for code, action in [
            ("entity.view", "view"),
            ("entity.create", "create"),
        ]:
            permission = Permission.objects.create(
                code=code,
                name=code,
                resource="entity",
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
            name="Customers",
            slug="customers",
        )

        self.name_field = self.entity.fields.create(
            name="Name",
            slug="name",
            field_type="text",
            required=True,
            position=1,
        )

        self.phone_field = self.entity.fields.create(
            name="Phone",
            slug="phone",
            field_type="text",
            position=2,
        )

        self.client.force_authenticate(user=self.user)

    def test_dynamic_form_schema(self):
        response = self.client.get(
            f"/api/entities/{self.entity.id}/form/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["entity"]["slug"],
            "customers",
        )
        self.assertEqual(len(response.data["fields"]), 2)
        self.assertEqual(
            response.data["fields"][0]["slug"],
            "name",
        )

    def test_dynamic_form_submission_creates_record(self):
        response = self.client.post(
            f"/api/entities/{self.entity.id}/form/",
            {
                "name": "Rahul Kumar",
                "phone": "9876543210",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["record"]["data"]["name"],
            "Rahul Kumar",
        )

    def test_dynamic_form_required_validation(self):
        response = self.client.post(
            f"/api/entities/{self.entity.id}/form/",
            {
                "phone": "9876543210",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_dynamic_form_unknown_field_rejected(self):
        response = self.client.post(
            f"/api/entities/{self.entity.id}/form/",
            {
                "name": "Rahul Kumar",
                "unknown": "test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

class DynamicFormAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="dynamicform",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Dynamic Form Business",
            slug="dynamic-form-business",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
        )

        permission_data = {
            "entity.view": {
                "name": "View Entities",
                "resource": "entity",
                "action": "view",
            },
            "entity.create": {
                "name": "Create Entities",
                "resource": "entity",
                "action": "create",
            },
        }

        for code, defaults in permission_data.items():
            permission, _ = Permission.objects.get_or_create(
                code=code,
                defaults=defaults,
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
            name="Customers",
            slug="customers",
            is_active=True,
        )

        self.name_field = FieldDefinition.objects.create(
            entity=self.entity,
            name="Name",
            slug="name",
            field_type="text",
            required=True,
            position=1,
            is_active=True,
        )

        self.phone_field = FieldDefinition.objects.create(
            entity=self.entity,
            name="Phone",
            slug="phone",
            field_type="text",
            required=False,
            position=2,
            is_active=True,
        )

        self.client.force_authenticate(user=self.user)

    def test_dynamic_form_schema(self):
        response = self.client.get(
            f"/api/entities/{self.entity.id}/form/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["entity"]["slug"],
            "customers",
        )
        self.assertEqual(len(response.data["fields"]), 2)
        self.assertEqual(
            response.data["fields"][0]["slug"],
            "name",
        )
        self.assertEqual(
            response.data["fields"][0]["required"],
            True,
        )

    def test_dynamic_form_submission_creates_record(self):
        response = self.client.post(
            f"/api/entities/{self.entity.id}/form/",
            {
                "name": "Rahul Sharma",
                "phone": "9876543210",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])

        record = EntityRecord.objects.get(
            id=response.data["record"]["id"]
        )

        self.assertEqual(
            record.data["name"],
            "Rahul Sharma",
        )
        self.assertEqual(
            record.data["phone"],
            "9876543210",
        )

    def test_dynamic_form_required_validation(self):
        response = self.client.post(
            f"/api/entities/{self.entity.id}/form/",
            {
                "phone": "9876543210",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("Name", response.data["message"])

    def test_dynamic_form_unknown_field_rejected(self):
        response = self.client.post(
            f"/api/entities/{self.entity.id}/form/",
            {
                "name": "Rahul Sharma",
                "unknown_field": "test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn(
            "Unknown field",
            response.data["message"],
        )

class DynamicFormAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="dynamicform",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Dynamic Form Business",
            slug="dynamic-form-business",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
        )

        permission_data = {
            "entity.view": {
                "name": "View Entities",
                "resource": "entity",
                "action": "view",
            },
            "entity.create": {
                "name": "Create Entities",
                "resource": "entity",
                "action": "create",
            },
        }

        for code, defaults in permission_data.items():
            permission, _ = Permission.objects.get_or_create(
                code=code,
                defaults=defaults,
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
            name="Customers",
            slug="customers",
            is_active=True,
        )

        self.name_field = FieldDefinition.objects.create(
            entity=self.entity,
            name="Name",
            slug="name",
            field_type="text",
            required=True,
            position=1,
            is_active=True,
        )

        self.phone_field = FieldDefinition.objects.create(
            entity=self.entity,
            name="Phone",
            slug="phone",
            field_type="text",
            required=False,
            position=2,
            is_active=True,
        )

        self.client.force_authenticate(user=self.user)

    def test_dynamic_form_schema(self):
        response = self.client.get(
            f"/api/entities/{self.entity.id}/form/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["entity"]["slug"],
            "customers",
        )
        self.assertEqual(len(response.data["fields"]), 2)
        self.assertEqual(
            response.data["fields"][0]["slug"],
            "name",
        )
        self.assertEqual(
            response.data["fields"][0]["required"],
            True,
        )

    def test_dynamic_form_submission_creates_record(self):
        response = self.client.post(
            f"/api/entities/{self.entity.id}/form/",
            {
                "name": "Rahul Sharma",
                "phone": "9876543210",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])

        record = EntityRecord.objects.get(
            id=response.data["record"]["id"]
        )

        self.assertEqual(
            record.data["name"],
            "Rahul Sharma",
        )
        self.assertEqual(
            record.data["phone"],
            "9876543210",
        )

    def test_dynamic_form_required_validation(self):
        response = self.client.post(
            f"/api/entities/{self.entity.id}/form/",
            {
                "phone": "9876543210",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("Name", response.data["message"])

    def test_dynamic_form_unknown_field_rejected(self):
        response = self.client.post(
            f"/api/entities/{self.entity.id}/form/",
            {
                "name": "Rahul Sharma",
                "unknown_field": "test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn(
            "Unknown field",
            response.data["message"],
        )


class DynamicTableAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="dynamictable",
            password="test-password-123",
        )

        self.business = Business.objects.create(
            name="Dynamic Table Business",
            slug="dynamic-table-business",
        )

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            slug="owner",
        )

        for code, name, resource, action in [
            ("entity.view", "View Entities", "entity", "view"),
        ]:
            permission, _ = Permission.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "resource": resource,
                    "action": action,
                },
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
            name="Customers",
            slug="customers",
            is_active=True,
        )

        FieldDefinition.objects.create(
            entity=self.entity,
            name="Name",
            slug="name",
            field_type="text",
            required=True,
            position=1,
            is_active=True,
        )

        FieldDefinition.objects.create(
            entity=self.entity,
            name="Phone",
            slug="phone",
            field_type="text",
            position=2,
            is_active=True,
        )

        self.records = []

        for name, phone in [
            ("Rahul", "9000000001"),
            ("Amit", "9000000002"),
            ("Ravi", "9000000003"),
        ]:
            self.records.append(
                EntityRecord.objects.create(
                    entity=self.entity,
                    data={
                        "name": name,
                        "phone": phone,
                    },
                    created_by=self.user,
                )
            )

        self.deleted_record = EntityRecord.objects.create(
            entity=self.entity,
            data={
                "name": "Deleted Customer",
                "phone": "9999999999",
            },
            created_by=self.user,
            is_deleted=True,
        )

        self.client.force_authenticate(user=self.user)

    def test_table_schema_and_rows(self):
        response = self.client.get(
            f"/api/entities/{self.entity.id}/table/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["entity"]["slug"],
            "customers",
        )
        self.assertEqual(len(response.data["columns"]), 2)
        self.assertEqual(response.data["pagination"]["total"], 3)
        self.assertEqual(len(response.data["rows"]), 3)

        names = [
            row["data"]["name"]
            for row in response.data["rows"]
        ]

        self.assertNotIn("Deleted Customer", names)

    def test_table_pagination(self):
        response = self.client.get(
            f"/api/entities/{self.entity.id}/table/?page=1&page_size=2"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["pagination"]["page"],
            1,
        )
        self.assertEqual(
            response.data["pagination"]["page_size"],
            2,
        )
        self.assertEqual(
            response.data["pagination"]["total"],
            3,
        )
        self.assertEqual(
            response.data["pagination"]["total_pages"],
            2,
        )
        self.assertEqual(len(response.data["rows"]), 2)

    def test_table_search(self):
        response = self.client.get(
            f"/api/entities/{self.entity.id}/table/?search=Rahul"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["pagination"]["total"],
            1,
        )
        self.assertEqual(
            response.data["rows"][0]["data"]["name"],
            "Rahul",
        )

    def test_table_search_phone(self):
        response = self.client.get(
            f"/api/entities/{self.entity.id}/table/?search=9000000002"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["pagination"]["total"],
            1,
        )
        self.assertEqual(
            response.data["rows"][0]["data"]["name"],
            "Amit",
        )

    def test_table_sort(self):
        response = self.client.get(
            f"/api/entities/{self.entity.id}/table/?sort=name"
        )

        self.assertEqual(response.status_code, 200)

        names = [
            row["data"]["name"]
            for row in response.data["rows"]
        ]

        self.assertEqual(
            names,
            ["Amit", "Rahul", "Ravi"],
        )

    def test_table_descending_sort(self):
        response = self.client.get(
            f"/api/entities/{self.entity.id}/table/?sort=-name"
        )

        self.assertEqual(response.status_code, 200)

        names = [
            row["data"]["name"]
            for row in response.data["rows"]
        ]

        self.assertEqual(
            names,
            ["Ravi", "Rahul", "Amit"],
        )

    def test_table_requires_membership(self):
        outsider = User.objects.create_user(
            username="tableoutsider",
            password="test-password-123",
        )

        self.client.force_authenticate(user=outsider)

        response = self.client.get(
            f"/api/entities/{self.entity.id}/table/"
        )

        self.assertEqual(response.status_code, 403)

    def test_table_requires_view_permission(self):
        permissionless_user = User.objects.create_user(
            username="tablepermissionless",
            password="test-password-123",
        )

        role = Role.objects.create(
            business=self.business,
            name="No View",
            slug="no-view",
        )

        Membership.objects.create(
            user=permissionless_user,
            business=self.business,
            role=role,
            is_active=True,
        )

        self.client.force_authenticate(
            user=permissionless_user
        )

        response = self.client.get(
            f"/api/entities/{self.entity.id}/table/"
        )

        self.assertEqual(response.status_code, 403)
