# Generated by Django 4.2.3 on 2023-08-12 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0007_alter_favoriterecipe_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='image',
            field=models.ImageField(default=None, null=True, upload_to='recipe/images/'),
        ),
    ]
