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

