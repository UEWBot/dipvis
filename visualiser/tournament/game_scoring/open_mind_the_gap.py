# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2020 Chris Brand
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
This module contains a class taht implements the Open Mind The Gap (OMG) scoring system.
"""
from operator import itemgetter

from django.utils.translation import gettext as _

from tournament.game_scoring.game_scoring_system import GameScoringSystem
from tournament.game_scoring.utils import _adjust_rank_score, _sorted_scores


class GScoringOMG(GameScoringSystem):
    """
    Open Mind the Gap (OMG) Scoring system

    a) Each supply center (SC) is worth 1.5 points (total = 51 points)
    b) Surviving in a draw is worth 9 points (average = 40.5 points per game)
    c) Bonuses for the Top 3: 4.5 points for 1st, 3 points for 2nd, 1.5 points for 3rd.
       If positions are tied, position points are shared between powers
       (e.g. a 2-way tie for second awards each player (3 + 1.5) / 2 = 2.25 points.
    d) Tribute paid to the board topper is equal to 1st place SCs - 2nd place SCs,
       capped at 50% of a players score from a, b, and c
    e) a solo victory is worth 100 points, with others scoring zero.
    """
    def __init__(self):
        self.name = _('OMG')

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        dots.sort(key=itemgetter(1), reverse=True)
        gap = dots[0][1] - dots[1][1]
        num_leaders = state.num_powers_with(dots[0][1])
        rank_pts = _adjust_rank_score(dots, [4.5, 3, 1.5])
        soloer = state.soloer()
        soloed = soloer is not None
        tribute = 0
        for i, (p, c) in enumerate(dots):
            if soloed:
                if p == soloer:
                    retval[p] = 100
                else:
                    retval[p] = 0
                continue
            # 1.5 point per dot
            retval[p] = 1.5 * c
            # Plus the survival points
            if c:
                retval[p] += 9
            # and position points
            retval[p] += rank_pts[i]
            if num_leaders == 1:
                # Leader(s) gets tribute from all the rest
                x = min(gap, retval[p]/2)
                retval[p] -= x
                tribute += x
        # Tribute goes to the leader
        retval[dots[0][0]] += tribute
        return _sorted_scores(retval, state)
