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
This module contains a class that implements the Solos scoring system.
"""
from django.utils.translation import gettext as _

from tournament.game_scoring.base import GameScoringSystem


class GScoringSolos(GameScoringSystem):
    """
    Only solo victories get points.

    Solos score 100 points.
    Other results score 0.
    """
    def __init__(self):
        self.name = _(u'Solo or bust')

    def scores(self, state):
        """
        If any power soloed, they get 100 points.
        Otherwise, they get 0.
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        for p in state.all_powers():
            retval[p] = 0.0
            if state.soloer() == p:
                retval[p] = 100.0
        return retval
