from django.contrib import admin

from .models import Category, Comment, Genre, Review, Title


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    list_display_links = ['name']
    search_fields = ('name', 'slug')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    list_display_links = ['name']
    search_fields = ('name', 'slug')


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'category']
    list_display_links = ['name']
    list_filter = ['category', 'year', 'genre']
    search_fields = ['name', 'description', 'name', 'genre__name']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'score', 'pub_date']
    list_display_links = ['title']
    list_filter = ['score', 'pub_date', 'title']
    readonly_fields = ['pub_date']


@admin.register(Comment)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ['author', 'review', 'text', 'pub_date']
    list_filter = ['pub_date', 'review']
    search_fields = ['text', 'author__username']
    readonly_fields = ['pub_date']
