from django.core.management.base import BaseCommand

from core.models import Permission, Role, RolePermission


WORKFLOW_PERMISSIONS = [
    ("workflow.view", "View Workflows", "workflow", "view"),
    ("workflow.create", "Create Workflows", "workflow", "create"),
    ("workflow.update", "Update Workflows", "workflow", "update"),
    ("workflow.delete", "Delete Workflows", "workflow", "delete"),
    ("workflow.manage", "Manage Workflows", "workflow", "manage"),
]


class Command(BaseCommand):
    help = "Seed Phase 4 workflow permissions."

    def handle(self, *args, **options):
        permissions = {}

        for code, name, resource, action in WORKFLOW_PERMISSIONS:
            permission, _ = Permission.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "resource": resource,
                    "action": action,
                },
            )
            permissions[code] = permission

        for role in Role.objects.select_related("business").all():
            if role.slug in {"owner", "admin"}:
                codes = permissions.keys()
            elif role.slug == "manager":
                codes = {
                    "workflow.view",
                    "workflow.create",
                    "workflow.update",
                }
            else:
                codes = {"workflow.view"}

            for code in codes:
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=permissions[code],
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Workflow permissions seeded successfully."
            )
        )
