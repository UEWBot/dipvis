# Generated by Django 4.2.16 on 2025-01-05 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0131_alter_tournament_tournament_scoring_system'),
    ]

    operations = [
        migrations.AddField(
            model_name='roundplayer',
            name='tournament_score',
            field=models.FloatField(default=0.0, help_text='Tournament score after the round'),
        ),
    ]
