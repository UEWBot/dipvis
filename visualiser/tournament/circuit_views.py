# Diplomacy Tournament Visualiser
# Copyright (C) 2026 Chris Brand
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Circuit views for the Diplomacy Tournament Visualiser.
"""

from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from tournament.circuits import (Circuit, CircuitPlayer, CircuitSeries,
                                 CircuitTournamentResult)


class CircuitIndexView(ListView):
    """Circuit index."""
    model = Circuit
    template_name = 'circuits/index.html'


class CircuitSeriesDetailView(DetailView):
    """Circuit series detail."""
    model = CircuitSeries
    template_name = 'circuits/series_detail.html'


class CircuitDetailView(DetailView):
    """Circuit detail."""
    model = Circuit
    pk_url_kwarg = 'circuit_id'
    template_name = 'circuits/detail.html'


def circuit_player_detail(request, circuit_id, circuit_player_id):
    """Circuit player detail."""
    circuit = get_object_or_404(Circuit, pk=circuit_id)
    cp = get_object_or_404(CircuitPlayer.objects.select_related('player', 'circuit'),
                           pk=circuit_player_id,
                           circuit_id=circuit_id)
    return render(request, 'circuits/player_detail.html',
                  {'circuit': circuit, 'circuit_player': cp})


def circuit_scores(request, circuit_id):
    """Show Circuit scores and tournament-by-tournament derivation."""
    circuit = get_object_or_404(Circuit, pk=circuit_id)
    tournaments = list(circuit.tournaments.order_by('start_date', 'id'))
    cps = list(circuit.circuitplayer_set.select_related('player').order_by('-score',
                                                                            'player__last_name',
                                                                            'player__first_name'))
    rankings = circuit.ranks_and_scores()

    results = CircuitTournamentResult.objects.filter(
        circuit_player__circuit=circuit
    ).select_related('tournament_player',
                     'tournament_player__tournament')
    result_by_cp_and_tournament = {
        (result.circuit_player_id, result.tournament_player.tournament_id): result
        for result in results
    }

    rows = []
    for cp in cps:
        contributions = []
        for tournament in tournaments:
            result = result_by_cp_and_tournament.get((cp.id, tournament.id))
            if result is None:
                contributions.append({'tournament': tournament,
                                      'tp': None,
                                      'percentile': None,
                                      'counts': False})
                continue
            contributions.append({'tournament': tournament,
                                  'tp': result.tournament_player,
                                  'percentile': result.score,
                                  'counts': not result.score_dropped})

        rows.append({'rank': rankings.get(cp.player, ('-', cp.score))[0],
                     'player': cp,
                     'contributions': contributions,
                     'score': cp.score})

    context = {'circuit': circuit,
               'tournaments': tournaments,
               'scores': rows}
    return render(request, 'circuits/scores.html', context)

def api(request, circuit_id, version):
    """JSON API to retrieve data"""
    if version != 1:
        raise Http404(f'Invalid API version {version}')
    c = get_object_or_404(Circuit, pk=circuit_id)
    tournaments = []
    for t in c.tournaments.all():
        entry = {'name': t.name,
                 'year': t.start_date.year,
                 'wdr_id': t.wdr_tournament_id,
                 'start_date': t.start_date,
                 'end_date': t.end_date,
                 'api_url': request.build_absolute_uri(reverse('api_tournament',
                                                               args=(version, t.pk,)))}
        tournaments.append(entry)
    results = []
    for player, (rank, score) in c.ranks_and_scores().items():
        # TODO add 'score_breakdown' array
        entry = {'player_name': str(player),
                 'player_wdr_id': player.wdr_player_id,
                 'ranking': rank,
                 'score': score}
        cp = CircuitPlayer.objects.get(circuit=c, player=player)
        entry['events_played'] = cp.tournamentplayers.count()
        results.append(entry)
    data = {'name': c.name,
            'year': c.start_date.year,
            'start_date': c.start_date,
            'end_date': c.end_date,
            'url': request.build_absolute_uri(c.get_absolute_url()),
            'wdd_id': c.wdd_circuit_id,
            'wdr_id': c.wdr_circuit_id,
            'scoring_system': c.scoring_system,
            'tournaments': tournaments,
            'results': results}
    return JsonResponse(data)
