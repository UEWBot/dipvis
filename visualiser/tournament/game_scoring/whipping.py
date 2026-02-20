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
This module contains a class that implements the Whipping scoring system.
"""
from operator import itemgetter

from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import (FIRST_YEAR,
                                                          WINNING_SCS)
from tournament.game_scoring.game_scoring_system import GameScoringSystem
from tournament.game_scoring.utils import _sorted_scores


class GScoringWhipping(GameScoringSystem):
    """
    Whipping scoring system

    If there is a solo:
    - Soloers score a set number of points (soloer_pts).
    - Survivors who lose to a solo score as if they were eliminated when the solo occurred.
    Otherwise:
    - Eliminated powers get one point per year played.
    - Everyone gets ten points per centre owned.
    - Surviving powers share 60 points equally between them.
    - The power with the most centres gets a bonus of twice the number of SCs owned.
    - If multiple powers are tied for board top, no board topping bonus is awarded.
    """
    def __init__(self, name, soloer_pts):
        self.soloer_pts = soloer_pts
        self.name = name

    @property
    def description(self):
        return _("""
                 If there is a solo:
                 - Soloers score %(soloer_pts)d.
                 - Survivors who lose to a solo score as if they were eliminated when the solo occurred.
                 Otherwise:
                 - Eliminated powers get one point per year played.
                 - Everyone gets ten points per centre owned.
                 - Surviving powers share 60 points equally between them.
                 - The power with the most centres gets a bonus of twice the number of SCs owned.
                 - If multiple powers are tied for board top, no board topping bonus is awarded.
                 """) % {'soloer_pts': self.soloer_pts}

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        dots.sort(key=itemgetter(1), reverse=True)
        topper_scs = dots[0][1]
        for i, (p, c) in enumerate(dots):
            if topper_scs >= WINNING_SCS:
                if c >= WINNING_SCS:
                    retval[p] = self.soloer_pts
                elif c > 0:
                    retval[p] = state.solo_year() - (FIRST_YEAR - 1)
                else:
                    retval[p] = state.year_eliminated(p) - (FIRST_YEAR - 1)
            else:
                if c == 0:
                    retval[p] = state.year_eliminated(p) - (FIRST_YEAR - 1)
                else:
                    retval[p] = (10 * c) + (60 / len(state.survivors()))
                    if c == topper_scs:
                        if state.num_powers_with(topper_scs) == 1:
                            retval[p] += topper_scs * 2
        return _sorted_scores(retval, state)
