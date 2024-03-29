# Generated by Django 3.2.17 on 2023-02-17 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0090_gameplayer_unique_player_game'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='drawproposal',
            constraint=models.CheckConstraint(check=models.Q(('season__in', ['S', 'F'])), name='drawproposal_season_valid'),
        ),
        migrations.AddConstraint(
            model_name='gameimage',
            constraint=models.CheckConstraint(check=models.Q(('season__in', ['S', 'F'])), name='gameimage_season_valid'),
        ),
        migrations.AddConstraint(
            model_name='gameimage',
            constraint=models.CheckConstraint(check=models.Q(('phase__in', ['M', 'R', 'X'])), name='gameimage_phase_valid'),
        ),
        migrations.AddConstraint(
            model_name='playergameresult',
            constraint=models.CheckConstraint(check=models.Q(('result__in', ['W', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'L']), ('result', ''), _connector='OR'), name='playergameresult_result_valid'),
        ),
        migrations.AddConstraint(
            model_name='tournament',
            constraint=models.CheckConstraint(check=models.Q(('draw_secrecy__in', ['S', 'C'])), name='tournament_draw_secrecy_valid'),
        ),
        migrations.AddConstraint(
            model_name='tournament',
            constraint=models.CheckConstraint(check=models.Q(('power_assignment__in', ['A', 'M', 'P'])), name='tournament_power_assignment_valid'),
        ),
        migrations.AddConstraint(
            model_name='tournament',
            constraint=models.CheckConstraint(check=models.Q(('best_country_criterion__in', ['S', 'D'])), name='tournament_best_country_criterion_valid'),
        ),
        migrations.AddConstraint(
            model_name='tournament',
            constraint=models.CheckConstraint(check=models.Q(('format__in', ['F', 'V'])), name='tournament_format_valid'),
        ),
    ]
