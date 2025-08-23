from rest_framework import serializers
from django.core.validators import RegexValidator
from users.models import CustomUser as User
from reviews.models import Title, Category, Genre, Comments, Review


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
        """
        Создает нового пользователя с заданными данными.

        Args:
            validated_data: Валидированные данные пользователя.
                - username: Имя пользователя,
                - email: Email адрес,
                - first_name: Имя (опционально),
                - last_name: Фамилия (опционально),
                - bio: Биография (опционально),
                - role: Роль пользователя (по умолчанию 'user').

        Returns:
            User: Созданный объект пользователя.
        """
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

    def validate_username(self, value):
        """
        Валидация имени пользователя.

        Args:
            value: Проверяемое имя пользователя.

        Returns:
            str: Валидное имя пользователя.

        Raises:
            ValidationError: Если имя пользователя невалидно.
        """
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
        """
        Валидация email адреса.

        Args:
            value: Проверяемый email адрес.

        Returns:
            str: Валидный email адрес.

        Raises:
            ValidationError: Если email невалиден.
        """
        if len(value) > 254:
            raise serializers.ValidationError(
                "Email не может быть длиннее 254 символов"
            )
        return value


class TitlesSerializer(serializers.ModelSerializer):
    """
    Сериализатор для произведений.

    Включает связанные поля категории и жанров через slug,
    а также вычисляемое поле рейтинга.
    """
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
        required=True
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True,
        required=True
    )
    rating = serializers.FloatField(read_only=True, allow_null=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'description', 'category', 'genre', 'rating')

    def to_representation(self, instance):
        """
        Преобразует объект в словарь для сериализации.

        Заменяет slug категорий и жанров на полные объекты
        с названиями и слагами.
        """
        representation = super().to_representation(instance)

        representation['category'] = {
            'name': instance.category.name,
            'slug': instance.category.slug
        }

        representation['genre'] = [
            {'name': genre.name, 'slug': genre.slug}
            for genre in instance.genre.all()
        ]

        return representation


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий произведений."""
    class Meta:
        model = Category
        fields = ('name', 'slug')


class CommentsSerializer(serializers.ModelSerializer):
    """Сериализатор для комментариев к отзывам."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comments
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


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для жанров произведений."""
    class Meta:
        model = Genre
        fields = ('name', 'slug')

    def validate_slug(self, value):
        if not value.islower():
            raise serializers.ValidationError("Slug должен быть в нижнем регистре.")
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
            raise serializers.ValidationError("Нельзя использовать 'me' как username")
        if len(value) > 150:
            raise serializers.ValidationError("Username не может быть длиннее 150 символов")
        return value

    def validate_email(self, value):
        if len(value) > 254:
            raise serializers.ValidationError("Email не может быть длиннее 254 символов")
        return value
