from django.contrib import admin
from .models import CustomUser, FollowUser


# Register your models here.
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    pass


@admin.register(FollowUser)
class CustomUserFollow(admin.ModelAdmin):
    pass
