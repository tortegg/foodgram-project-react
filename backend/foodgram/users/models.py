from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    email = models.EmailField(
        max_length=254,
        blank=False,
        verbose_name='Почта',
        unique=True
    )
    username = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Никнейм',
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Недопустимое имя'
            )
        ],
        unique=True
    )
    first_name = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Фамилия'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.username


class FollowUser(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='followed',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='user_author_subscribe_unique'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Пописки'

    def __str__(self):
        return f'{self.user} подписан на автора {self.author}'
