# Generated by Django 4.2.16 on 2025-04-10 04:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0142_alter_tournament_tournament_scoring_system'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='external_url',
            field=models.URLField(blank=True, help_text='Will be included in board call emails and game page', verbose_name='External site URL'),
        ),
    ]
