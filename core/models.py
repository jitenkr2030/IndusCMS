import uuid

from django.contrib.auth.models import User
from django.db import models


class Business(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(max_length=200)

    slug = models.SlugField(
        max_length=200,
        unique=True,
    )

    industry = models.CharField(
        max_length=100,
        blank=True,
    )

    email = models.EmailField(blank=True)

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    website = models.URLField(blank=True)

    address = models.TextField(blank=True)

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    country = models.CharField(
        max_length=100,
        default="India",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Role(models.Model):
    """
    Business-specific role.
    """

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="roles",
    )

    name = models.CharField(
        max_length=100,
    )

    slug = models.SlugField(
        max_length=100,
    )

    description = models.TextField(
        blank=True,
    )

    is_system = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "slug"],
                name="unique_business_role",
            )
        ]

        ordering = ["name"]

    def __str__(self):
        return f"{self.business.name} - {self.name}"


class Permission(models.Model):
    """
    Permission available inside IndusCMS.
    """

    ACTION_CHOICES = [
        ("view", "View"),
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("manage", "Manage"),
    ]

    code = models.CharField(
        max_length=150,
        unique=True,
    )

    name = models.CharField(
        max_length=150,
    )

    resource = models.CharField(
        max_length=100,
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
    )

    description = models.TextField(
        blank=True,
    )

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    """
    Connects roles with permissions.
    """

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )

    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="unique_role_permission",
            )
        ]

    def __str__(self):
        return f"{self.role} → {self.permission}"


class Membership(models.Model):
    """
    Connects a Django user with a business.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="business_memberships",
    )

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memberships",
    )

    is_active = models.BooleanField(
        default=True,
    )

    joined_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "business"],
                name="unique_user_business_membership",
            )
        ]

    def __str__(self):
        role_name = self.role.name if self.role else "No Role"
        return f"{self.user.username} → {self.business.name} ({role_name})"


class BusinessSettings(models.Model):
    business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name="settings",
    )

    currency = models.CharField(
        max_length=10,
        default="INR",
    )

    timezone = models.CharField(
        max_length=100,
        default="Asia/Kolkata",
    )

    date_format = models.CharField(
        max_length=30,
        default="DD-MM-YYYY",
    )

    logo = models.ImageField(
        upload_to="business/logos/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Settings - {self.business.name}"


class AuditLog(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.PROTECT,
        related_name="audit_logs",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="induscms_audit_logs",
    )
    action = models.CharField(max_length=100)
    resource = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["business", "-created_at"],
                name="audit_business_time_idx",
            ),
            models.Index(
                fields=["action"],
                name="audit_action_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValueError("Audit logs cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Audit logs cannot be deleted.")

    def __str__(self):
        return f"{self.action} - {self.resource} - {self.created_at}"


class EntityDefinition(models.Model):
    """A configurable business entity, such as Customers or Products."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="entity_definitions",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "slug"],
                name="unique_entity_slug_per_business",
            ),
        ]
        indexes = [
            models.Index(fields=["business", "is_active"]),
        ]

    def __str__(self):
        return f"{self.business.name} - {self.name}"


class FieldDefinition(models.Model):
    """Configurable field metadata for an entity."""

    class FieldType(models.TextChoices):
        TEXT = "text", "Text"
        LONG_TEXT = "long_text", "Long text"
        NUMBER = "number", "Number"
        DECIMAL = "decimal", "Decimal"
        BOOLEAN = "boolean", "Boolean"
        DATE = "date", "Date"
        DATETIME = "datetime", "Date and time"
        EMAIL = "email", "Email"
        URL = "url", "URL"
        CHOICE = "choice", "Choice"
        JSON = "json", "JSON"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    entity = models.ForeignKey(
        EntityDefinition,
        on_delete=models.CASCADE,
        related_name="fields",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160)
    field_type = models.CharField(
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.TEXT,
    )
    required = models.BooleanField(default=False)
    unique = models.BooleanField(default=False)
    default_value = models.JSONField(null=True, blank=True)
    choices = models.JSONField(default=list, blank=True)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["entity", "slug"],
                name="unique_field_slug_per_entity",
            ),
        ]

    def __str__(self):
        return f"{self.entity.name} - {self.name}"



class RelationshipDefinition(models.Model):
    RELATIONSHIP_TYPES = (
        ("many_to_one", "Many to One"),
        ("one_to_one", "One to One"),
        ("many_to_many", "Many to Many"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="relationships",
    )
    source_entity = models.ForeignKey(
        EntityDefinition,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
    )
    target_entity = models.ForeignKey(
        EntityDefinition,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)
    relationship_type = models.CharField(
        max_length=30,
        choices=RELATIONSHIP_TYPES,
        default="many_to_one",
    )
    required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_entity", "slug"),
                name="unique_source_relationship_slug",
            ),
        ]
        indexes = [
            models.Index(
                fields=("business", "is_active"),
            ),
            models.Index(
                fields=("source_entity", "is_active"),
            ),
        ]
        ordering = ("name",)

    def __str__(self):
        return (
            f"{self.source_entity.name} -> "
            f"{self.target_entity.name}: {self.name}"
        )


class EntityRecord(models.Model):
    """A record stored against a configurable entity."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    entity = models.ForeignKey(
        EntityDefinition,
        on_delete=models.CASCADE,
        related_name="records",
    )
    data = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_entity_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_entity_records",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity", "created_at"]),
        ]

    def __str__(self):
        return f"{self.entity.name} record ({self.pk})"

# ============================================================
# PHASE 4 — WORKFLOW ENGINE
# ============================================================

class WorkflowDefinition(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="workflows",
    )
    entity = models.ForeignKey(
        EntityDefinition,
        on_delete=models.CASCADE,
        related_name="workflows",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("business", "slug"),
                name="unique_business_workflow_slug",
            ),
        ]
        indexes = [
            models.Index(fields=("business", "is_active")),
            models.Index(fields=("entity", "is_active")),
        ]
        ordering = ("name",)

    def __str__(self):
        return f"{self.business.name} - {self.name}"


class WorkflowStep(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    workflow = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)
    description = models.TextField(blank=True, default="")
    position = models.PositiveIntegerField(default=0)
    is_initial = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("workflow", "slug"),
                name="unique_workflow_step_slug",
            ),
        ]
        indexes = [
            models.Index(fields=("workflow", "is_active")),
        ]
        ordering = ("position", "name")

    def __str__(self):
        return f"{self.workflow.name} - {self.name}"


class WorkflowTransition(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    workflow = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.CASCADE,
        related_name="transitions",
    )
    from_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="outgoing_transitions",
    )
    to_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="incoming_transitions",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("workflow", "slug"),
                name="unique_workflow_transition_slug",
            ),
        ]
        indexes = [
            models.Index(fields=("workflow", "is_active")),
            models.Index(fields=("from_step", "is_active")),
        ]
        ordering = ("name",)

    def __str__(self):
        return (
            f"{self.workflow.name}: "
            f"{self.from_step.name} -> {self.to_step.name}"
        )


class WorkflowInstance(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    workflow = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.CASCADE,
        related_name="instances",
    )
    record = models.ForeignKey(
        EntityRecord,
        on_delete=models.CASCADE,
        related_name="workflow_instances",
    )
    current_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.PROTECT,
        related_name="current_instances",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    started_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="started_workflow_instances",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("workflow", "record"),
                name="unique_workflow_record_instance",
            ),
        ]
        indexes = [
            models.Index(fields=("workflow", "status")),
            models.Index(fields=("record", "status")),
        ]
        ordering = ("-started_at",)

    def __str__(self):
        return (
            f"{self.workflow.name} / "
            f"{self.record_id} / "
            f"{self.current_step.name}"
        )


class WorkflowHistory(models.Model):
    """Immutable-by-convention timeline for a workflow instance."""

    ACTION_CHOICES = (
        ("started", "Started"),
        ("transitioned", "Transitioned"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    instance = models.ForeignKey(
        "WorkflowInstance",
        on_delete=models.CASCADE,
        related_name="history",
    )
    transition = models.ForeignKey(
        "WorkflowTransition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="history_entries",
    )
    from_step = models.ForeignKey(
        "WorkflowStep",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="history_from_entries",
    )
    to_step = models.ForeignKey(
        "WorkflowStep",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="history_to_entries",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_history_entries",
    )
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [
            models.Index(fields=("instance", "created_at")),
        ]

    def __str__(self):
        return f"{self.instance_id}: {self.action}"


class WorkflowCondition(models.Model):
    OPERATOR_CHOICES = (
        ("equals", "Equals"),
        ("not_equals", "Not Equals"),
        ("greater_than", "Greater Than"),
        ("greater_than_or_equal", "Greater Than or Equal"),
        ("less_than", "Less Than"),
        ("less_than_or_equal", "Less Than or Equal"),
        ("contains", "Contains"),
        ("is_true", "Is True"),
        ("is_false", "Is False"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    transition = models.ForeignKey(
        WorkflowTransition,
        on_delete=models.CASCADE,
        related_name="conditions",
    )

    field_slug = models.CharField(
        max_length=160,
    )

    operator = models.CharField(
        max_length=40,
        choices=OPERATOR_CHOICES,
    )

    value = models.JSONField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("field_slug", "created_at")
        indexes = [
            models.Index(
                fields=("transition", "is_active"),
            ),
        ]

    def __str__(self):
        return (
            f"{self.transition.name}: "
            f"{self.field_slug} {self.operator}"
        )


class WorkflowAction(models.Model):
    ACTION_TYPES = (
        ("audit", "Audit"),
        ("notification", "Notification"),
        ("webhook", "Webhook"),
        ("update_record", "Update Record"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    transition = models.ForeignKey(
        WorkflowTransition,
        on_delete=models.CASCADE,
        related_name="actions",
    )

    name = models.CharField(max_length=150)
    action_type = models.CharField(
        max_length=40,
        choices=ACTION_TYPES,
    )

    config = models.JSONField(
        default=dict,
        blank=True,
    )

    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("position", "created_at")
        indexes = [
            models.Index(
                fields=("transition", "is_active"),
            ),
        ]

    def __str__(self):
        return f"{self.transition.name}: {self.name}"
