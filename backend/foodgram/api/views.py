from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.models import CustomUser, FollowUser

from .filters import RecipeFilter, IngredientFilterSet
from .pagination import CustomPaginator
from .permissions import IsAuthorOrReadOnly
from .serializers import (FollowListSerializer, FollowSerializer,
                          OutIngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, TagSerializer)


class CustomUserViewSet(UserViewSet):
    """ViewSet пользователя."""
    permission_classes = (AllowAny,)
    pagination_class = CustomPaginator

    @action(['GET'], detail=False,
            permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(methods=['GET'], detail=False,
            permission_classes=(IsAuthenticated,),
            pagination_class=CustomPaginator)
    def subscriptions(self, request):
        """Отоброжение подписок."""
        subscription_list = self.paginate_queryset(
            CustomUser.objects.filter(followed__user=request.user)
        )
        serializer = FollowListSerializer(
            subscription_list, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id):
        """Подписаться/отписаться."""
        author = get_object_or_404(CustomUser, id=id)
        if request.method == 'POST':
            user = self.request.user
            data = {'author': author.id, 'user': user.id}
            serializer = FollowSerializer(
                data=data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data=serializer.data,
                            status=status.HTTP_201_CREATED)

        subscription = get_object_or_404(
            FollowUser, user=request.user, author=author
        )
        self.perform_destroy(subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ModelViewSet):
    """ViewSet тегов."""
    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """ViewSet рецептов."""
    queryset = Recipe.objects.all()
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return RecipeSerializer
        return RecipeCreateSerializer

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        """Добавление/удаление избранного рецепта."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        favorite = FavoriteRecipe.objects.filter(user=user, recipe=recipe)
        if request.method == 'DELETE':
            if favorite.exists():
                favorite.delete()
                return Response(
                    {'message': 'Рецепт удален из избранного'},
                    status=status.HTTP_204_NO_CONTENT
                )
            else:
                return Response(
                    {'message': 'Такого рецепта нет в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            favorite, created = FavoriteRecipe.objects.get_or_create(
                user=user, recipe=recipe
            )
            if created is False:
                return Response(
                    {'message': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'message': 'Рецепт добавлен в избранное'},
                    status=status.HTTP_201_CREATED
                )

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в корзине."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if request.method == 'DELETE':
            if cart.exists():
                cart.delete()
                return Response(
                    {'message': 'Рецепт удален из корзины'},
                    status=status.HTTP_204_NO_CONTENT
                )
            else:
                return Response(
                    {'message': 'Такого рецепта нет в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            cart, created = ShoppingCart.objects.get_or_create(
                user=user, recipe=recipe
            )
            if created is False:
                return Response(
                    {'message': 'Рецепт уже в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'message': 'Рецепт добавлен в корзину'},
                    status=status.HTTP_201_CREATED
                )

    def convert_txt(self, shop_list):
        file_name = settings.SHOPPING_CART_FILE
        lines = []
        for ing in shop_list:
            name = ing['ingredient__name']
            measurement_unit = ing['ingredient__measurement_unit']
            amount = ing['ingredient_total']
            lines.append(f'{name} ({measurement_unit}) - {amount}')
        lines.append('\nFoodGram Service')
        content = '\n'.join(lines)
        content_type = 'text/plain,charset=utf8'
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        return response

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Скачивание ингредиентов из корзины."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__cart_recipe__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).order_by(
            'ingredient__name'
        ).annotate(ingredient_total=Sum('amount'))
        return self.convert_txt(ingredients)


class IngredientViewSet(ModelViewSet):
    """ViewSet ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = OutIngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilterSet
