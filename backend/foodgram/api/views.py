from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import F, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from djoser.views import UserViewSet
from rest_framework.generics import get_object_or_404
from weasyprint import HTML

from recipes.models import Tag, Recipe, FavoriteRecipe, ShoppingCart, Ingredient, RecipeIngredient
from users.models import CustomUser, FollowUser
from .serializers import TagSerializer, RecipeSerializer, RecipeCreateSerializer, OutIngredientSerializer, \
    FavoriteRecipeSerializer, ShoppingCartSerializer, CustomUserSerializer, FollowListSerializer, FollowSerializer
from .filters import IngredientFilterSet, RecipeFilter
from .pagination import CustomPaginator


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPaginator

    @action(['GET'], detail=False, permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(methods=['GET'], detail=False)
    def subscriptions(self, request):
        """ Отоброжение подписок """
        subscription_list = self.paginate_queryset(
            CustomUser.objects.filter(followed__user=request.user)
        )
        serializer = FollowListSerializer(
            subscription_list, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


    @action(methods=['POST', 'DELETE'], detail=True)
    def subscribe(self, request, id):
        """ Подписаться/отписаться """
        author = get_object_or_404(CustomUser, id=id)
        if request.method == 'POST':
            user = self.request.user
            data = {'author': author.id, 'user': user.id}
            serializer = FollowSerializer(
                data=data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        subscription = get_object_or_404(
            FollowUser, user=request.user, author=author
        )
        self.perform_destroy(subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    # def perform_create(self, serializer):
    #     serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return RecipeSerializer
        return RecipeCreateSerializer

    @action(methods=['POST', 'DELETE'], detail=True, permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk=None):
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
            favorite, created = FavoriteRecipe.objects.get_or_create(user=user, recipe=recipe)
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

    @action(methods=['POST', 'DELETE'], detail=True, permission_classes=[IsAuthenticated, ])
    def shopping_cart(self, request, pk=None):
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
            cart, created = ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
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

    def get_list_ingredients(self, user):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_recipe__user=user).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount')).values_list(
            'ingredient__name', 'amount', 'ingredient__measurement_unit')
        return ingredients

    @action(detail=False, methods=['GET'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = self.get_list_ingredients(request.user)
        html_template = render_to_string('recipes/pdf_template.html',
                                         {'ingredients': ingredients})
        html = HTML(string=html_template)
        result = html.write_pdf()
        response = HttpResponse(result, content_type='application/pdf;')
        response['Content-Disposition'] = 'inline; filename=shopping_list.pdf'
        response['Content-Transfer-Encoding'] = 'binary'
        return response


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = OutIngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
