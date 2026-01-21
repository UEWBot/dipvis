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
This module contains a class that implements the Manorcon scoring systems.
"""
from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR
from tournament.game_scoring.game_scoring_system import GameScoringSystem


class GScoringManorCon(GameScoringSystem):
    """
    ManorCon scoring system

    Solo gets a set number of points. Others get 0.1 per year they survived.
    Otherwise calculate N = S^2 + 4*S + 16 for each power, where S is their centre-count (optionally including N=16 for dead powers).
    Then each surviving power scored 100 * N/(sum of all Ns), and each dead power still scores 0.1 per year they survived.
    """
    def __init__(self, name, solo_score=75, dead_get_16=True):
        self.solo_score = solo_score
        self.dead_get_16 = dead_get_16
        self.name = name

    @property
    def description(self):
        if self.dead_get_16:
            dead_sum_str = ' (including N=16 for dead powers)'
        else:
            dead_sum_str = ''
        return _("""
                 Solo gets %(solo_score)d. Others get 0.1 per year they survived.
                 Otherwise calculate N = S^2 + 4*S + 16 for each power,
                 where S is their centre-count%(dead_sum_str)s.
                 Then each surviving power scored 100 * N/(sum of all Ns),
                 and each dead power still scores 0.1 per year they survived.
                 """) % {'solo_score': self.solo_score,
                         'dead_sum_str': dead_sum_str}

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        soloer = state.soloer()
        soloed = soloer is not None
        if soloed:
            solo_year = state.solo_year()
        sum_of_n = 0.0
        all_powers = state.all_powers()
        for p in all_powers:
            dots = state.dot_count(p)
            # Scoring a soloed game is different
            if soloed:
                # In this case, "sum of N" is irrelevant, so retval is the actual score
                if p == soloer:
                    retval[p] = self.solo_score
                # Everyone else does still get survival points up to the solo year or their elimination year
                else:
                    if dots == 0:
                        year = state.year_eliminated(p)
                    else:
                        year = solo_year
                    retval[p] = 0.1 * (year - FIRST_YEAR)
            else:
                # 0.1 point per season survived if eliminated, regardless of the game result
                if dots == 0:
                    year = state.year_eliminated(p)
                    if self.dead_get_16:
                        n = 16
                    else:
                        n = 0
                    # retval gets the actual score
                    retval[p] = 0.1 * (year - FIRST_YEAR)
                else:
                    # Calculate N for the power
                    n = dots * dots + 4 * dots + 16
                    # Retval gets N, which still needs to be divided
                    retval[p] = n
                # And add N for this power to the total
                sum_of_n += n
        if not soloed:
            for p in all_powers:
                if state.dot_count(p) > 0:
                    retval[p] *= 100 / sum_of_n
        return retval
