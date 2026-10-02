from django.urls import path

from core.api.views import (
    BusinessCreateAPIView,
    EntityDefinitionCreateAPIView,
    EntityDefinitionListAPIView,
    EntityDefinitionDetailAPIView,
    FieldDefinitionCreateAPIView,
    EntityRecordCreateAPIView,
    EntityRecordDetailAPIView,
)


urlpatterns = [
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
