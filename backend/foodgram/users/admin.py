from django.contrib import admin

from .models import CustomUser, FollowUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email'
    )
    search_fields = ('username', 'email',)
    list_filter = ('username', 'email',)


@admin.register(FollowUser)
class CustomUserFollow(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'author'
    )
    search_fields = ('user', 'author',)
    list_filter = ('user', 'author',)
