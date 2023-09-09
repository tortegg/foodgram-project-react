import base64

from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.core.exceptions import ValidationError
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from users.models import CustomUser, FollowUser
from utils.static_params import LEN_200
from utils.validators import validate_less_than_zero, validate_required


class Base64ImageField(serializers.ImageField):
    """Метод для загрузки картинки через Base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomCreateUserSerializer(UserCreateSerializer):
    """Создание пользователя."""

    class Meta:
        model = CustomUser
        fields = '__all__'

    def validate(self, obj):
        usernames = [
            'me', 'set_password', 'subscriptions', 'subscribe'
        ]
        if self.initial_data.get('username') in usernames:
            raise serializers.ValidationError(
                {'Нельзя использовать это имя пользователя'}
            )
        return obj


class CustomUserListSerializer(UserSerializer):
    """Получение списка пользователей."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'is_subscribed',
        )

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return FollowUser.objects.filter(
            user=request.user, author=author
        ).exists()


class CustomUserSerializer(CustomUserListSerializer):
    """Получение списка подписок пользователей."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'is_subscribed',
        )

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class TagSerializer(serializers.ModelSerializer):
    """Список тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class OutIngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Список ингредиентов."""
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author',
            'ingredients', 'is_favorited', 'is_in_shopping_cart',
            'image', 'name', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return (request.user.is_authenticated
                and FavoriteRecipe.objects.filter(
                    user=request.user, recipe=obj
                ).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return (request.user.is_authenticated
                and ShoppingCart.objects.filter(
                    user=request.user, recipe=obj
                ).exists())


class AddIngredientSerializer(serializers.ModelSerializer):
    """Создание ингредиента при создании рецепта."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    @staticmethod
    def validate_amount(data):
        return validate_less_than_zero(data)


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Создание редактирование и удаление рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = AddIngredientSerializer(many=True)
    image = Base64ImageField(max_length=None)
    name = serializers.CharField(max_length=LEN_200)
    cooking_time = serializers.IntegerField()
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags',
            'image', 'name', 'text',
            'cooking_time', 'author'
        )

    @staticmethod
    def validate_cooking_time(time):
        return (validate_required(time)
                and validate_less_than_zero(time))

    @staticmethod
    def validate_tags(tag):
        return validate_required(tag)

    @staticmethod
    def validate_ingredients(data):
        ids = [item['id'] for item in data]
        if len(ids) != len(set(ids)):
            return serializers.ValidationError({
                'error': 'Ингредиенты в рецепте не должны повторяться.'
            })
        return validate_required(data)

    @staticmethod
    def validate_name(name):
        return validate_required(name)

    @staticmethod
    def validate_text(text):
        return validate_required(text)

    @staticmethod
    def add_ingredient(recipe, tags, ingredients):
        recipe.tags.set(tags)
        ingredients_to_add = [
            RecipeIngredient(
                ingredient=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount'],
            ) for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredients_to_add)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        self.add_ingredient(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        self.add_ingredient(
            ingredients=ingredients,
            recipe=recipe,
            tags=tags
        )
        return super().update(recipe, validated_data)


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """Добавление рецепта в избранное."""
    user = CustomUserSerializer(read_only=True)
    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = FavoriteRecipe
        fields = ['user', 'recipe']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=FavoriteRecipe.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже в избранном'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Добавление рецепта в корзину"""
    user = CustomUserSerializer(read_only=True)
    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = FavoriteRecipe
        fields = ['user', 'recipe']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже в корзине'
            )
        ]


class RecipeMiniSerializer(serializers.ModelSerializer):
    """Сокращенная информация о рецепте."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowListSerializer(serializers.ModelSerializer):
    """ Сериализатор списка подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, author):
        return FollowUser.objects.filter(
            user=self.context.get('request').user,
            author=author
        ).exists()

    def get_recipes(self, author):
        queryset = self.context.get('request')
        recipes_limit = queryset.query_params.get('recipes_limit')
        if not recipes_limit:
            return RecipeMiniSerializer(
                Recipe.objects.filter(author=author),
                many=True, context={'request': queryset}
            ).data
        return RecipeMiniSerializer(
            Recipe.objects.filter(author=author)[:int(recipes_limit)],
            many=True,
            context={'request': queryset}
        ).data

    def get_recipes_count(self, author):
        return Recipe.objects.filter(author=author).count()


class FollowSerializer(serializers.ModelSerializer):
    """ Сериализатор подписки."""

    class Meta:
        model = FollowUser
        fields = ('user', 'author')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=FollowUser.objects.all(),
                fields=('user', 'author',),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    # def validate(self, data):
    #     get_object_or_404(CustomUser, username=data['author'])
    #     if self.context['request'].user == data['author']:
    #         raise serializers.ValidationError({
    #             'error': 'На себя подписаться нельзя.'
    #         })
    #     if FollowUser.objects.filter(
    #             user=self.context['request'].user,
    #             author=data['author']
    #     ):
    #         raise serializers.ValidationError({
    #             'error': 'Вы уже подписаны.'
    #         })
    #     return data
    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                {
                    'error': 'Нельзя подписаться на себя!'
                }
            )
        return data

    def to_representation(self, instance):
        return FollowListSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data
