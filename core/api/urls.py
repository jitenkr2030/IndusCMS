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
