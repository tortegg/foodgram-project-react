from django.contrib import admin

from .models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInLine,)
    list_display = (
        'id',
        'name',
        'author',
        'is_favorited'
    )
    list_filter = ('author', 'name', 'tags',)
    search_fields = ('name', 'author', 'tags',)

    @admin.display(description='В избранном')
    def is_favorited(self, obj):
        return obj.favorite_recipe.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(FavoriteRecipe)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'recipe',
    )
    list_filter = ('user',)
    search_fields = ('user', 'recipe',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'recipe',
    )
    list_filter = ('user',)
    search_fields = ('user', 'recipe',)


@admin.register(RecipeIngredient)
class IngredientInRecipe(admin.ModelAdmin):
    list_display = (
        'id',
        'recipe',
        'ingredient'
    )
    list_filter = ('recipe',)
    search_fields = ('recipe', 'ingredient',)
