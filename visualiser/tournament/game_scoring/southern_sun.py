# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2025 Chris Brand
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
This module contains a class that implements the Southern Sun scoring system.
"""
from operator import itemgetter

from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR
from tournament.game_scoring.game_scoring_system import GameScoringSystem
from tournament.game_scoring.utils import _adjust_rank_score, _sorted_scores


class GScoringSouthernSun(GameScoringSystem):
    """
    Southern Sun scoring system

    In a draw: 30 points for surviving players at the end of the game,
    10 points per centre, then ranking points based on the Fibonacci sequence:
    7th - 10 points
    6th - 10 points
    5th - 20 points
    4th - 30 points
    3rd - 50 points
    2nd - 80 points
    1st - 130 points.

    Players on an equal number of centres share the average of their ranks
    (rounded to the nearest whole number, where relevant). e.g. Duo board top
    is (130+80)/2 = 105 points each, three way share for 2nd behind a sole board
    top is (80+50+30)/3 = 53 points each, etc.

    Eliminated players receive 3 points per game year played; no place bonus.

    In a solo: Winner receives 500 points; all other players receive zero points.
    """
    def __init__(self):
        self.name = _('Southern Sun')
        self.position_points = [130, 80, 50, 30, 20, 10, 10]
        self.dead_score_can_change = True

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        all_powers = state.all_powers()
        soloer = state.soloer()
        if soloer is not None:
            for p in all_powers:
                if p == soloer:
                    retval[p] = 500
                else:
                    retval[p] = 0
        else:
            dots = [(p, state.dot_count(p)) for p in all_powers]
            dots.sort(key=itemgetter(1), reverse=True)
            # Allow for tied positions
            rank_pts = _adjust_rank_score(dots, self.position_points[:len(state.survivors())])
            for i, (p, c) in enumerate(dots):
                if c > 0:
                    # 30 plus 10/dot plus rank points
                    retval[p] = 30 + 10 * c + round(rank_pts[i])
                else:
                    # 3 points per game year survived, no place bonus
                    retval[p] = 3 * (1 + state.year_eliminated(p) - FIRST_YEAR)
        return _sorted_scores(retval, state)
