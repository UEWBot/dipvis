# Generated by Django 4.2.16 on 2025-01-05 22:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0132_roundplayer_tournament_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='show_current_scores',
            field=models.BooleanField(default=True, help_text='Whether to show up-to-date after-last-round scores'),
        ),
    ]