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
This module contains a class that implements the C-Diplo Namur scoring system.
"""
from operator import itemgetter

from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import WINNING_SCS
from tournament.game_scoring.game_scoring_system import GameScoringSystem
from tournament.game_scoring.utils import _adjust_rank_score
from tournament.game_scoring.utils import _sorted_scores


class GScoringCDiploNamur(GameScoringSystem):
    """
    C-Diplo Namur scoring system

    If there is a solo:
    - Soloers score 85 points
    - Everyone else scores zero
    Otherwise:
    - Participants gets one point
    - Everyone who owns centre(s) gets some points:
      1 SC = 5pts, 2 SCs = 9 pts, 3 SCs = 12 pts, 4 SCs = 14 pts, 5 SCs = 16 pts,
      6 SCs = 18 pts, _1 pt per additional SC
    - Power with the most points gets 38 points
    - Power in second place gets 14 points
    - Power in third place gets 7 points
    - if powers are tied for rank, they split the total points for their ranks.
    """
    def __init__(self):
        self.name = _(u'C-Diplo Namur')
        # Losers to a solo don't get their participation point
        self.dead_score_can_change = True
        self.position_pts = [38, 14, 7]
        self.sc_pts = [0, 5, 9, 12, 14, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        dots.sort(key = itemgetter(1), reverse=True)
        # Tweak the ranking points to allow for ties
        rank_pts = _adjust_rank_score(dots, self.position_pts)
        for i, (p, c) in enumerate(dots):
            if dots[0][1] >= WINNING_SCS:
                retval[p] = 0
                if c >= WINNING_SCS:
                    retval[p] = 85
            else:
                retval[p] = 1 + self.sc_pts[c] + rank_pts[i]
        return _sorted_scores(retval, state)
