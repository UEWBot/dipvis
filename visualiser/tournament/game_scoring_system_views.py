# Diplomacy Tournament Visualiser
# Copyright (C) 2020 Chris Brand
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Game Scoring System Views for the Diplomacy Tournament Visualiser.
"""

from operator import attrgetter

from django.http import Http404
from django.shortcuts import render

from tournament.diplomacy.models.great_power import GreatPower
from tournament.game_scoring.g_scoring_systems import G_SCORING_SYSTEMS
from tournament.game_scoring.game_state import DotCountUnknown
from tournament.game_scoring.simple_game_state import SimpleGameState


# Some fixed interesting game ends
GAME_1 = {'sc_counts': [0, 17, 0, 0, 16, 1, 0],
          'final_year': 1912,
          'elimination_years': [1903, 1909, 1905, 1905]}
GAME_2 = {'sc_counts': [2, 3, 3, 3, 17, 3, 3],
          'final_year': 1910,
          'elimination_years': []}
GAME_3 = {'sc_counts': [6, 5, 5, 4, 4, 5, 5],
          'final_year': 1919,
          'elimination_years': []}
GAME_4 = {'sc_counts': [11, 1, 0, 11, 11, 0, 0],
          'final_year': 1909,
          'elimination_years': [1905, 1906, 1909]}
GAME_5 = {'sc_counts': [11, 0, 0, 12, 11, 0, 0],
          'final_year': 1910,
          'elimination_years': [1910, 1905, 1906, 1909]}


def _create_state(params):
    """Create a GameState object from the params dict."""
    # TODO Add support for draw
    sc_counts = {}
    elimination_years = {}
    n = 0

    # Map to Great Powers
    for p, c in zip(GreatPower.objects.all(), params['sc_counts']):
        sc_counts[p] = c
        if c == 0:
            elimination_years[p] = params['elimination_years'][n]
            n += 1

    return SimpleGameState(sc_counts=sc_counts,
                           final_year=params['final_year'],
                           elimination_years=elimination_years,
                           draw=None)


# GameScoringSystem views

def game_scoring_index(request):
    """GameScoringSystem index"""
    # Sort by name
    system_list = sorted(G_SCORING_SYSTEMS, key=attrgetter('name'))
    return render(request,
                  'game_scoring_systems/index.html',
                  {'system_list': system_list})


def game_scoring_detail(request, slug):
    """Details of a single GameScoringSystem"""
    sys = next((s for s in G_SCORING_SYSTEMS if s.slug == slug), None)
    if sys is None:
        raise Http404

    examples = []

    # Use sys to score some sample games
    for game in [GAME_1, GAME_2, GAME_3, GAME_4, GAME_5]:
        state = _create_state(game)
        try:
            scores = sys.scores(state)
        except DotCountUnknown:
            pass
        else:
            examples.append((state, scores))

    return render(request,
                  'game_scoring_systems/detail.html',
                  {'system': sys,
                   'examples': examples})
