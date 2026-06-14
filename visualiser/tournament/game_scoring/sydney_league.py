# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2026 Chris Brand
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
This module contains a class that implements the Sydney League scoring systems.
"""
from operator import itemgetter

from django.utils.translation import gettext as _

from tournament.diplomacy import FIRST_YEAR, TOTAL_SCS

from .game_scoring_system import GameScoringSystem
from .utils import _adjust_rank_score, _sorted_scores


class GScoringSydneyLeague(GameScoringSystem):
    """
    Sydney League scoring system

    Points for position, 700, 600, 500, 400, 300, 200, 100,
    with players on shared positions averaging the points between them.
    i.e. 2 way board top (700+600)/2 for each player.,
         3 way board top (700+600+500)/3 for each player, etc.
    Points for centres, 25 per centre.
    Points for time survived, 1 point per year for eliminated players.
    Solo on board: +50% for soloing player, -50% for all other players.
    """
    def __init__(self):
        self.name = 'Sydney League'
        self.dead_score_can_change = True
        self.points_per_dot = 25
        self.position_pts = [700, 600, 500, 400, 300, 200, 100]

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}

        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        dots.sort(key=itemgetter(1), reverse=True)

        # Split out the eliminated powers
        live_scs = [(p, c) for (p, c) in dots if c > 0]
        pos_pts_1 = self.position_pts[:len(live_scs)]
        # Tweak the alive powers points to allow for ties
        rank_pts = _adjust_rank_score(live_scs, pos_pts_1)
        for i, (p, c) in enumerate(live_scs):
            retval[p] = self.points_per_dot * c + rank_pts[i]

        # Calculate scores for eliminated powers, if any
        if len(self.position_pts) != len(pos_pts_1):
            dead_scs = [(p, c) for (p, c) in dots if c == 0]
            pos_pts_2 = self.position_pts[len(pos_pts_1) - len(self.position_pts):]
            # Find when the dead powers died
            dummys = []
            for p, c in dead_scs:
                year = state.year_eliminated(p)
                # For both year and SC count, higher is better
                dummys.append((p, year))
            dummys.sort(key=itemgetter(1), reverse=True)
            rank_pts = _adjust_rank_score(dummys, pos_pts_2)
            for i, (p, y) in enumerate(dummys):
                # Add in points per year survived
                retval[p] = rank_pts[i] + (y + 1 - FIRST_YEAR)

        # Adjust scores if someone soloed
        soloer = state.soloer()
        if soloer is not None:
            for p in state.all_powers():
                if p == soloer:
                    retval[p] *= 1.5
                else:
                    retval[p] *= 0.5

        return _sorted_scores(retval, state)
