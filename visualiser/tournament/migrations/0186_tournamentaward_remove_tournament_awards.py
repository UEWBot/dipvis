from django.db import migrations, models
import django.db.models.deletion


def migrate_tournament_awards(apps, schema_editor):
    Tournament = apps.get_model('tournament', 'Tournament')
    TournamentAward = apps.get_model('tournament', 'TournamentAward')
    for tournament in Tournament.objects.all():
        for award in tournament.awards.all():
            TournamentAward.objects.get_or_create(tournament=tournament,
                                                   award=award)


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0185_playereventranking_tournament_kind'),
    ]

    operations = [
        migrations.CreateModel(
            name='TournamentAward',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('award', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournament.award')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournament.tournament')),
            ],
        ),
        migrations.RunPython(migrate_tournament_awards, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='tournament',
            name='awards',
        ),
        migrations.AddConstraint(
            model_name='tournamentaward',
            constraint=models.UniqueConstraint(fields=('tournament', 'award'), name='unique_tournament_award'),
        ),
    ]