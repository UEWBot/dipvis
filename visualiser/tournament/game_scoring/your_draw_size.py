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
This module contains a class that implements the Your Draw Size scoring system.
"""
from django.utils.translation import gettext as _

from tournament.game_scoring.game_scoring_system import GameScoringSystem
from tournament.game_scoring.utils import _sorted_scores


class GScoringYourDrawSize(GameScoringSystem):
    """
    Your Draw Size scoring system

    If there is a solo:
    - Soloers score a set number of points (soloer_pts).
    - Losers to a solo get zero.
    Otherwise, players score based on the number of centres they own at
    the end of the game:
    14 - 17 centres - 105 points
    11 - 13 centres -  70 points
     8 - 10 centres -  42 points
     4 -  7 centres -  30 points
     1 -  3 centres -  21 points
          0 centres -   0 points
    """
    def __init__(self, name, soloer_pts):
        self.name = name
        self.dead_score_can_change = False
        self.soloer_pts = soloer_pts
        # Scores for 0..17 dots
        self.dots_to_pts = [0, 21, 21, 21, 30, 30, 30, 30, 42, 42, 42, 70, 70, 70, 105, 105, 105, 105]

    @property
    def description(self):
        return _("""
                 If there is a solo:
                 - Soloers score %(soloer_pts)d points.
                 - Losers to a solo get zero.
                 Otherwise, players score based on the number of centres they own at
                 the end of the game:
                 14 - 17 centres - 105 points
                 11 - 13 centres -  70 points
                  8 - 10 centres -  42 points
                  4 -  7 centres -  30 points
                  1 -  3 centres -  21 points
                       0 centres -   0 points
                 """) % {'soloer_pts': self.soloer_pts}

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        soloer = state.soloer()
        for p in state.all_powers():
            if soloer is None:
                retval[p] = self.dots_to_pts[state.dot_count(p)]
            else:
                retval[p] = 0
                if p == soloer:
                    retval[p] = self.soloer_pts
        return _sorted_scores(retval, state)
