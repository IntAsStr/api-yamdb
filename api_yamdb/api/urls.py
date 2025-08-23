from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('users', views.UserViewSet, basename='users')
router.register('categories', views.CategoryViewSet)
router.register('genres', views.GenreViewSet)
router.register('titles', views.TitlesViewSet)
router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    views.ReviewsViewSet,
    basename='reviews'
)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    views.CommentsViewSet,
    basename='comments'
)

urlpatterns = [
    path('auth/signup/', views.SignUpView.as_view(), name='signup'),
    path('auth/token/', views.TokenView.as_view(), name='token'),
    path('', include(router.urls)),
]
