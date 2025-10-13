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
This module contains a class that implements the Bangkok scoring system.
"""
from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR
from tournament.game_scoring.game_scoring_system import GameScoringSystem


class GScoringBangkok(GameScoringSystem):
    """
    Bengkok scoring system

    In a draw,
      Everyone gets 1 point per centre.
      12 points is divided between dominating players:
        3 shares to topping players
        2 shares to players 1 centre from the top
        1 share to players 2 centres from the top
        points = 12 * (player's shares) / sum of all shares
      3 points to all surviving players
      0.3 points per year survived for elimnated players
    In a solo:
      Soloer gets 41 points
      Everyone else gets 0.5 points per centre
    """
    def __init__(self):
        self.name = _('Bangkok')
        self.dead_score_can_change = True

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        all_powers = state.all_powers()
        soloer = state.soloer()
        soloed = soloer is not None
        if soloed:
            for p in all_powers:
                dots = state.dot_count(p)
                if p == soloer:
                    retval[p] = 41
                else:
                    retval[p] = 0.5 * dots
        else:
            shares = {}
            leader_scs = state.highest_dot_count()
            for p in all_powers:
                dots = state.dot_count(p)
                retval[p] = dots
                # Store shares for domination bonus
                if dots == leader_scs:
                    shares[p] = 3
                elif dots == leader_scs - 1:
                    shares[p] = 2
                elif dots == leader_scs - 2:
                    shares[p] = 1
                else:
                    shares[p] = 0
                if dots == 0:
                    year = state.year_eliminated(p)
                    retval[p] += 0.3 * (year - FIRST_YEAR)
                else:
                    retval[p] += 3
            # Now add in the domination bonus
            total_shares = sum(shares.values())
            for p in all_powers:
                retval[p] += 12 * shares[p] / total_shares
        return retval
