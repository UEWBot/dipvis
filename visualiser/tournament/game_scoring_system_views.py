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
Player Views for the Diplomacy Tournament Visualiser.
"""

import operator

from django.http import Http404
from django.shortcuts import render

from tournament.game_scoring import GameScoringSystem, G_SCORING_SYSTEMS

# GameScoringSystem views


def game_scoring_index(request):
    """GameScoringSystem index"""
    # Sort by name
    system_list = sorted(G_SCORING_SYSTEMS, key=operator.attrgetter('name'))
    return render(request,
                  'game_scoring_systems/index.html',
                  {'system_list': system_list})


def game_scoring_detail(request, slug):
    """ Details of a single GameScoringSystem"""
    sys = next((s for s in G_SCORING_SYSTEMS if s.slug == slug), None)
    if sys is None:
        raise Http404
    # TODO Use sys to score some sample games
    return render(request,
                  'game_scoring_systems/detail.html',
                  {'system': sys})
