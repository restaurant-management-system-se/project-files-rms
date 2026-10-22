from rest_framework.permissions import BasePermission
from .models import User


def has_role(user, *roles):
    return bool(user and user.is_authenticated and user.is_active and user.role in roles)


class IsRestaurantAdmin(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, User.Role.ADMIN)


class IsStaffOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, User.Role.STAFF, User.Role.ADMIN)


class IsOwnerOrStaffAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.method != "DELETE" and has_role(request.user, *User.Role.values)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view) and (
            has_role(request.user, User.Role.STAFF, User.Role.ADMIN)
            or obj.customer_id == request.user.pk
        )


def owned_queryset(queryset, user):
    """Always filter lists; DRF object permissions do not filter list results."""
    if has_role(user, User.Role.STAFF, User.Role.ADMIN):
        return queryset
    if has_role(user, User.Role.CUSTOMER):
        return queryset.filter(customer_id=user.pk)
    return queryset.none()
