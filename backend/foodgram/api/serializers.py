import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer

from recipes.models import Tag, Recipe, RecipeIngredient, FavoriteRecipe, ShoppingCart, Ingredient
from users.models import CustomUser, FollowUser


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomCreateUserSerializer(UserCreateSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

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
        return FollowUser.objects.filter(user=request.user, author=author).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class OutIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = CustomUserSerializer(read_only=True)

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author',
            'ingredients', 'is_favorited', 'is_in_shopping_cart',
            'image', 'name', 'text', 'cooking_time')


class AddIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = AddIngredientSerializer(many=True)
    image = Base64ImageField(max_length=None)
    name = serializers.CharField(max_length=200)
    cooking_time = serializers.IntegerField()
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags',
                  'image', 'name', 'text',
                  'cooking_time', 'author')

    def add_ingredient(self, ingredients, recipe):
        ingredients_to_add = [
            RecipeIngredient(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient['amount'],
            ) for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredients_to_add)

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        image = validated_data.pop('image')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            image=image,
            author=author,
            **validated_data
        )
        self.add_ingredient(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        self.add_ingredient(ingredients, recipe)
        recipe.tags.set(tags)
        return super().update(recipe, validated_data)


class FavoriteRecipeSerializer(serializers.ModelSerializer):
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
