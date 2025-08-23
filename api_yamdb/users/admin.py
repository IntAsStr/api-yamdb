from django.contrib import admin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'role', 'is_staff')
    list_filter = ('role',)
    search_fields = ('email', 'username')
    ordering = ('email',)
