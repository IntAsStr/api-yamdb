from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение всем пользователям, а изменения только администраторам.

    Разрешает безопасные методы (GET, HEAD, OPTIONS) для всех,
    а изменяющие методы (POST, PUT, PATCH, DELETE)
    только аутентифицированным администраторам.
    """
    def has_permission(self, request, view):
        """
        Проверяет права доступа для запроса.

        Args:
            request: HTTP запрос.
            view: ViewSet или APIView.

        Returns:
            bool: True если разрешено, False если запрещено.
        """
        return (
            request.method in permissions.SAFE_METHODS or
            (request.user.is_authenticated and request.user.is_admin)
        )


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение всем пользователям, а изменения- только автору объекта.

    Разрешает безопасные методы всем,
    а изменяющие методы только автору объекта.
    """
    def has_object_permission(self, request, view, obj):
        """
        Проверяет права доступа для конкретного объекта.

        Args:
            request: HTTP запрос.
            view: ViewSet или APIView.
            obj: Объект для проверки прав.

        Returns:
            bool: True если разрешено, False если запрещено.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            obj.author == request.user
            or request.user.is_admin
            or request.user.is_moderator
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission для разрешения доступа только администраторам.

    Полный доступ только аутентифицированным пользователям
    с ролью администратора.
    """
    def has_permission(self, request, view):
        """
        Проверяет, является ли пользователь администратором.

        Args:
            request: HTTP запрос
            view: ViewSet или APIView

        Returns:
            bool: если пользователь аутентифицирован
            и является администратором - True.
        """
        return request.user.is_authenticated and request.user.is_admin


class IsModerator(permissions.BasePermission):
    """
    Permission для разрешения доступа только модераторам.

    Полный доступ только аутентифицированным пользователям с ролью модератора.
    """
    def has_permission(self, request, view):
        """
        Проверяет, является ли пользователь модератором.

        Args:
            request: HTTP запрос.
            view: ViewSet или APIView.

        Returns:
            bool: если пользователь аутентифицирован
            и является модератором - True.
        """
        return request.user.is_authenticated and request.user.is_moderator
