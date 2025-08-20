from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, get_jwt_token, signup

app_name = 'users'

users_router = DefaultRouter()
users_router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('v1/', include(users_router.urls)),
]