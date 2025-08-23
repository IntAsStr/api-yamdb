from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class CustomUser(AbstractUser):
    CHOICES = [
        ('user', 'user'),
        ('admin', 'admin'),
        ('moderator', 'moderator'),
    ]
    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True,
        blank=False,
        null=False
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
        )]
    )
    role = models.CharField(
        verbose_name='Роль',
        choices=CHOICES,
        default='user',
        max_length=20
    )
    bio = models.TextField(
        verbose_name='Биография',
        max_length=264,
        blank=True,
        null=True
    )
    confirmation_code = models.CharField(
        verbose_name='Код подтверждения',
        max_length=200,
        editable=False,
        null=True,
        blank=True,
        unique=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def is_user(self):
        return self.role == 'user'

    @property
    def is_moderator(self):
        return self.role == 'moderator'

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser or self.is_staff

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['email']
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]

    def __str__(self):
        return self.email
