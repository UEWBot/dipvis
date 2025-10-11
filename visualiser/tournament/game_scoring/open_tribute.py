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
This module contains a class that implements the Open Tribute scoring system.
"""
from math import floor

from django.utils.translation import gettext as _

from tournament.game_scoring.base import GameScoringSystem


class GScoringOpenTribute(GameScoringSystem):
    """
    OpenTribute scoring system

    Base score of 34 plus 3 points per dot.
    Each player pays the board leader(s) 1 point for each dot
    the leader has more than them.
    Eliminated players lose all remaining points, scoring zero.
    If the board top is shared by N players, each gets 1/(N^2) of the total tribute, rounded down.
    With a solo, soloer gets 340, everyone else gets 0.
    """
    def __init__(self):
        self.name = _('OpenTribute')

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        leader_scs = state.highest_dot_count()
        num_leaders = state.num_powers_with(leader_scs)
        soloer = state.soloer()
        soloed = soloer is not None
        tribute = 0
        for p in state.all_powers():
            if soloed:
                if p == soloer:
                    retval[p] = 340
                else:
                    retval[p] = 0
                continue
            dots = state.dot_count(p)
            if dots:
                # Start with 34
                retval[p] = 34
                # 3 points per dot
                retval[p] += 3 * dots
                # pay the tribute
                t = leader_scs - dots
                retval[p] -= t
                tribute += t
            else:
                retval[p] = 0
                # pay the tribute
                tribute += leader_scs
        if not soloed:
            # Leader(s) gets tribute
            for p in state.all_powers():
                dots = state.dot_count(p)
                if dots == leader_scs:
                    retval[p] += floor(tribute / (num_leaders * num_leaders))
        return retval
