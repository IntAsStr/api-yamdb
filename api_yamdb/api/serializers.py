from rest_framework import serializers

from users.models import CustomUser as User
from review.models import Titles, Category, Genre, Comments, Reviews


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'bio', 'role')
        read_only_fields = ('role',)

    def create(self, validated_data):
        # Создаем пользователя с правильной ролью
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=None,
            role=validated_data.get('role', 'user')
        )
        return user


class UserMeSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для редактирования своего профиля"""
    role = serializers.CharField(read_only=True)
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'bio')
        read_only_fields = ('username', 'email', 'role')  # Логин и email нельзя менять самому


class TitlesSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
        required=False,
        allow_null=True
    )
    
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True,
        required=False
    )
    class Meta:
        model = Titles
        fields = ('id', 'title', 'year', 'description', 'category', 'genre')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'title', 'slug')

    def validate_slug(self, value):
        # Кастомная валидация slug
        if not value.islower():
            raise serializers.ValidationError("Slug должен быть в нижнем регистре")
        return value
    

class CommentsSerializer(serializers.ModelSerializer):
    # показывать username вместо id
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    class Meta:
        model = Comments
        fields = ('id', 'author', 'review', 'text', 'pub_date')


class ReviewsSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    class Meta:
        model = Reviews
        fields = ('id', 'title', 'text', 'score', 'author', 'pub_date')
        read_only_fields = ('author', 'pub_date')
    
    def validate_score(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Оценка должна быть от 1 до 10")
        return value


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'title', 'slug')


class UserCreationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True)

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError("Нельзя использовать 'me' как username")
        if len(value) > 150:
            raise serializers.ValidationError("Username не может быть длиннее 150 символов")
        return value
    
    def validate_email(self, value):
        if len(value) > 254:
            raise serializers.ValidationError("Email не может быть длиннее 254 символов")
        return value