from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from djoser.views import UserViewSet
from rest_framework.generics import get_object_or_404

from recipes.models import Tag, Recipe, FavoriteRecipe, ShoppingCart, Ingredient
from .serializers import TagSerializer, RecipeSerializer, RecipeCreateSerializer, OutIngredientSerializer, \
    FavoriteRecipeSerializer, ShoppingCartSerializer
from .filters import IngredientFilterSet


class CustomUserViewSet(UserViewSet):
    pass


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]

    # def perform_create(self, serializer):
    #     serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action == ('retrieve' or 'list'):
            return RecipeSerializer
        return RecipeCreateSerializer

    def favorite_cart_add_delete(self, method, user, pk, model, serializer):
        recipe = get_object_or_404(Recipe, pk)
        if method == 'POST':
            model.objects.get_or_create(user=user, recipe=recipe)
            return Response(
                serializer.to_representation(instance=recipe),
                status=status.HTTP_204_NO_CONTENT
            )
        elif method == 'DELETE':
            model.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST', 'DELETE'], detail=True, permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk=None):
        return self.favorite_cart_add_delete(
            method=request.method,
            user=request.user,
            pk=pk,
            model=ShoppingCart,
            serializer=FavoriteRecipeSerializer
        )

    @action(methods=['POST', 'DELETE'], detail=True, permission_classes=[IsAuthenticated, ])
    def shopping_cart(self, request, pk=None):
        return self.favorite_cart_add_delete(
            method=request.method,
            user=request.user,
            pk=pk,
            model=FavoriteRecipe,
            serializer=ShoppingCartSerializer
        )


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = OutIngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilterSet
