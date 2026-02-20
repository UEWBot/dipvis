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
This module contains a class that implements the Detour 09 soring system.
"""
from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR
from tournament.game_scoring.game_scoring_system import GameScoringSystem
from tournament.game_scoring.utils import _normalise_scores


class GScoringDetour09(GameScoringSystem):
    """
    Detour 09 scoring system

    Soloer gets 110.
    Otherwise, players get 1 per centre held, plus 2 points if they hold any centres,
    If there's a single board topper, that player get points equal to the difference between their
    centre count and that of the player(s) immediately behind them.
    Leader gets 4 points, 2nd gets 3, 3rd gets 2 and 4th gets 1. If players are tied for
    position, they all get the lower position points.
    Finally, scores for a game without a solo are normalised to be out of 100.
    Eliminated players and those who lose to a solo get 0.25 points per year of survival,
    to a maximum of 2 points. A year of survival is when the player has at least 1 centre during
    winter and no other player has 18 or more.
    """
    def __init__(self):
        self.name = _('Detour09')

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        soloer = state.soloer()
        soloed = soloer is not None
        all_powers = state.all_powers()
        leader_scs = state.highest_dot_count()
        # Scoring a soloed game is different
        if soloed:
            for p in all_powers:
                if p == soloer:
                    retval[p] = 110
                else:
                    retval[p] = 0
        else:
            # Do a first pass to allocate the easy points
            for p in all_powers:
                dots = state.dot_count(p)
                retval[p] = dots
                if dots > 0:
                    retval[p] += 2
            # Figure out which power is in which position
            top_powers = sorted(retval, key=retval.get, reverse=True)
            second = top_powers[1]
            # Now do a second pass to allocate position-based points
            for p in all_powers:
                if state.dot_count(p) == leader_scs:
                    # Add gap to second-place power
                    retval[p] += leader_scs - state.dot_count(second)
            # 1st place gets another 4, 2nd 3, 3rd 2 and 4th 1,
            # with ties getting the lower position points
            i = 0
            bonus = 4
            while (bonus > 0) and (i < 4):
                p = top_powers[i]
                dots = state.dot_count(p)
                if state.num_powers_with(dots) == 1:
                    retval[p] += bonus
                elif state.num_powers_with(dots) == 2:
                    bonus -= 1
                    if bonus > 0:
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                elif state.num_powers_with(dots) == 3:
                    bonus -= 2
                    if bonus > 0:
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                elif state.num_powers_with(dots) == 4:
                    bonus -= 3
                    if bonus > 0:
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                else:
                    # No bonus at all
                    break
                i += 1
                bonus -= 1
            _normalise_scores(retval)
        # Survival points for eliminated players and losers to a solo
        if soloed:
            solo_year = state.solo_year()
        for p in all_powers:
            if state.dot_count(p) == 0:
                year = state.year_eliminated(p)
            elif soloed and (p != soloer):
                year = solo_year
            else:
                # No survival points
                continue
            years = year - FIRST_YEAR
            if years > 8:
                years = 8
            retval[p] += 0.25 * years
        return retval
