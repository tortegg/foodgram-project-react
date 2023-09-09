from django.core.exceptions import ValidationError


def validate_less_than_zero(value):
    if value <= 0:
        raise ValidationError(
            message='Значение не может быть меньше или равно нулю.'
        )
    return value


def validate_required(value):
    if not value:
        raise ValidationError(
            message='Обязательное поле.'
        )
    return value


def validate_ingredients(data):
    ids = [item['id'] for item in data]
    if len(ids) != len(set(ids)):
        return ValidationError(
            message='Ингредиенты в рецепте не должны повторяться.'
        )
    return data
