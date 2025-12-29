import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загрузка ингредиентов из CSV файла в базу данных."""

    def handle(self, *args, **kwargs):
        data_path = os.path.join(settings.BASE_DIR, '..', 'data', 'ingredients.csv')

        self.stdout.write(f'Путь: {data_path}')

        if not os.path.exists(data_path):
            self.stdout.write(self.style.ERROR('Файл ingredients.csv не найден!'))
            return

        with open(data_path, encoding='utf-8') as file:
            reader = csv.reader(file)
            ingredients_to_create = []
            for row in reader:
                name, measurement_unit = row
                ingredients_to_create.append(
                    Ingredient(
                        name=name,
                        measurement_unit=measurement_unit
                    )
                )

            # bulk_create для быстрой вставки множества записей
            # ignore_conflicts=True пропустит дубликаты, если они уже есть
            Ingredient.objects.bulk_create(ingredients_to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS('Ингредиенты загружены.'))
