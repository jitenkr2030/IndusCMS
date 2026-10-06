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


from core.api.workflow_action_management_views import (
    WorkflowActionUpdateAPIView,
    WorkflowActionDeactivateAPIView,
    WorkflowActionDeleteAPIView,
    WorkflowActionReorderAPIView,
)

from core.api.workflow_action_views import (
    WorkflowActionCreateAPIView,
    WorkflowActionListAPIView,
)

from core.api.workflow_action_execution_views import (
    WorkflowActionExecutionListAPIView,
    WorkflowActionExecutionDetailAPIView,
    WorkflowActionExecutionRetryAPIView,
)

from core.api.workflow_trigger_views import (
    WorkflowTriggerCreateAPIView,
    WorkflowTriggerListAPIView,
    WorkflowTriggerUpdateAPIView,
    WorkflowTriggerDeactivateAPIView,
    WorkflowTriggerDeleteAPIView,
)

urlpatterns = [

    path(
        "workflow-triggers/",
        WorkflowTriggerCreateAPIView.as_view(),
        name="workflow-trigger-create",
    ),
    path(
        "workflow-triggers/list/",
        WorkflowTriggerListAPIView.as_view(),
        name="workflow-trigger-list",
    ),
    path(
        "workflow-triggers/<uuid:trigger_id>/update/",
        WorkflowTriggerUpdateAPIView.as_view(),
        name="workflow-trigger-update",
    ),
    path(
        "workflow-triggers/<uuid:trigger_id>/deactivate/",
        WorkflowTriggerDeactivateAPIView.as_view(),
        name="workflow-trigger-deactivate",
    ),
    path(
        "workflow-triggers/<uuid:trigger_id>/delete/",
        WorkflowTriggerDeleteAPIView.as_view(),
        name="workflow-trigger-delete",
    ),
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

from core.api.workflow_condition_management_views import (
    WorkflowConditionUpdateAPIView,
    WorkflowConditionDeactivateAPIView,
    WorkflowConditionDeleteAPIView,
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
        "workflow-action-executions/",
        WorkflowActionExecutionListAPIView.as_view(),
        name="workflow-action-execution-list",
    ),
    path(
        "workflow-action-executions/<uuid:execution_id>/",
        WorkflowActionExecutionDetailAPIView.as_view(),
        name="workflow-action-execution-detail",
    ),
    path(
        "workflow-action-executions/<uuid:execution_id>/retry/",
        WorkflowActionExecutionRetryAPIView.as_view(),
        name="workflow-action-execution-retry",
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


urlpatterns += [
    path("workflow-conditions/<uuid:condition_id>/update/", WorkflowConditionUpdateAPIView.as_view(), name="workflow-condition-update"),
    path("workflow-conditions/<uuid:condition_id>/deactivate/", WorkflowConditionDeactivateAPIView.as_view(), name="workflow-condition-deactivate"),
    path("workflow-conditions/<uuid:condition_id>/delete/", WorkflowConditionDeleteAPIView.as_view(), name="workflow-condition-delete"),
    path("workflow-actions/<uuid:action_id>/update/", WorkflowActionUpdateAPIView.as_view(), name="workflow-action-update"),
    path("workflow-actions/<uuid:action_id>/deactivate/", WorkflowActionDeactivateAPIView.as_view(), name="workflow-action-deactivate"),
    path("workflow-actions/<uuid:action_id>/delete/", WorkflowActionDeleteAPIView.as_view(), name="workflow-action-delete"),
    path("workflow-actions/<uuid:action_id>/reorder/", WorkflowActionReorderAPIView.as_view(), name="workflow-action-reorder"),
]