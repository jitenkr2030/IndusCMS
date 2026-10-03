from core.models import FieldDefinition, RelationshipDefinition
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.serializers import (
    BusinessCreateSerializer,
    BusinessSerializer,
    EntityDefinitionSerializer,
    EntityRecordSerializer,
    FieldDefinitionSerializer,
)
from core.models import Business, EntityDefinition, EntityRecord
from core.services.business import create_business_for_user
from core.services.entity import (
    create_entity_for_business,
    update_entity_for_business,
    deactivate_entity_for_business,
    delete_entity_for_business,
)

from core.services.record import create_record_for_entity

from core.services.field import (
    create_field_for_entity,
    update_field_for_entity,
    deactivate_field_for_entity,
)
from core.services.field import create_field_for_entity
from core.services.record import (
    create_record_for_entity,
    update_record_for_entity,
    delete_record_for_entity,
)
from core.services.permissions import get_membership, user_can


class BusinessCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BusinessCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        business, membership = create_business_for_user(
            user=request.user,
            **serializer.validated_data,
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {
                "success": True,
                "message": "Business created successfully.",
                "business": BusinessSerializer(business).data,
                "membership_id": str(membership.id),
            },
            status=status.HTTP_201_CREATED,
        )


class EntityDefinitionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        business_id = request.data.get("business_id")

        if not business_id:
            return Response(
                {
                    "success": False,
                    "message": "business_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            business = Business.objects.get(
                id=business_id,
                is_active=True,
            )
        except Business.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Active business not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(request.user, business)

        if not membership:
            return Response(
                {
                    "success": False,
                    "message": "You are not an active member of this business.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = EntityDefinitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            entity = create_entity_for_business(
                user=request.user,
                business=business,
                name=serializer.validated_data["name"],
                slug=serializer.validated_data.get("slug", ""),
                description=serializer.validated_data.get(
                    "description", ""
                ),
                is_active=serializer.validated_data.get(
                    "is_active", True
                ),
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PermissionError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Entity created successfully.",
                "entity": EntityDefinitionSerializer(entity).data,
            },
            status=status.HTTP_201_CREATED,
        )


class FieldDefinitionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        entity_id = request.data.get("entity_id")

        if not entity_id:
            return Response(
                {
                    "success": False,
                    "message": "entity_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            entity = EntityDefinition.objects.select_related(
                "business"
            ).get(
                id=entity_id,
                is_active=True,
                business__is_active=True,
            )
        except EntityDefinition.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Active entity not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = FieldDefinitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            field = create_field_for_entity(
                user=request.user,
                entity=entity,
                name=serializer.validated_data["name"],
                field_type=serializer.validated_data.get(
                    "field_type", "text"
                ),
                slug=serializer.validated_data.get("slug", ""),
                required=serializer.validated_data.get(
                    "required", False
                ),
                unique=serializer.validated_data.get(
                    "unique", False
                ),
                default_value=serializer.validated_data.get(
                    "default_value"
                ),
                choices=serializer.validated_data.get(
                    "choices"
                ),
                position=serializer.validated_data.get(
                    "position", 0
                ),
                is_active=serializer.validated_data.get(
                    "is_active", True
                ),
                is_system=serializer.validated_data.get(
                    "is_system", False
                ),
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PermissionError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Field created successfully.",
                "field": FieldDefinitionSerializer(field).data,
            },
            status=status.HTTP_201_CREATED,
        )


class EntityRecordCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        entity_id = request.data.get("entity_id")

        if not entity_id:
            return Response(
                {
                    "success": False,
                    "message": "entity_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            entity = EntityDefinition.objects.select_related(
                "business"
            ).get(
                id=entity_id,
                is_active=True,
                business__is_active=True,
            )
        except EntityDefinition.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Active entity not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(
            request.user,
            entity.business,
        )

        if not membership:
            return Response(
                {
                    "success": False,
                    "message": "You are not an active member of this business.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = EntityRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            record = create_record_for_entity(
                user=request.user,
                entity=entity,
                data=serializer.validated_data["data"],
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PermissionError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Record created successfully.",
                "record": EntityRecordSerializer(record).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        from django.core.exceptions import ValidationError
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

        entity_id = request.query_params.get("entity_id")

        if not entity_id:
            return Response(
                {"success": False, "message": "entity_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            entity = EntityDefinition.objects.select_related(
                "business"
            ).get(
                id=entity_id,
                is_active=True,
                business__is_active=True,
            )
        except (EntityDefinition.DoesNotExist, ValidationError, ValueError):
            return Response(
                {"success": False, "message": "Active entity not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(request.user, entity.business)

        if not membership:
            return Response(
                {
                    "success": False,
                    "message": "You are not an active member of this business.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(request.user, entity.business, "entity.view"):
            return Response(
                {
                    "success": False,
                    "message": "You do not have permission to view entity records.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            page_number = int(request.query_params.get("page", "1"))
            page_size = int(request.query_params.get("page_size", "20"))

            if page_number < 1:
                raise ValueError

            if page_size < 1 or page_size > 100:
                raise ValueError

        except (ValueError, TypeError):
            return Response(
                {
                    "success": False,
                    "message": "page must be positive; page_size must be between 1 and 100.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = EntityRecord.objects.filter(
            entity=entity,
            is_deleted=False,
        ).select_related("created_by").order_by("-created_at", "-id")

        paginator = Paginator(records, page_size)

        try:
            page_obj = paginator.page(page_number)
        except EmptyPage:
            return Response(
                {
                    "success": False,
                    "message": "Requested page does not exist.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "success": True,
                "pagination": {
                    "count": paginator.count,
                    "page": page_obj.number,
                    "page_size": page_size,
                    "total_pages": paginator.num_pages,
                    "next_page": (
                        page_obj.next_page_number()
                        if page_obj.has_next()
                        else None
                    ),
                    "previous_page": (
                        page_obj.previous_page_number()
                        if page_obj.has_previous()
                        else None
                    ),
                },
                "results": EntityRecordSerializer(
                    page_obj.object_list,
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class EntityRecordDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            record = EntityRecord.objects.select_related(
                "entity",
                "entity__business",
                "created_by",
            ).get(
                id=record_id,
                is_deleted=False,
                entity__is_active=True,
                entity__business__is_active=True,
            )
        except (EntityRecord.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Entity record not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        business = record.entity.business

        membership = get_membership(
            request.user,
            business,
        )

        if not membership:
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not an active member of this business."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            business,
            "entity.view",
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You do not have permission to view entity records."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "success": True,
                "record": EntityRecordSerializer(record).data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, record_id):
        try:
            record = EntityRecord.objects.select_related(
                "entity",
                "entity__business",
                "created_by",
            ).get(
                id=record_id,
                entity__is_active=True,
                entity__business__is_active=True,
            )
        except (EntityRecord.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Entity record not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        business = record.entity.business

        membership = get_membership(
            request.user,
            business,
        )

        if not membership:
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not an active member of this business."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = EntityRecordSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        try:
            updated_record = update_record_for_entity(
                user=request.user,
                record=record,
                data=serializer.validated_data["data"],
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PermissionError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Record updated successfully.",
                "record": EntityRecordSerializer(
                    updated_record
                ).data,
            },
            status=status.HTTP_200_OK,
        )


    def delete(self, request, record_id):
        try:
            record = EntityRecord.objects.select_related(
                "entity",
                "entity__business",
                "created_by",
                "deleted_by",
            ).get(
                id=record_id,
                entity__is_active=True,
                entity__business__is_active=True,
            )
        except (EntityRecord.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Entity record not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            deleted_record = delete_record_for_entity(
                user=request.user,
                record=record,
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PermissionError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Record deleted successfully.",
                "record": {
                    "id": str(deleted_record.id),
                    "is_deleted": deleted_record.is_deleted,
                    "deleted_at": deleted_record.deleted_at,
                    "deleted_by": (
                        deleted_record.deleted_by_id
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


class EntityDefinitionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business_id = request.query_params.get("business_id")

        if not business_id:
            return Response(
                {
                    "success": False,
                    "message": "business_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            business = Business.objects.get(
                id=business_id,
                is_active=True,
            )
        except (Business.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Active business not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(
            request.user,
            business,
        )

        if not membership:
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not an active member of this business."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            business,
            "entity.view",
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You do not have permission to view entities."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        entities = EntityDefinition.objects.filter(
            business=business,
            is_active=True,
        ).order_by("name", "id")

        return Response(
            {
                "success": True,
                "count": entities.count(),
                "results": EntityDefinitionSerializer(
                    entities,
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class EntityDefinitionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, entity_id):
        try:
            entity = EntityDefinition.objects.select_related(
                "business"
            ).get(
                id=entity_id,
                is_active=True,
                business__is_active=True,
            )
        except (EntityDefinition.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Active entity not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(
            request.user,
            entity.business,
        )

        if not membership:
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not an active member "
                        "of this business."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(
            request.user,
            entity.business,
            "entity.view",
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You do not have permission "
                        "to view entities."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "success": True,
                "entity": EntityDefinitionSerializer(
                    entity
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, entity_id):
        try:
            entity = EntityDefinition.objects.select_related(
                "business"
            ).get(
                id=entity_id,
                is_active=True,
                business__is_active=True,
            )
        except (EntityDefinition.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Active entity not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(
            request.user,
            entity.business,
        )

        if not membership:
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not an active member "
                        "of this business."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        allowed_fields = {
            "name",
            "slug",
            "description",
        }

        invalid_fields = set(request.data.keys()) - allowed_fields

        if invalid_fields:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Unsupported fields: "
                        + ", ".join(sorted(invalid_fields))
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            entity = update_entity_for_business(
                user=request.user,
                entity=entity,
                name=request.data.get("name"),
                slug=request.data.get("slug"),
                description=request.data.get("description"),
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PermissionError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Entity updated successfully.",
                "entity": EntityDefinitionSerializer(
                    entity
                ).data,
            },
            status=status.HTTP_200_OK,
        )



class EntityDefinitionDeactivateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, entity_id):
        try:
            entity = EntityDefinition.objects.select_related(
                "business"
            ).get(
                id=entity_id,
                business__is_active=True,
            )
        except (EntityDefinition.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Entity not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = get_membership(
            request.user,
            entity.business,
        )

        if not membership:
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not an active member "
                        "of this business."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            entity = deactivate_entity_for_business(
                user=request.user,
                entity=entity,
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PermissionError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Entity deactivated successfully.",
                "entity": EntityDefinitionSerializer(
                    entity
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class EntityDefinitionDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, entity_id):
        try:
            entity = EntityDefinition.objects.select_related(
                "business"
            ).get(
                id=entity_id,
                business__is_active=True,
            )
        except (EntityDefinition.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Entity not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not get_membership(request.user, entity.business):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not an active member "
                        "of this business."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            delete_entity_for_business(
                user=request.user,
                entity=entity,
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PermissionError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Entity deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )


class FieldDefinitionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entity_id = request.query_params.get("entity_id")

        if not entity_id:
            return Response(
                {"success": False, "message": "entity_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            entity = EntityDefinition.objects.select_related(
                "business"
            ).get(
                id=entity_id,
                is_active=True,
                business__is_active=True,
            )
        except (EntityDefinition.DoesNotExist, ValueError):
            return Response(
                {"success": False, "message": "Active entity not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not get_membership(request.user, entity.business):
            return Response(
                {"success": False,
                 "message": "You are not an active member of this business."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(request.user, entity.business, "entity.view"):
            return Response(
                {"success": False,
                 "message": "You do not have permission to view entities."},
                status=status.HTTP_403_FORBIDDEN,
            )

        fields = entity.fields.filter(
            is_active=True
        ).order_by("position", "created_at")

        return Response(
            {
                "success": True,
                "count": fields.count(),
                "results": FieldDefinitionSerializer(
                    fields, many=True
                ).data,
            }
        )


class FieldDefinitionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, field_id):
        try:
            field = FieldDefinition.objects.select_related(
                "entity__business"
            ).get(
                id=field_id,
                is_active=True,
                entity__is_active=True,
                entity__business__is_active=True,
            )
        except (FieldDefinition.DoesNotExist, ValueError):
            return Response(
                {"success": False, "message": "Active field not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        business = field.entity.business

        if not get_membership(request.user, business):
            return Response(
                {"success": False,
                 "message": "You are not an active member of this business."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(request.user, business, "entity.view"):
            return Response(
                {"success": False,
                 "message": "You do not have permission to view fields."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response({
            "success": True,
            "field": FieldDefinitionSerializer(field).data,
        })


class FieldDefinitionUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, field_id):
        try:
            field = FieldDefinition.objects.select_related(
                "entity__business"
            ).get(
                id=field_id,
                entity__business__is_active=True,
            )
        except (FieldDefinition.DoesNotExist, ValueError):
            return Response(
                {"success": False, "message": "Field not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        allowed = {
            "name", "slug", "field_type", "required",
            "unique", "default_value", "choices", "position",
        }

        unsupported = set(request.data.keys()) - allowed
        if unsupported:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Unsupported field(s): "
                        + ", ".join(sorted(unsupported))
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            field = update_field_for_entity(
                user=request.user,
                field=field,
                **{
                    key: request.data[key]
                    for key in allowed
                    if key in request.data
                },
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PermissionError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "success": True,
            "message": "Field updated successfully.",
            "field": FieldDefinitionSerializer(field).data,
        })


class FieldDefinitionDeactivateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, field_id):
        try:
            field = FieldDefinition.objects.select_related(
                "entity__business"
            ).get(
                id=field_id,
                entity__business__is_active=True,
            )
        except (FieldDefinition.DoesNotExist, ValueError):
            return Response(
                {"success": False, "message": "Field not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            field = deactivate_field_for_entity(
                user=request.user,
                field=field,
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PermissionError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "success": True,
            "message": "Field deactivated successfully.",
            "field": FieldDefinitionSerializer(field).data,
        })


class RelationshipOptionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, relationship_id):
        from core.models import RelationshipDefinition, EntityRecord
        from core.services.permissions import get_membership, user_can

        try:
            relationship = RelationshipDefinition.objects.select_related(
                "business", "source_entity", "target_entity"
            ).get(
                id=relationship_id,
                is_active=True,
                business__is_active=True,
            )
        except (RelationshipDefinition.DoesNotExist, ValueError):
            return Response(
                {"success": False, "message": "Active relationship not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        business = relationship.business

        if not get_membership(request.user, business):
            return Response(
                {"success": False, "message": "You are not an active member of this business."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(request.user, business, "entity.view"):
            return Response(
                {"success": False, "message": "You do not have permission to view entities."},
                status=status.HTTP_403_FORBIDDEN,
            )

        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
        search = request.query_params.get("search", "").strip()

        queryset = EntityRecord.objects.filter(
            entity=relationship.target_entity,
            is_deleted=False,
        ).order_by("-created_at")

        if search:
            queryset = queryset.filter(
                data__icontains=search
            )

        total = queryset.count()
        start = (page - 1) * page_size
        records = queryset[start:start + page_size]

        return Response({
            "success": True,
            "relationship": {
                "id": str(relationship.id),
                "name": relationship.name,
                "slug": relationship.slug,
                "relationship_type": relationship.relationship_type,
                "target_entity": str(relationship.target_entity_id),
                "target_entity_name": relationship.target_entity.name,
            },
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
                "has_next": start + page_size < total,
                "has_previous": page > 1,
            },
            "options": [
                {
                    "id": str(record.id),
                    "data": record.data,
                    "created_at": record.created_at,
                    "updated_at": record.updated_at,
                }
                for record in records
            ],
        })


class EntityDynamicFormAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, entity_id):
        try:
            entity = EntityDefinition.objects.select_related(
                "business"
            ).get(
                id=entity_id,
                is_active=True,
                business__is_active=True,
            )
        except (EntityDefinition.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Active entity not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        business = entity.business

        if not get_membership(request.user, business):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not an active member of this business."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(request.user, business, "entity.view"):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You do not have permission to view entities."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        fields = entity.fields.filter(
            is_active=True
        ).order_by("position", "created_at")
        relationships = RelationshipDefinition.objects.filter(
            source_entity=entity,
            is_active=True,
        ).select_related("target_entity").order_by("name")

        return Response(
            {
                "success": True,
                "entity": {
                    "id": str(entity.id),
                    "name": entity.name,
                    "slug": entity.slug,
                    "description": entity.description,
                },
                "relationships": [{"id": str(r.id), "name": r.name, "slug": r.slug, "field_type": "relationship", "required": r.required, "relationship_type": r.relationship_type, "target_entity": str(r.target_entity_id), "target_entity_name": r.target_entity.name, "options_url": f"/api/relationships/{r.id}/options/"} for r in relationships],
            "fields": [
                    {
                        "id": str(field.id),
                        "name": field.name,
                        "slug": field.slug,
                        "field_type": field.field_type,
                        "required": field.required,
                        "unique": field.unique,
                        "default_value": field.default_value,
                        "choices": field.choices,
                        "position": field.position,
                    }
                    for field in fields
                ],
            }
        )

    def post(self, request, entity_id):
        try:
            entity = EntityDefinition.objects.select_related(
                "business"
            ).get(
                id=entity_id,
                is_active=True,
                business__is_active=True,
            )
        except (EntityDefinition.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Active entity not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        business = entity.business

        if not get_membership(request.user, business):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not an active member of this business."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(request.user, business, "entity.create"):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You do not have permission to create records."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data

        if not isinstance(data, dict):
            return Response(
                {
                    "success": False,
                    "message": "Form data must be a JSON object.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            record = create_record_for_entity(
                user=request.user,
                entity=entity,
                data=data,
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PermissionError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Form submitted successfully.",
                "record": {
                    "id": str(record.id),
                    "entity": str(record.entity_id),
                    "data": record.data,
                    "created_by": (
                        record.created_by_id
                        if record.created_by_id
                        else None
                    ),
                    "created_at": record.created_at,
                    "updated_at": record.updated_at,
                },
            },
            status=status.HTTP_201_CREATED,
        )



class EntityDynamicTableAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, entity_id):
        try:
            entity = EntityDefinition.objects.select_related(
                "business"
            ).get(
                id=entity_id,
                is_active=True,
                business__is_active=True,
            )
        except (EntityDefinition.DoesNotExist, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Active entity not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        business = entity.business

        if not get_membership(request.user, business):
            return Response(
                {
                    "success": False,
                    "message": "You are not an active member of this business.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user_can(request.user, business, "entity.view"):
            return Response(
                {
                    "success": False,
                    "message": "You do not have permission to view entities.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        fields = list(
            entity.fields.filter(is_active=True)
            .order_by("position", "created_at")
        )

        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1

        try:
            page_size = int(request.query_params.get("page_size", 20))
        except ValueError:
            page_size = 20

        page_size = min(max(page_size, 1), 100)

        records = entity.records.filter(
            is_deleted=False
        ).order_by("-created_at")

        search = request.query_params.get("search", "").strip()

        if search:
            from django.db.models import Q

            query = Q()

            for field in fields:
                query |= Q(
                    **{
                        f"data__{field.slug}__icontains": search
                    }
                )

            records = records.filter(query)

        sort = request.query_params.get("sort", "").strip()

        if sort:
            direction = "-" if sort.startswith("-") else ""
            sort_slug = sort.lstrip("-")

            if sort_slug in {
                field.slug for field in fields
            }:
                if sort_slug == "created_at":
                    records = records.order_by(
                        f"{direction}created_at"
                    )
                else:
                    records = records.order_by(
                        f"{direction}data__{sort_slug}"
                    )

        total = records.count()

        total_pages = (
            (total + page_size - 1) // page_size
            if total
            else 1
        )

        if page > total_pages:
            page = total_pages

        start = (page - 1) * page_size
        end = start + page_size

        records = records[start:end]

        return Response(
            {
                "success": True,
                "entity": {
                    "id": str(entity.id),
                    "name": entity.name,
                    "slug": entity.slug,
                },
                "columns": [
                    {
                        "id": str(field.id),
                        "name": field.name,
                        "slug": field.slug,
                        "field_type": field.field_type,
                        "required": field.required,
                        "position": field.position,
                    }
                    for field in fields
                ],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1,
                },
                "rows": [
                    {
                        "id": str(record.id),
                        "data": record.data,
                        "created_by": (
                            record.created_by_id
                            if record.created_by_id
                            else None
                        ),
                        "created_at": record.created_at,
                        "updated_at": record.updated_at,
                    }
                    for record in records
                ],
            }
        )
