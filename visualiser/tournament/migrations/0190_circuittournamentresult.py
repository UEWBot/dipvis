from django.db import migrations, models
import django.db.models.deletion


def copy_circuit_tournament_results(apps, schema_editor):
    CircuitPlayer = apps.get_model('tournament', 'CircuitPlayer')
    CircuitTournamentResult = apps.get_model('tournament', 'CircuitTournamentResult')
    old_through = CircuitPlayer.tournamentplayers.through
    CircuitTournamentResult.objects.bulk_create([
        CircuitTournamentResult(circuit_player_id=link.circuitplayer_id,
                                tournament_player_id=link.tournamentplayer_id)
        for link in old_through.objects.all().iterator()
    ])


def restore_circuit_tournament_links(apps, schema_editor):
    CircuitPlayer = apps.get_model('tournament', 'CircuitPlayer')
    CircuitTournamentResult = apps.get_model('tournament', 'CircuitTournamentResult')
    old_through = CircuitPlayer.tournamentplayers.through
    old_through.objects.bulk_create([
        old_through(circuitplayer_id=result.circuit_player_id,
                    tournamentplayer_id=result.tournament_player_id)
        for result in CircuitTournamentResult.objects.all().iterator()
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0189_rename_player_placement_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='CircuitTournamentResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(default=0.0)),
                ('score_dropped', models.BooleanField(default=False)),
                ('circuit_player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                     related_name='tournament_results',
                                                     to='tournament.circuitplayer')),
                ('tournament_player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                        related_name='+',
                                                        to='tournament.tournamentplayer')),
            ],
        ),
        migrations.RunPython(copy_circuit_tournament_results, restore_circuit_tournament_links),
        migrations.RemoveField(
            model_name='circuitplayer',
            name='tournamentplayers',
        ),
        migrations.AddField(
            model_name='circuitplayer',
            name='tournamentplayers',
            field=models.ManyToManyField(blank=True,
                                         through='tournament.CircuitTournamentResult',
                                         to='tournament.tournamentplayer'),
        ),
        migrations.AddConstraint(
            model_name='circuittournamentresult',
            constraint=models.UniqueConstraint(fields=('circuit_player', 'tournament_player'),
                                                name='unique_circuit_tournament_result'),
        ),
    ]