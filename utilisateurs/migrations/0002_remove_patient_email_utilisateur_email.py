# Generated by Django 5.1.4 on 2024-12-12 23:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utilisateurs', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patient',
            name='email',
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='email',
            field=models.EmailField(default='', max_length=254, unique=True),
        ),
    ]
