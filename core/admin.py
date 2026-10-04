from django.contrib import admin

from .models import (
    AuditLog,
    Business,
    BusinessSettings,
    EntityDefinition,
    EntityRecord,
    FieldDefinition,
    Membership,
    Permission,
    Role,
    RolePermission,
)


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "industry",
        "city",
        "country",
        "is_active",
        "created_at",
    )

    list_filter = (
        "industry",
        "is_active",
        "country",
    )

    search_fields = (
        "name",
        "slug",
        "email",
        "phone",
        "city",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "business",
        "is_system",
        "created_at",
    )

    list_filter = (
        "business",
        "is_system",
    )

    search_fields = (
        "name",
        "slug",
        "business__name",
    )


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "resource",
        "action",
    )

    list_filter = (
        "resource",
        "action",
    )

    search_fields = (
        "code",
        "name",
        "resource",
    )


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = (
        "role",
        "permission",
    )

    list_filter = (
        "role",
        "permission",
    )


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "business",
        "role",
        "is_active",
        "joined_at",
    )

    list_filter = (
        "role",
        "is_active",
        "business",
    )

    search_fields = (
        "user__username",
        "user__email",
        "business__name",
    )


@admin.register(BusinessSettings)
class BusinessSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "business",
        "currency",
        "timezone",
        "date_format",
    )

    search_fields = (
        "business__name",
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "business",
        "user",
        "action",
        "resource",
        "object_id",
    )

    list_filter = (
        "action",
        "resource",
        "created_at",
    )

    search_fields = (
        "business__name",
        "user__username",
        "action",
        "resource",
        "object_id",
    )

    readonly_fields = (
        "business",
        "user",
        "action",
        "resource",
        "object_id",
        "ip_address",
        "metadata",
        "created_at",
    )

    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EntityDefinition)
class EntityDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "business",
        "slug",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "business",
        "is_active",
    )

    search_fields = (
        "name",
        "slug",
        "business__name",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "business",
        "name",
    )


@admin.register(FieldDefinition)
class FieldDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "entity",
        "field_type",
        "required",
        "unique",
        "position",
        "is_active",
        "is_system",
    )

    list_filter = (
        "field_type",
        "required",
        "unique",
        "is_active",
        "is_system",
    )

    search_fields = (
        "name",
        "slug",
        "entity__name",
        "entity__business__name",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "entity",
        "position",
        "name",
    )


@admin.register(EntityRecord)
class EntityRecordAdmin(admin.ModelAdmin):
    list_display = (
        "entity",
        "created_by",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "entity",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "entity__name",
        "entity__business__name",
        "created_by__username",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

from core.models import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTransition,
    WorkflowInstance,
    WorkflowTrigger,
)

admin.site.register(WorkflowDefinition)
admin.site.register(WorkflowStep)
admin.site.register(WorkflowTransition)
admin.site.register(WorkflowInstance)


from core.models import WorkflowHistory

admin.site.register(WorkflowHistory)


@admin.register(WorkflowTrigger)
class WorkflowTriggerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "workflow",
        "event_type",
        "is_active",
        "created_at",
    )
    list_filter = (
        "event_type",
        "is_active",
    )
    search_fields = (
        "name",
        "workflow__name",
    )
