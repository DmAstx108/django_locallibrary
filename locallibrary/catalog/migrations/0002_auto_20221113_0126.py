# Generated by Django 2.2.19 on 2022-11-12 22:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='books', to='catalog.Author'),
        ),
        migrations.RemoveField(
            model_name='book',
            name='genre',
        ),
        migrations.AddField(
            model_name='book',
            name='genre',
            field=models.ForeignKey(default=1, help_text='Select a genre for this book', on_delete=django.db.models.deletion.CASCADE, related_name='books', to='catalog.Genre'),
            preserve_default=False,
        ),
    ]
