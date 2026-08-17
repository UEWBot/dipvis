from django.db import migrations, models
import django.db.models.deletion


def _link_background_to_rankings(apps, schema_editor):
    PlayerEventRanking = apps.get_model('tournament', 'PlayerEventRanking')
    PlayerGameResult = apps.get_model('tournament', 'PlayerGameResult')
    PlayerAward = apps.get_model('tournament', 'PlayerAward')

    def link_or_create(obj):
        query = PlayerEventRanking.objects.filter(player_id=obj.player_id)
        if obj.wdr_tournament_id is not None:
            query = query.filter(wdr_tournament_id=obj.wdr_tournament_id)
        elif obj.wdd_tournament_id is not None:
            query = query.filter(wdd_tournament_id=obj.wdd_tournament_id)
        elif obj.event_name:
            query = query.filter(event_name=obj.event_name)

        rankings = list(query.order_by('id'))
        if len(rankings) == 1:
            return rankings[0]

        if len(rankings) > 1:
            same_date = [r for r in rankings if r.date == obj.date]
            if same_date:
                return same_date[0]
            return rankings[0]

        event_name = obj.event_name or '(Unknown event)'
        event_date = obj.date

        defaults = {
            'wdd_tournament_id': obj.wdd_tournament_id,
            'wdr_tournament_id': obj.wdr_tournament_id,
        }
        ranking, _ = PlayerEventRanking.objects.get_or_create(
            player_id=obj.player_id,
            event_name=event_name,
            date=event_date,
            defaults=defaults)
        return ranking

    for model in (PlayerGameResult, PlayerAward):
        for obj in model.objects.filter(event_ranking__isnull=True):
            ranking = link_or_create(obj)
            obj.event_ranking_id = ranking.id
            obj.save(update_fields=['event_ranking'])


def assert_all_background_rows_linked(apps, schema_editor):
    PlayerGameResult = apps.get_model('tournament', 'PlayerGameResult')
    PlayerAward = apps.get_model('tournament', 'PlayerAward')
    missing_results = PlayerGameResult.objects.filter(event_ranking__isnull=True).count()
    missing_awards = PlayerAward.objects.filter(event_ranking__isnull=True).count()
    if missing_results or missing_awards:
        raise RuntimeError(
            f'Cannot enforce non-null event_ranking: '
            f'{missing_results} PlayerGameResult and '
            f'{missing_awards} PlayerAward rows are still unlinked.')


def convert_unranked_positions(apps, schema_editor):
    PlayerEventRanking = apps.get_model('tournament', 'PlayerEventRanking')
    PlayerEventRanking.objects.filter(position=0).update(position=None)


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0182_remove_playereventranking_unique_player_event_name_year_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='playeraward',
            name='event_ranking',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tournament.playereventranking'),
        ),
        migrations.AddField(
            model_name='playergameresult',
            name='event_ranking',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tournament.playereventranking'),
        ),
        migrations.RunPython(_link_background_to_rankings, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name='playeraward',
            name='unique_player_event_name_date_name',
        ),
        migrations.RemoveConstraint(
            model_name='playergameresult',
            name='unique_names_player_power',
        ),
        migrations.RemoveField(
            model_name='playeraward',
            name='event_name',
        ),
        migrations.RemoveField(
            model_name='playergameresult',
            name='event_name',
        ),
        migrations.AddConstraint(
            model_name='playeraward',
            constraint=models.UniqueConstraint(fields=('player', 'event_ranking', 'date', 'name'), name='unique_player_eventranking_date_name'),
        ),
        migrations.RunPython(assert_all_background_rows_linked, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='playeraward',
            name='event_ranking',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournament.playereventranking'),
        ),
        migrations.AlterField(
            model_name='playergameresult',
            name='event_ranking',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournament.playereventranking'),
        ),
        migrations.AddConstraint(
            model_name='playergameresult',
            constraint=models.UniqueConstraint(fields=('event_ranking', 'round_number', 'game_number', 'player', 'power'), name='unique_eventranking_player_power'),
        ),
        migrations.AlterField(
            model_name='playereventranking',
            name='position',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(convert_unranked_positions, migrations.RunPython.noop),
    ]
