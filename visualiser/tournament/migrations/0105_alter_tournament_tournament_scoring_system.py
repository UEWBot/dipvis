# Generated by Django 3.2.24 on 2024-03-03 03:42

from django.db import migrations, models
import tournament.models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0104_auto_20240222_1024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournament',
            name='tournament_scoring_system',
            field=models.CharField(choices=[('Best single game result', 'Best single game result'), ('Sum best 2 rounds', 'Sum best 2 rounds'), ('Sum best 3 rounds', 'Sum best 3 rounds'), ('Sum best 4 games in any rounds', 'Sum best 4 games in any rounds'), ('Sum best 4 rounds', 'Sum best 4 rounds')], help_text='How to combine round scores into a tournament score', max_length=40, validators=[tournament.models.validate_tournament_scoring_system]),
        ),
    ]
