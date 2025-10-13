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
This module contains a class that implements the Sum Of Squares scoring system.
"""
from django.utils.translation import gettext as _

from tournament.game_scoring.game_scoring_system import GameScoringSystem
from tournament.game_scoring.utils import _normalise_scores


class GScoringSumOfSquares(GameScoringSystem):
    """
    Sum of Squares scoring system

    Soloer gets 100 points, everyone else gets zero.
    If there is no solo, square each power's final centre-count
    and normalize those numbers to sum to 100 points.
    """
    def __init__(self):
        self.name = _(u'Sum of Squares')

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        retval_solo = {}
        soloer = state.soloer()
        all_powers = state.all_powers()
        for p in all_powers:
            retval_solo[p] = 0.0
            dots = state.dot_count(p)
            retval[p] = dots * dots
            if p == soloer:
                retval_solo[p] = 100.0
        if soloer is not None:
            return retval_solo
        _normalise_scores(retval)
        return retval
