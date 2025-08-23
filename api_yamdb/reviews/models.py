from django.db import models
from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError


def validate_slug(value):
    if not value.islower():
        raise ValidationError("Slug должен быть в нижнем регистре.")
    return value


class Category(models.Model):
    name = models.CharField('Категория', max_length=64, help_text='Выберите категорию')
    slug = models.SlugField('Слаг', unique=True, help_text='Выберите Slug')
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name[:20]


class Genre(models.Model):
    name = models.CharField(
        'Название',
        max_length=64,
        help_text='Выберите название жанра'
    )
    slug = models.SlugField(max_length=20, unique=True, verbose_name='Слаг')
    # slug = models.SlugField(max_length=20, unique=True, verbose_name='Слаг', validators=[validate_slug])

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ['name']

    def __str__(self):
        return self.name[:20]




class Title(models.Model):
    name = models.CharField('Произведение', max_length=64, help_text='Выберите название произведения')
    year = models.IntegerField('Год произведения', null=True, blank=True)
    description = models.TextField('Описание', blank=True)
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        null=True,
        blank=False)
    genre = models.ManyToManyField(
        Genre,
        verbose_name='Жанр',
        related_name='titles',
        blank=True,
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        # ordering = ['name']
        ordering = ['-year', 'name']

    def __str__(self):
        return self.name[:20]


class Review(models.Model):
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
    score = models.IntegerField(
        null=True,
        validators=[
            MaxValueValidator(10, message='Оценка должна быть не выше 10'),
            MinValueValidator(1, message='Оценка должна быть не ниже 1')
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
        return self.title[:20]


class Comments(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Автор',
        on_delete=models.SET_NULL,
        null=True)
    review = models.ForeignKey(
        Review,
        verbose_name='Обзор',
        on_delete=models.SET_NULL,
        null=True)
    text = models.TextField('Текст комментария')
    pub_date = models.DateTimeField(
        'Дата публикации комментария',
        auto_now_add=True,
    )

    class Meta:
        ordering = ['pub_date']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:15]
