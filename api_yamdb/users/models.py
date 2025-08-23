from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя.

    Основное поле для аутентификации - email.
    Также дабавляет дополнительные поля- роли, биографии и кода подтверждения.
    """
    CHOICES = [
        ('user', 'user'),
        ('admin', 'admin'),
        ('moderator', 'moderator'),
    ]
    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True,
        blank=False,
        null=False,
        help_text='Уникальный email адрес пользователя'
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=150,
        unique=True,
        blank=False,
        null=False,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+\Z',
            message='Username содержит недопустимые символы'
        )],
        help_text='Уникальное имя пользователя. Можно буквы, цифры и @/./+/-/_'
    )
    role = models.CharField(
        verbose_name='Роль',
        choices=CHOICES,
        default='user',
        max_length=20,
        help_text='Роль пользователя'
    )
    bio = models.TextField(
        verbose_name='Биография',
        max_length=264,
        blank=True,
        null=True,
        help_text='Краткая биография пользователя'
    )
    confirmation_code = models.CharField(
        verbose_name='Код подтверждения',
        max_length=200,
        editable=False,
        null=True,
        blank=True,
        unique=True,
        help_text='Код для подтверждения регистрации'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def is_user(self):
        """Делает проверку, является ли пользователь обычным пользователем."""
        return self.role == 'user'

    @property
    def is_moderator(self):
        """Делает проверку, является ли пользователь модератором."""
        return self.role == 'moderator'

    @property
    def is_admin(self):
        """Делает проверку, является ли пользователь администратором."""
        return self.role == 'admin' or self.is_superuser or self.is_staff

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]

    def __str__(self):
        return self.email
    
    # def save(self, *args, **kwargs):  #улучшить?
    #     """
    #     Переопределенный метод сохранения.
        
    #     Обеспечивает корректную обработку
    #     уникальных полей и дополнительную логику.
    #     """
    #     # Можно добавить дополнительную логику перед сохранением
    #     super().save(*args, **kwargs)
