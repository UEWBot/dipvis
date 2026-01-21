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
This module contains a class that implements the Base 3 scoring system.
"""
from django.utils.translation import gettext as _

from tournament.game_scoring.game_scoring_system import GameScoringSystem


class GScoringBase3(GameScoringSystem):
    """
    Base 3 scoring system

    1 point per centre
    3 points for survival
    9 point bonus for topping the board, divided by by 3 for each additional person
    sharing the top (9 points for lone top, 3 each for 2-way top, 1 each for 3-way top, etc)
    Solos score 46 points.
    Elimination or loss to a solo scores 0.
    """
    def __init__(self):
        self.name = _('Base 3')

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        soloer = state.soloer()
        soloed = soloer is not None
        leader_scs = state.highest_dot_count()
        num_leaders = state.num_powers_with(leader_scs)
        # Calculate the bonus each board topper gets
        bonus = 9.0 / (3 ** (num_leaders - 1))
        for p in state.all_powers():
            retval[p] = 0.0
            if soloed:
                if soloer == p:
                    retval[p] = 46.0
            else:
                dots = state.dot_count(p)
                if dots:
                    # 3 points for survival plus 1 per centre
                    retval[p] = 3.0 + dots
                # Bonus points for board toppers
                if dots == leader_scs:
                   retval[p] += bonus
        return retval
