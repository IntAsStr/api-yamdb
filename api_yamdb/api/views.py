from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.shortcuts import get_object_or_404
from review.models import Titles, Category, Genre, Reviews, Comments
from users.models import CustomUser as User
from .serializers import (
    TitlesSerializer, CategorySerializer, GenreSerializer,
    ReviewsSerializer, CommentsSerializer, CustomUserSerializer,
    UserMeSerializer, UserCreationSerializer,
)
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly, IsAdmin, IsModerator


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'username'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']

    @action(
        detail=False,
        methods=['get', 'patch', 'put'],
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = UserMeSerializer(user)
            return Response(serializer.data)
        
        elif request.method in ['PATCH', 'PUT']:
            serializer = UserMeSerializer(
                user, 
                data=request.data, 
                partial=request.method == 'PATCH'  # partial только для PATCH
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'


class TitlesViewSet(viewsets.ModelViewSet):
    queryset = Titles.objects.all()
    serializer_class = TitlesSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        category = get_object_or_404(Category, slug=self.request.data.get('category'))
        genre = Genre.objects.filter(slug__in=self.request.data.getlist('genre'))
        serializer.save(category=category, genre=genre)


class ReviewsViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        return Reviews.objects.filter(title_id=title_id)

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Titles, id=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentsViewSet(viewsets.ModelViewSet):
    serializer_class = CommentsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        review_id = self.kwargs.get('review_id')
        return Comments.objects.filter(review_id=review_id)

    def perform_create(self, serializer):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Reviews, id=review_id)
        serializer.save(author=self.request.user, review=review)


class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserCreationSerializer(data=request.data)

        if not serializer.is_valid():  # ← ЕСЛИ НЕ ВАЛИДНО
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            username = serializer.validated_data.get('username')

            if User.objects.filter(email=email).exists():
                return Response(
                    {'error': 'Пользователь с таким email уже существует'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if User.objects.filter(username=username).exists():
                return Response(
                    {'error': 'Пользователь с таким username уже существует'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=None  # пароль не нужен для начальной регистрации
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
                serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if user.confirmation_code == confirmation_code:
            # Генерация JWT токена
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
            })
        
        return Response(
            {'error': 'Неверный код подтверждения'},
            status=status.HTTP_400_BAD_REQUEST
        )
