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
This module contains a class that implements the Tribute scoring system.
"""
from django.utils.translation import gettext as _

from tournament.game_scoring.game_scoring_system import GameScoringSystem


class GScoringTribute(GameScoringSystem):
    """
    Tribute scoring system

    1 point per dot, survivors split 66 points
    equally between them.
    Each player pays the board leader(s) 1 point for each dot
    the leader has over 6. This payment cannot exceed the survival points.
    With a solo, soloer gets 100, everyone else gets 0.
    """
    def __init__(self):
        self.name = _('Tribute')

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        num_survivors = len(state.survivors())
        survival_points = 66 / num_survivors
        leader_scs = state.highest_dot_count()
        num_leaders = state.num_powers_with(leader_scs)
        if leader_scs > 6:
            bonus_per_survivor = min(survival_points, leader_scs - 6)
        else:
            bonus_per_survivor = 0
        soloer = state.soloer()
        soloed = soloer is not None
        for p in state.all_powers():
            if soloed:
                if p == soloer:
                    retval[p] = 100
                else:
                    retval[p] = 0
                continue
            # 1 point per dot
            dots = state.dot_count(p)
            retval[p] = dots
            # Plus the survival points
            if dots:
                retval[p] += survival_points
            # Leader(s) gets tribute
            if dots == leader_scs:
                retval[p] += bonus_per_survivor * (num_survivors - num_leaders) / num_leaders
            # from all the rest
            elif dots:
                retval[p] -= bonus_per_survivor
        return retval
