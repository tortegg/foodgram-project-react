from django_filters import rest_framework as filters
from recipes.models import Ingredient


class IngredientFilterSet(filters.FilterSet):
    ingredient = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
