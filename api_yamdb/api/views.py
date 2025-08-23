from django.db.models import Avg
from rest_framework import mixins
from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import viewsets, permissions, status, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from reviews.models import Title, Category, Genre, Review, Comments
from users.models import CustomUser as User
from .serializers import (
    TitlesSerializer, CategorySerializer, GenreSerializer,
    ReviewsSerializer, CommentsSerializer, CustomUserSerializer,
    UserMeSerializer, UserCreationSerializer,
)
from .permissions import (
    IsAdminOrReadOnly, IsAuthorOrReadOnly, IsAdmin, IsModerator
)


class StandardPagination(PageNumberPagination):
    """Стандартная пагинация для API."""
    page_size = 10


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
    pagination_class = StandardPagination
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

    def perform_create(self, serializer):
        serializer.save()


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

    def perform_create(self, serializer):
        serializer.save()


class TitlesViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления произведениями.

    Поддержка всех CRUD операций для произведений.
    При создании автоматически связывает категорию и жанры по slug.
    """
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    )
    serializer_class = TitlesSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'year', 'genre__slug', 'category__slug']
    ordering_fields = ['name', 'year']

    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = super().get_queryset()

        genre_slug = self.request.query_params.get('genre')
        if genre_slug:
            queryset = queryset.filter(genre__slug=genre_slug)

        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)

        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save()


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
        return Review.objects.filter(title_id=title_id)

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
        return Comments.objects.filter(review_id=review_id)

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
            confirm_code = default_token_generator.make_token(user_exists)
            user_exists.confirmation_code = confirm_code
            user_exists.save()

            send_mail(
                'Confirmation code',
                f'Your new code {confirm_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False
            )
            return Response(
                {'email': email, 'username': username},
                status=status.HTTP_200_OK
            )

        if User.objects.filter(email=email).exclude(username=username).exists():
            return Response(
                {'error': 'Пользователь с таким email уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if User.objects.filter(username=username).exclude(email=email).exists():
            return Response(
                {'error': 'Пользователь с таким username уже существует'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
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
                f'Your code {confirm_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False
            )
            return Response(
                {'email': email, 'username': username},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
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

        if user.confirmation_code == confirmation_code:
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
            })
        else:
            return Response(
                {'error': 'Неверный код подтверждения'},
                status=status.HTTP_400_BAD_REQUEST
            )
