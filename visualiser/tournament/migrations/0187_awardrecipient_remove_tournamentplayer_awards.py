from django.db import migrations, models
import django.db.models.deletion


def migrate_award_recipients(apps, schema_editor):
    TournamentPlayer = apps.get_model('tournament', 'TournamentPlayer')
    TournamentAward = apps.get_model('tournament', 'TournamentAward')
    AwardRecipient = apps.get_model('tournament', 'AwardRecipient')
    for tp in TournamentPlayer.objects.all():
        for award in tp.awards.all():
            tournament_award, _ = TournamentAward.objects.get_or_create(tournament=tp.tournament,
                                                                        award=award)
            AwardRecipient.objects.get_or_create(tournament_award=tournament_award,
                                                 tournament_player=tp)


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0186_tournamentaward_remove_tournament_awards'),
    ]

    operations = [
        migrations.CreateModel(
            name='AwardRecipient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tournament_award', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournament.tournamentaward')),
                ('tournament_player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournament.tournamentplayer')),
            ],
        ),
        migrations.RunPython(migrate_award_recipients, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='tournamentplayer',
            name='awards',
        ),
        migrations.AddConstraint(
            model_name='awardrecipient',
            constraint=models.UniqueConstraint(fields=('tournament_award', 'tournament_player'), name='unique_award_recipient'),
        ),
    ]
