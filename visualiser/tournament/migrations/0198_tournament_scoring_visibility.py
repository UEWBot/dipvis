from django.db import migrations, models


def show_current_scores_to_scoring_visibility(apps, schema_editor):
    Tournament = apps.get_model('tournament', 'Tournament')
    Tournament.objects.filter(show_current_scores=False).update(scoring_visibility='R')


def scoring_visibility_to_show_current_scores(apps, schema_editor):
    Tournament = apps.get_model('tournament', 'Tournament')
    Tournament.objects.filter(scoring_visibility='R').update(show_current_scores=False)


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0197_constant_max_validators'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='scoring_visibility',
            field=models.CharField(choices=[('C', '"If all games ended now" scores'), ('R', 'Scores after the last finished round')], default='C', help_text='Which scores to show', max_length=1, verbose_name='scoring visibility'),
        ),
        migrations.RunPython(show_current_scores_to_scoring_visibility,
                             scoring_visibility_to_show_current_scores),
        migrations.RemoveField(
            model_name='tournament',
            name='show_current_scores',
        ),
        migrations.AddConstraint(
            model_name='tournament',
            constraint=models.CheckConstraint(condition=models.Q(('scoring_visibility__in', ['C', 'R'])), name='tournament_scoring_visibility_valid'),
        ),
    ]
