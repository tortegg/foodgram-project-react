from django.urls import include, path
from rest_framework import routers

from .views import (
    CustomUserViewSet, IngredientViewSet, RecipeViewSet,
    TagViewSet
)

router = routers.DefaultRouter()
router.register('users', CustomUserViewSet)
router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
