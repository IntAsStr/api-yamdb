from django.core.validators import RegexValidator

from rest_framework import serializers

from reviews.models import Category, Comment, Genre, Review, Title
from users.models import CustomUser as User


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели пользователя.

    Применяется для создания и отображения данных пользователя,
    включая все основные поля профиля.
    """
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=None,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            bio=validated_data.get('bio', ''),
            role=validated_data.get('role', 'user')
        )
        return user


class UserMeSerializer(serializers.ModelSerializer):
    """
    Упрощенный сериализатор для редактирования своего профиля.

    Поле role только для чтения.
    Пользователи не могут сами менять свою роль.
    """
    role = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )
        read_only_fields = ('role',)


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий произведений."""
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для жанров произведений."""
    class Meta:
        model = Genre
        fields = ('name', 'slug')

    def validate_slug(self, value):
        if not value.islower():
            raise serializers.ValidationError(
                "Slug должен быть в нижнем регистре."
            )
        return value


class TitlesSerializer(serializers.ModelSerializer):
    """
    Сериализатор для произведений.
    """
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
        write_only=True
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True,
        write_only=True
    )

    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'description',
            'category', 'genre', 'rating'
        )

    def __init__(self, *args, **kwargs):
        """Динамически меняем поле category в зависимости от операции"""
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        if request and request.method in ['POST', 'PUT', 'PATCH']:
            self.fields['category'] = serializers.SlugRelatedField(
                slug_field='slug',
                queryset=Category.objects.all()
            )
            self.fields['genre'] = serializers.SlugRelatedField(
                slug_field='slug',
                queryset=Genre.objects.all(),
                many=True
            )
        else:
            self.fields['category'] = CategorySerializer(read_only=True)
            self.fields['genre'] = GenreSerializer(many=True, read_only=True)


class CommentsSerializer(serializers.ModelSerializer):
    """Сериализатор для комментариев к отзывам."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ('id', 'author', 'review', 'text', 'pub_date')


class ReviewsSerializer(serializers.ModelSerializer):
    """Сериализатор для отзывов на произведения."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'score', 'author', 'pub_date')
        read_only_fields = ('author', 'pub_date')

    def validate_rating(self, value):
        """Валидация оценки отзыва."""
        if value < 1 or value > 10:
            raise serializers.ValidationError("Оценка должна быть от 1 до 10")
        return value


class UserCreationSerializer(serializers.Serializer):
    """
    Сериализатор для создания пользователя при регистрации.

    Валилирует email и username при первоначальной регистрации.
    """
    email = serializers.EmailField(required=True)
    username = serializers.CharField(
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Username содержит недопустимые символы'
            )
        ]
    )

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                "Нельзя использовать 'me' как username"
            )
        if len(value) > 150:
            raise serializers.ValidationError(
                "Username не может быть длиннее 150 символов"
            )
        return value

    def validate_email(self, value):
        if len(value) > 254:
            raise serializers.ValidationError(
                "Email не может быть длиннее 254 символов"
            )
        return value
