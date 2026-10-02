from django.core.management.base import BaseCommand

from core.models import (
    Business,
    Permission,
    Role,
    RolePermission,
)


DEFAULT_PERMISSIONS = [
    {
        "code": "business.view",
        "name": "View Business",
        "resource": "business",
        "action": "view",
    },
    {
        "code": "business.update",
        "name": "Update Business",
        "resource": "business",
        "action": "update",
    },

    # Users
    {
        "code": "users.view",
        "name": "View Users",
        "resource": "users",
        "action": "view",
    },
    {
        "code": "users.create",
        "name": "Create Users",
        "resource": "users",
        "action": "create",
    },
    {
        "code": "users.update",
        "name": "Update Users",
        "resource": "users",
        "action": "update",
    },
    {
        "code": "users.delete",
        "name": "Delete Users",
        "resource": "users",
        "action": "delete",
    },

    # Roles
    {
        "code": "roles.view",
        "name": "View Roles",
        "resource": "roles",
        "action": "view",
    },
    {
        "code": "roles.create",
        "name": "Create Roles",
        "resource": "roles",
        "action": "create",
    },
    {
        "code": "roles.update",
        "name": "Update Roles",
        "resource": "roles",
        "action": "update",
    },
    {
        "code": "roles.delete",
        "name": "Delete Roles",
        "resource": "roles",
        "action": "delete",
    },

    # Permissions
    {
        "code": "permissions.view",
        "name": "View Permissions",
        "resource": "permissions",
        "action": "view",
    },
    {
        "code": "permissions.manage",
        "name": "Manage Permissions",
        "resource": "permissions",
        "action": "manage",
    },

    # Settings
    {
        "code": "settings.view",
        "name": "View Settings",
        "resource": "settings",
        "action": "view",
    },
    {
        "code": "settings.update",
        "name": "Update Settings",
        "resource": "settings",
        "action": "update",
    },

    # Dynamic Entity Engine
    {
        "code": "entity.view",
        "name": "View Entities",
        "resource": "entity",
        "action": "view",
    },
    {
        "code": "entity.create",
        "name": "Create Entities",
        "resource": "entity",
        "action": "create",
    },
    {
        "code": "entity.update",
        "name": "Update Entities",
        "resource": "entity",
        "action": "update",
    },
    {
        "code": "entity.delete",
        "name": "Delete Entities",
        "resource": "entity",
        "action": "delete",
    },
    {
        "code": "entity.manage",
        "name": "Manage Entities",
        "resource": "entity",
        "action": "manage",
    },
]


ROLE_DEFINITIONS = {
    "owner": {
        "name": "Owner",
        "description": "Full access to the business.",
    },
    "admin": {
        "name": "Admin",
        "description": "Administrative access to the business.",
    },
    "manager": {
        "name": "Manager",
        "description": "Management-level access.",
    },
    "staff": {
        "name": "Staff",
        "description": "Basic operational access.",
    },
}


class Command(BaseCommand):
    help = "Seed default permissions and roles for all businesses."

    def handle(self, *args, **options):
        self.stdout.write("Creating permissions...")

        permissions = {}

        for item in DEFAULT_PERMISSIONS:
            permission, created = Permission.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "resource": item["resource"],
                    "action": item["action"],
                },
            )

            permissions[permission.code] = permission

            status = "created" if created else "updated"

            self.stdout.write(
                f"  {permission.code} ({status})"
            )

        businesses = Business.objects.all()

        if not businesses.exists():
            self.stdout.write(
                self.style.WARNING(
                    "No businesses found. Create a business first."
                )
            )
            return

        for business in businesses:
            self.stdout.write(
                f"\nProcessing business: {business.name}"
            )

            roles = {}

            for slug, definition in ROLE_DEFINITIONS.items():
                role, created = Role.objects.update_or_create(
                    business=business,
                    slug=slug,
                    defaults={
                        "name": definition["name"],
                        "description": definition["description"],
                        "is_system": True,
                    },
                )

                roles[slug] = role

                status = "created" if created else "updated"

                self.stdout.write(
                    f"  Role: {role.name} ({status})"
                )

            # Owner gets everything.
            owner = roles["owner"]

            for permission in permissions.values():
                RolePermission.objects.get_or_create(
                    role=owner,
                    permission=permission,
                )

            # Admin gets everything except permission administration.
            admin = roles["admin"]

            for permission in permissions.values():
                if permission.code == "permissions.manage":
                    continue

                RolePermission.objects.get_or_create(
                    role=admin,
                    permission=permission,
                )

            # Manager gets operational management permissions.
            manager = roles["manager"]

            manager_permissions = [
                "business.view",
                "users.view",
                "users.create",
                "users.update",
                "roles.view",
                "settings.view",

                # Dynamic Entity Engine
                "entity.view",
                "entity.create",
                "entity.update",
            ]

            for code in manager_permissions:
                RolePermission.objects.get_or_create(
                    role=manager,
                    permission=permissions[code],
                )

            # Staff gets basic viewing access.
            staff = roles["staff"]

            staff_permissions = [
                "business.view",
                "users.view",
                "roles.view",
                "settings.view",

                # Dynamic Entity Engine
                "entity.view",
            ]

            for code in staff_permissions:
                RolePermission.objects.get_or_create(
                    role=staff,
                    permission=permissions[code],
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Default permissions and roles seeded successfully."
            )
        )
