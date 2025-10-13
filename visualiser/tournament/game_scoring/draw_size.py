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
This module contains a class that implements the draw size scoring system.
"""
from django.utils.translation import gettext as _

from tournament.game_scoring.game_scoring_system import GameScoringSystem


class GScoringDrawSize(GameScoringSystem):
    """
    Draw Size scoring system

    Solos score 100 points.
    Draw sharers split 100 points between them.
    """
    def __init__(self):
        self.name = _(u'Draw size')

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.

        If any power soloed, they get 100 points.
        Otherwise, if a draw passed, all powers in the draw equally shared 100
        points between them.
        Otherwise, all surviving powers equally share 100 points between them.
        """
        retval = {}
        survivors = state.powers_in_draw()
        soloed = state.soloer() is not None
        for p in state.all_powers():
            retval[p] = 0.0
            if p == state.soloer():
                retval[p] = 100.0
            elif soloed:
                # Leave the score at zero
                pass
            elif p in survivors:
                retval[p] = 100.0 / len(survivors)
            # This leaves dead powers, or those excluded from a draw, with zero
        return retval
