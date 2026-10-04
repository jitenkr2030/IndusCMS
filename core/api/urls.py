from django.urls import path

from core.api.views import (
    EntityDynamicTableAPIView,
    BusinessCreateAPIView,
    EntityDefinitionCreateAPIView,
    EntityDefinitionListAPIView,
    EntityDefinitionDetailAPIView,
    EntityDefinitionDeactivateAPIView,
    EntityDefinitionDeleteAPIView,
    FieldDefinitionCreateAPIView,
    FieldDefinitionListAPIView,
    FieldDefinitionDetailAPIView,
    FieldDefinitionUpdateAPIView,
    FieldDefinitionDeactivateAPIView,
    RelationshipOptionsAPIView,
    EntityDynamicFormAPIView,
    EntityRecordCreateAPIView,
    EntityRecordDetailAPIView,
)


from core.api.workflow_action_views import (
    WorkflowActionCreateAPIView,
    WorkflowActionListAPIView,
)

urlpatterns = [
    path(
        "entities/<uuid:entity_id>/table/",
        EntityDynamicTableAPIView.as_view(),
        name="entity-dynamic-table",
    ),

    path(
        "entities/<uuid:entity_id>/form/",
        EntityDynamicFormAPIView.as_view(),
        name="entity-dynamic-form",
    ),
    path(
        "businesses/",
        BusinessCreateAPIView.as_view(),
        name="business-create",
    ),

    path(
        "entities/",
        EntityDefinitionCreateAPIView.as_view(),
        name="entity-create",
    ),

    path(
        "entities/list/",
        EntityDefinitionListAPIView.as_view(),
        name="entity-list",
    ),

    path(
        "entities/<uuid:entity_id>/delete/",
        EntityDefinitionDeleteAPIView.as_view(),
        name="entity-delete",
    ),
    path(
        "entities/<uuid:entity_id>/deactivate/",
        EntityDefinitionDeactivateAPIView.as_view(),
        name="entity-deactivate",
    ),
    path(
        "entities/<uuid:entity_id>/",
        EntityDefinitionDetailAPIView.as_view(),
        name="entity-detail",
    ),

    path(
        "entity-fields/",
        FieldDefinitionCreateAPIView.as_view(),
        name="field-create",
    ),
    path(
        "entity-fields/list/",
        FieldDefinitionListAPIView.as_view(),
        name="field-list",
    ),
    path(
        "entity-fields/<uuid:field_id>/",
        FieldDefinitionDetailAPIView.as_view(),
        name="field-detail",
    ),
    path(
        "entity-fields/<uuid:field_id>/update/",
        FieldDefinitionUpdateAPIView.as_view(),
        name="field-update",
    ),
    path(
        "entity-fields/<uuid:field_id>/deactivate/",
        FieldDefinitionDeactivateAPIView.as_view(),
        name="field-deactivate",
    ),

    path(
        "entity-records/",
        EntityRecordCreateAPIView.as_view(),
        name="entity-record-create",
    ),

    path(
        "entity-records/<uuid:record_id>/",
        EntityRecordDetailAPIView.as_view(),
        name="entity-record-detail",
    ),
]

from core.api.workflow_views import (
    WorkflowCreateAPIView,
    WorkflowListAPIView,
    WorkflowDetailAPIView,
    WorkflowStepCreateAPIView,
    WorkflowTransitionCreateAPIView,
    WorkflowInstanceCreateAPIView,
    WorkflowInstanceDetailAPIView,
    WorkflowTransitionAPIView,
)

urlpatterns += [
    path(
        "workflows/",
        WorkflowCreateAPIView.as_view(),
        name="workflow-create",
    ),
    path(
        "workflows/list/",
        WorkflowListAPIView.as_view(),
        name="workflow-list",
    ),
    path(
        "workflows/<uuid:workflow_id>/",
        WorkflowDetailAPIView.as_view(),
        name="workflow-detail",
    ),
    path(
        "workflow-steps/",
        WorkflowStepCreateAPIView.as_view(),
        name="workflow-step-create",
    ),
    path(
        "workflow-transitions/",
        WorkflowTransitionCreateAPIView.as_view(),
        name="workflow-transition-create",
    ),
    path(
        "workflow-instances/",
        WorkflowInstanceCreateAPIView.as_view(),
        name="workflow-instance-create",
    ),
    path(
        "workflow-instances/<uuid:instance_id>/",
        WorkflowInstanceDetailAPIView.as_view(),
        name="workflow-instance-detail",
    ),
    path(
        "workflow-instances/<uuid:instance_id>/transition/",
        WorkflowTransitionAPIView.as_view(),
        name="workflow-instance-transition",
    ),
]


from core.api.workflow_management_views import (
    WorkflowUpdateAPIView,
    WorkflowDeactivateAPIView,
    WorkflowDeleteAPIView,
    WorkflowStepListAPIView,
    WorkflowTransitionListAPIView,
    WorkflowInstanceListAPIView,
    WorkflowInstanceHistoryAPIView,
)

from core.api.workflow_condition_views import (
    WorkflowConditionCreateAPIView,
    WorkflowConditionListAPIView,
)

urlpatterns += [
    path(
        "workflows/<uuid:workflow_id>/update/",
        WorkflowUpdateAPIView.as_view(),
        name="workflow-update",
    ),
    path(
        "workflows/<uuid:workflow_id>/deactivate/",
        WorkflowDeactivateAPIView.as_view(),
        name="workflow-deactivate",
    ),
    path(
        "workflows/<uuid:workflow_id>/delete/",
        WorkflowDeleteAPIView.as_view(),
        name="workflow-delete",
    ),
    path(
        "workflow-steps/list/",
        WorkflowStepListAPIView.as_view(),
        name="workflow-step-list",
    ),
    path(
        "workflow-transitions/list/",
        WorkflowTransitionListAPIView.as_view(),
        name="workflow-transition-list",
    ),
    path(
        "workflow-instances/list/",
        WorkflowInstanceListAPIView.as_view(),
        name="workflow-instance-list",
    ),
    path(
        "workflow-instances/<uuid:instance_id>/history/",
        WorkflowInstanceHistoryAPIView.as_view(),
        name="workflow-instance-history",
    ),
path(
    "workflow-conditions/",
    WorkflowConditionCreateAPIView.as_view(),
    name="workflow-condition-create",
),

path(
    "workflow-conditions/list/",
    WorkflowConditionListAPIView.as_view(),
    name="workflow-condition-list",
),
]


urlpatterns += [
    path(
        "workflow-actions/",
        WorkflowActionCreateAPIView.as_view(),
        name="workflow-action-create",
    ),
    path(
        "workflow-actions/list/",
        WorkflowActionListAPIView.as_view(),
        name="workflow-action-list",
    ),
]
