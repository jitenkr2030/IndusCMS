from django.db import transaction
from django.utils.text import slugify

from core.models import (
    Business,
    BusinessSettings,
    Membership,
    Permission,
    Role,
    RolePermission,
)
from core.services.audit import log_action


@transaction.atomic
def create_business_for_user(
    user,
    name,
    industry="",
    email="",
    phone="",
    website="",
    address="",
    city="",
    state="",
    country="India",
    ip_address=None,
):
    if not user or not user.is_authenticated:
        raise ValueError("Authenticated user is required.")

    name = name.strip()

    if not name:
        raise ValueError("Business name is required.")

    base_slug = slugify(name) or "business"
    slug = base_slug
    counter = 2

    while Business.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    business = Business.objects.create(
        name=name,
        slug=slug,
        industry=industry,
        email=email,
        phone=phone,
        website=website,
        address=address,
        city=city,
        state=state,
        country=country,
    )

    BusinessSettings.objects.create(
        business=business,
        currency="INR",
        timezone="Asia/Kolkata",
        date_format="DD-MM-YYYY",
    )

    owner_role = Role.objects.create(
        business=business,
        name="Owner",
        slug="owner",
        description="Full access to the business.",
        is_system=True,
    )

    permissions = Permission.objects.all()

    RolePermission.objects.bulk_create(
        [
            RolePermission(
                role=owner_role,
                permission=permission,
            )
            for permission in permissions
        ],
        ignore_conflicts=True,
    )

    membership = Membership.objects.create(
        user=user,
        business=business,
        role=owner_role,
        is_active=True,
    )

    log_action(
        business=business,
        user=user,
        action="business.created",
        resource="business",
        object_id=business.pk,
        ip_address=ip_address,
        metadata={
            "name": business.name,
            "slug": business.slug,
            "industry": business.industry,
        },
    )

    return business, membership
