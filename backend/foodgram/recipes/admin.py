from django.contrib import admin

# Register your models here.
from .models import Tag, Recipe, Ingredient, RecipeIngredient, FavoriteRecipe, ShoppingCart


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInLine,)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    pass


@admin.register(FavoriteRecipe)
class FavoriteAdmin(admin.ModelAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    pass
