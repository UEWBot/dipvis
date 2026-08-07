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

from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from tournament.circuits import Circuit, CircuitPlayer, CircuitSeries, _percentiles


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
    rankings = circuit.positions_and_scores()

    tps = CircuitPlayer.tournamentplayers.through.objects.filter(
        circuitplayer__circuit=circuit
    ).select_related('tournamentplayer',
                     'tournamentplayer__player',
                     'circuitplayer__player',
                     'tournamentplayer__tournament')

    tp_by_cp_and_tournament = {}
    tp_by_tournament = {}
    for link in tps:
        tp = link.tournamentplayer
        tp_by_cp_and_tournament[(link.circuitplayer_id, tp.tournament_id)] = tp
        tp_by_tournament.setdefault(tp.tournament_id, []).append(tp)

    percentiles_by_tournament = {}
    # _percentiles expects TournamentPlayers from one Tournament.
    for tournament in tournaments:
        tp_subset = tp_by_tournament.get(tournament.id, [])
        percentiles_by_tournament[tournament.id] = _percentiles(tp_subset)

    scored_rounds = circuit.scoring_system_obj().scored_rounds
    rows = []
    for cp in cps:
        contributions = []
        for tournament in tournaments:
            tp = tp_by_cp_and_tournament.get((cp.id, tournament.id))
            if tp is None:
                contributions.append({'tournament': tournament,
                                      'tp': None,
                                      'percentile': None,
                                      'counts': False})
                continue
            percentile = percentiles_by_tournament[tournament.id].get(cp.player)
            contributions.append({'tournament': tournament,
                                  'tp': tp,
                                  'percentile': percentile,
                                  'counts': False})

        scored = [c for c in contributions if c['percentile'] is not None]
        scored.sort(key=lambda c: (-c['percentile'], c['tournament'].start_date, c['tournament'].id))
        for c in scored[:scored_rounds]:
            c['counts'] = True

        rows.append({'rank': rankings.get(cp.player, ('-', cp.score))[0],
                     'player': cp,
                     'contributions': contributions,
                     'score': cp.score})

    context = {'circuit': circuit,
               'tournaments': tournaments,
               'scores': rows}
    return render(request, 'circuits/scores.html', context)
