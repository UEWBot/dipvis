# Generated by Django 4.2.16 on 2025-01-05 22:34

from django.db import migrations, models
import tournament.models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0130_alter_tournament_tournament_scoring_system'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournament',
            name='tournament_scoring_system',
            field=models.CharField(choices=[('Best single game result', 'Best single game result'), ('Sum all round scores', 'Sum all round scores'), ('Sum best 2 games plus half the average of the rest', 'Sum best 2 games plus half the average of the rest'), ('Sum best 2 rounds', 'Sum best 2 rounds'), ('Sum best 3 games in any rounds', 'Sum best 3 games in any rounds'), ('Sum best 3 rounds', 'Sum best 3 rounds'), ('Sum best 4 games in any rounds', 'Sum best 4 games in any rounds'), ('Sum best 4 rounds', 'Sum best 4 rounds'), ('Sum best 5 games in any rounds', 'Sum best 5 games in any rounds'), ('Sum best 5 rounds', 'Sum best 5 rounds')], help_text='How to combine round or game scores into a tournament score', max_length=50, validators=[tournament.models.validate_tournament_scoring_system]),
        ),
    ]