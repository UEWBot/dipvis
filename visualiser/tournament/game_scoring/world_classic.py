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
This module contains a class that implements the World Classic and Summer Classic scoring systems.
"""
from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR
from tournament.game_scoring.game_scoring_system import GameScoringSystem


class GScoringWorldClassic(GameScoringSystem):
    """
    World Classic scoring system

    Solo gets 420. Others get 0.
    Otherwise 10 points per SC, 30 for surviving to the end/draw.
    48 pool for board topping, optionally only if 1 or 2 people top.
    1 point for year survived if eliminated by a non-solo.
    """
    def __init__(self, name, no_3ways=False):
        self.no_3ways = no_3ways
        self.name = name

    @property
    def description(self):
        if self.no_3ways:
            topping_str = '48 extra points for a solo board topper, 24 each if 2 people top.'
        else:
            topping_str = '48 pool for board topping, split between all toppers.'
        return _("""
                 Solo gets 420. Others get 0.
                 Otherwise 10 points per SC, 30 for surviving to the end/draw.
                 %(topping_str)s
                 1 point for year survived if eliminated by a non-solo.
                 """) % {'topping_str': topping_str}

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        leader_scs = state.highest_dot_count()
        num_leaders = state.num_powers_with(leader_scs)
        soloer = state.soloer()
        soloed = soloer is not None
        if soloed:
            solo_year = state.solo_year()
        for p in state.all_powers():
            dots = state.dot_count(p)
            # 1 point per year survived if eliminated, regardless of the game result
            if dots == 0:
                retval[p] = state.year_eliminated(p) - FIRST_YEAR
                continue
            # Scoring a soloed game is different
            if soloed:
                if p == soloer:
                    retval[p] = 420
                else:
                    # Everyone else does still get survival points up to the solo year
                    retval[p] = solo_year - FIRST_YEAR
                continue
            # 10 points per SC
            retval[p] = 10 * dots
            # 30 for surviving
            retval[p] += 30
            # 48 split between board toppers
            if dots == leader_scs:
                if self.no_3ways:
                    # Topper bonus is void if 3 or more people share the top
                    if num_leaders < 3:
                        retval[p] += 48 / num_leaders
                else:
                    # Split the topper bonus between all toppers
                    retval[p] += 48 / num_leaders
        return retval
