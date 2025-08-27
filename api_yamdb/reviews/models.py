from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import (
    CATEGORY_NAME_MAX_LENGTH,
    GENRE_NAME_MAX_LENGTH,
    TITLE_NAME_MAX_LENGTH,
    SLUG_MAX_LENGTH,
    MIN_YEAR,
    MAX_YEAR,
    MIN_SCORE,
    MAX_SCORE
)


class Category(models.Model):
    """Модель категории произведений."""

    name = models.CharField(
        'Категория',
        max_length=CATEGORY_NAME_MAX_LENGTH
    )
    slug = models.SlugField('Слаг', unique=True, max_length=SLUG_MAX_LENGTH)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Genre(models.Model):
    """Модель жанра произведений."""

    name = models.CharField(
        'Название',
        max_length=GENRE_NAME_MAX_LENGTH
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ['name']

    def __str__(self):
        return self.name


class Title(models.Model):
    """Модель произведения."""

    name = models.CharField(
        'Произведение',
        max_length=TITLE_NAME_MAX_LENGTH
    )
    year = models.PositiveSmallIntegerField(
        'Год произведения',
        null=True,
        blank=True,
        validators=[
            MinValueValidator(
                MIN_YEAR,
                message=f'Год должен быть не меньше {MIN_YEAR}'
            ),
            MaxValueValidator(
                MAX_YEAR,
                message=f'Год должен быть не больше {MAX_YEAR}'
            )
        ]
    )
    description = models.TextField('Описание', blank=True)
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        null=True,
    )
    genre = models.ManyToManyField(
        Genre,
        verbose_name='Жанр',
        related_name='titles',
        blank=True,
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ['-year', 'name']

    def __str__(self):
        return self.name


class Review(models.Model):
    """Модель отзыва на произведение."""

    title = models.ForeignKey(
        Title,
        verbose_name='Произведение',
        related_name='reviews',
        on_delete=models.CASCADE,
    )
    text = models.TextField('Текст обзора')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    score = models.PositiveSmallIntegerField(
        null=True,
        validators=[
            MaxValueValidator(
                MAX_SCORE,
                message=f'Оценка должна быть не выше {MAX_SCORE}'
            ),
            MinValueValidator(
                MIN_SCORE,
                message=f'Оценка должна быть не ниже {MIN_SCORE}'
            )
        ]
    )
    pub_date = models.DateTimeField('Дата обзора', auto_now_add=True)

    class Meta:
        verbose_name = 'Обзор'
        verbose_name_plural = 'Обзоры'
        ordering = ['-pub_date']
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review_per_author'
            )
        ]

    def __str__(self):
        return self.title.name


class Comment(models.Model):
    """Модель комментария к отзыву."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    review = models.ForeignKey(
        Review,
        verbose_name='Обзор',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField('Текст комментария')
    pub_date = models.DateTimeField(
        'Дата публикации комментария',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:15]
