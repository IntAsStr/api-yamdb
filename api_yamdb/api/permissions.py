from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешает чтение всем, а изменения только администраторам."""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and request.user.is_admin)
        )


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Чтение для всех, изменение только для автора, админа или модератора."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            obj.author == request.user
            or request.user.is_admin
            or request.user.is_moderator
        )


class IsAdmin(permissions.BasePermission):
    """Доступ только для администраторов."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsModerator(permissions.BasePermission):
    """Доступ только для модераторов."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_moderator
