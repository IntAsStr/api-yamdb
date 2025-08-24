from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404

from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend

from reviews.models import Category, Comments, Genre, Review, Title
from users.models import CustomUser as User

from .filters import TitleFilter
from .permissions import IsAdmin, IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (
    CategorySerializer,
    CommentsSerializer,
    CustomUserSerializer,
    GenreSerializer,
    ReviewsSerializer,
    TitlesSerializer,
    UserCreationSerializer,
    UserMeSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.

    Только для администраторов. Поддержка поиска по username и email.
    """
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'username'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']

    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    @action(
        detail=False,
        methods=['get', 'patch', 'put'],
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        """Возвращает или обновляет данные текущего пользователя."""
        user = request.user
        if request.method == 'GET':
            serializer = UserMeSerializer(user)
            return Response(serializer.data)

        elif request.method in ['PATCH', 'PUT']:
            serializer = UserMeSerializer(
                user,
                data=request.data,
                partial=request.method == 'PATCH'
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


class CategoryViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet для управления категориями.

    Поддержка создания, удаления и получения списка категорий.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    lookup_field = 'slug'
    http_method_names = ['get', 'post', 'delete']


class GenreViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet для управления жанрами.

    Поддержка создания, удаления и получения списка жанров.
    """
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    lookup_field = 'slug'


class TitlesViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления произведениями.

    Поддержка всех CRUD операций для произведений.
    При создании автоматически связывает категорию и жанры по slug.
    """
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).select_related(
        'category'
    ).prefetch_related(
        'genre'
    )
    serializer_class = TitlesSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TitleFilter
    search_fields = ['name', 'year', 'genre__slug', 'category__slug']
    ordering_fields = ['name', 'year']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']


class ReviewsViewSet(viewsets.ModelViewSet):
    """ViewSet для управления отзывами на произведения."""
    serializer_class = ReviewsSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
    ]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        """Возвращает queryset отзывов для конкретного произведения."""
        title_id = self.kwargs.get('title_id')
        return Review.objects.filter(
            title_id=title_id
        ).select_related('author')

    def perform_create(self, serializer):
        """Создает отзыв для конкретного произведения."""
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)

        if Review.objects.filter(
            title=title, author=self.request.user
        ).exists():
            raise ValidationError("Вы уже оставляли отзыв на это произведение")

        serializer.save(author=self.request.user, title=title)


class CommentsViewSet(viewsets.ModelViewSet):
    """ViewSet для управления комментариями к отзывам"""
    serializer_class = CommentsSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
    ]

    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        """Возвращает queryset комментариев для отзыва."""
        review_id = self.kwargs.get('review_id')
        return Comments.objects.filter(
            review_id=review_id
        ).select_related('author')

    def perform_create(self, serializer):
        """
        Создает комментарий для отзыва.

        Возвращает ошибку 404, если отзыв не найден.
        """
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id)
        serializer.save(author=self.request.user, review=review)


class SignUpView(APIView):
    """
    APIView для регистрации новых пользователей.

    Для подтверждения регистрации отправляется confirmation code на email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserCreationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data.get('email')
        username = serializer.validated_data.get('username')

        user_exists = User.objects.filter(
            username=username,
            email=email
        ).first()

        if user_exists:
            confirm_code = user_exists.confirmation_code

            send_mail(
                'Confirmation code',
                f'Your confirmation code: {confirm_code}',
                None,
                [email],
                fail_silently=False
            )
            return Response(
                {'email': email, 'username': username},
                status=status.HTTP_200_OK
            )

        if User.objects.filter(email=email).exclude(
            username=username
        ).exists():
            return Response(
                {'error': 'Пользователь с таким email уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if User.objects.filter(username=username).exclude(
            email=email
        ).exists():
            return Response(
                {'error': 'Пользователь с таким username уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=None
        )
        confirm_code = default_token_generator.make_token(user)
        user.confirmation_code = confirm_code
        user.save()

        send_mail(
            'Confirmation code',
            f'Your confirmation code: {confirm_code}',
            None,
            [email],
            fail_silently=False
        )
        return Response(
            {'email': email, 'username': username},
            status=status.HTTP_200_OK
        )


class TokenView(APIView):
    """
    APIView для получения JWT токена.

    Замена confirmation code на access token для аутентификации.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')

        if not username or not confirmation_code:
            return Response(
                {'error': 'Необходимо указать username и confirmation_code'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not default_token_generator.check_token(user, confirmation_code):
            return Response(
                {'error': 'Неверный код подтверждения'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.confirmation_code != confirmation_code:
            return Response(
                {'error': 'Неверный код подтверждения'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
        })
