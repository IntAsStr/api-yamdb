from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .constants import BIO_MAX_LENGTH, USER_ROLE_CHOICES, USERNAME_MAX_LENGTH


class CustomUser(AbstractUser):
    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True,
    )

    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+\Z',
            message='Username содержит недопустимые символы'
        )]
    )
    role = models.CharField(
        verbose_name='Роль',
        choices=USER_ROLE_CHOICES,
        default='user',
        max_length=20
    )
    bio = models.TextField(
        verbose_name='Биография',
        max_length=BIO_MAX_LENGTH,
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

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

    @property
    def is_user(self):
        return self.role == 'user'

    @property
    def is_moderator(self):
        return self.role == 'moderator'

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    def __str__(self):
        return self.email
