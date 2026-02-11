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
This module contains a class that implements the Bangkok Pike scoring system.
"""
from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR
from tournament.game_scoring.game_scoring_system import GameScoringSystem


class GScoringBangkokPike(GameScoringSystem):
    """
    Bengkok Pike scoring system

    In a draw,
      3 points for having at least 1 supply centre
      1 point per supply centre
      Lone board topper gets a 6-point bonus
      If 2 or more players are tied for top, they each get 4 points
      Everyone with exactly 1 centre less than the board topper(s)
      gets a 4 point bonus
      If there's a lone board topper and nobody has exactly 1 centre less
      than them, the board topper also gets this 4-point bonus
      Everyone with exactly 2 centres less than the board topper(s)
      gets a 2 point bonus
      If there's a lone board topper and nobody has exactly 2 centres less
      than them, the board topper also gets this 2-point bonus
      Eliminated players get 0.1 points for each game year they played
    In a solo:
      Soloer gets 60 points
      Everyone else gets points as if they were eliminated
    """
    def __init__(self):
        self.name = _('Bangkok Pike')
        self.dead_score_can_change = False

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        all_powers = state.all_powers()
        soloer = state.soloer()
        soloed = soloer is not None
        if soloed:
            solo_year = state.solo_year()
            for p in all_powers:
                dots = state.dot_count(p)
                if p == soloer:
                    retval[p] = 60
                else:
                    if dots == 0:
                        year = state.year_eliminated(p)
                    else:
                        year = solo_year
                    retval[p] = 0.1 * (1 + year - FIRST_YEAR)
        else:
            leader_scs = state.highest_dot_count()
            num_toppers = state.num_powers_with(leader_scs)
            for p in all_powers:
                # 1 point per supply centre
                dots = state.dot_count(p)
                retval[p] = dots
                # Bonus for board topper
                if dots == leader_scs:
                    if num_toppers == 1:
                        retval[p] += 6
                        if state.num_powers_with(leader_scs - 1) == 0:
                            # Topper also gets the 4-point bonus
                            retval[p] += 4
                        if state.num_powers_with(leader_scs - 2) == 0:
                            # Topper also gets the 2-point bonus
                            retval[p] += 2
                    else:
                        retval[p] += 4
                # Bonus for 1-centre away from topper
                elif dots == leader_scs - 1:
                    retval[p] += 4
                # Bonus for 2-centres away from topper
                elif dots == leader_scs - 2:
                    retval[p] += 2
                # Points for survival, or pity points
                if dots == 0:
                    year = state.year_eliminated(p)
                    retval[p] += 0.1 * (1 + year - FIRST_YEAR)
                else:
                    retval[p] += 3
        return retval
