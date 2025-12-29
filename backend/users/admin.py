from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Subscribe


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name',
    )
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
