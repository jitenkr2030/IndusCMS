from core.models import Membership


def get_membership(user, business):
    """
    Return the active membership of a user in a business.
    """
    if not user or not user.is_authenticated:
        return None

    return (
        Membership.objects
        .select_related("role")
        .filter(
            user=user,
            business=business,
            is_active=True,
        )
        .first()
    )


def user_can(user, business, permission_code):
    """
    Check whether a user has a specific permission
    inside a specific business.

    Example:
        user_can(user, business, "customers.create")
    """

    if not user or not user.is_authenticated:
        return False

    # Django superusers have full access.
    if user.is_superuser:
        return True

    membership = get_membership(user, business)

    if not membership or not membership.role:
        return False

    return membership.role.role_permissions.filter(
        permission__code=permission_code
    ).exists()


def has_role(user, business, role_slug):
    """
    Check whether a user has a particular role
    inside a business.
    """

    membership = get_membership(user, business)

    if not membership or not membership.role:
        return False

    return membership.role.slug == role_slug
