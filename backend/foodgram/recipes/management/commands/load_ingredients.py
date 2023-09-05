import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'load ingredients from csv'

    def handle(self, *args, **options):
        with open(settings.BASE_DIR / 'recipes/ingredients.csv') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                name, measurement_unit = row
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )
