# Generated by Django 5.0.2 on 2024-02-27 01:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_project_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='paused',
            field=models.BooleanField(default=False),
        ),
    ]