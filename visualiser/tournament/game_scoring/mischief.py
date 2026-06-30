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
This module contains a class that implements the Mischief scoring system.
"""
from django.utils.translation import gettext as _

from .game_scoring_system import GameScoringSystem


class GScoringMischief(GameScoringSystem):
    """
    Mischief scoring system

    Solo gets 34. Others get 0.
    Otherwise 1 point per SC.
    5 point bonus for a lone board top.
    1 point bonus for a 2-way shared board top.
    """
    def __init__(self):
        self.name = _('Mischief')

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        leader_scs = state.highest_dot_count()
        num_leaders = state.num_powers_with(leader_scs)
        soloer = state.soloer()
        soloed = soloer is not None
        for p in state.all_powers():
            dots = state.dot_count(p)
            # Scoring a soloed game is different
            if soloed:
                if p == soloer:
                    retval[p] = 34
                else:
                    retval[p] = 0
                continue
            # 1 point per SC
            retval[p] = 1 * dots
            # 5- or 1-point bonus for board toppers
            if dots == leader_scs:
                if num_leaders == 1:
                    retval[p] += 5
                elif num_leaders == 2:
                    retval[p] += 1
        return retval
