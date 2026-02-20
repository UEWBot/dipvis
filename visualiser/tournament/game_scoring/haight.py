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
This module contains a class that implements the Haight scoring system.
"""
from operator import itemgetter

from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import (FIRST_YEAR,
                                                          WINNING_SCS)
from tournament.game_scoring.game_scoring_system import GameScoringSystem
from tournament.game_scoring.utils import (_adjust_rank_score_lower,
                                           _sorted_scores)


class GScoringHaight(GameScoringSystem):
    """
    Haight scoring system

    Games that end by draw vote or timing out score as follows:
     - Players score 10 points per supply center.
     - Eliminated players get 1 point for every year played.
     - Players are ranked by their ending supply center count or order of
       elimination and score a ranking bonus as follows:
         7th: 0 points
         6th: 11 points
         5th: 22 points
         4th: 33 points
         3rd: 44 points
         2nd: 55 points
         1st: 66 points
       If there is a tie for a particular rank, both players receive the score
       for the lower of the rankings (i.e., in a 2-way tie for 1st place, both
       players get 55 points; in a 3-way tie for 1st, all 3 players get 44
       points; in a 2-way tie for 2nd place both players get 44 points, etc).
       If there is a single player topping the board, they receive a bonus
       equally to 5 times the difference between their SC count and the
       next highest SC count (e.g., the board topper has 12 centers and the
       next largest power has 9, the board topper receives a bonus of
       5x3=15 points). This bonus is not awarded if there is a shared top.
    Games that end in solos score as follows:
     - The soloing player gets 451 points.
     - Surviving players get 5 points per SC, or points equal to the
       number of years played, whichever is greater.
     - Eliminated players score 1 point for every year they played,
       including the year eliminated.
     - Ranking points are not awarded.
    """
    def __init__(self):
        self.name = _('Haight v1.0')
        self.position_points = [66, 55, 44, 33, 22, 11]
        self.dead_score_can_change = True

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        if state.soloer() is not None:
            solo_year = state.solo_year()
            for p, c in dots:
                if c >= WINNING_SCS:
                    retval[p] = 451
                elif c > 0:
                    retval[p] = max(5 * c, 1 + solo_year - FIRST_YEAR)
                else:
                    retval[p] = 1 + state.year_eliminated(p) - FIRST_YEAR
        else:
            # We want to order eliminations by year eliminated
            # so here we add fractional dots for years survived
            for i, (p, c) in enumerate(dots):
                if c == 0:
                    dots[i] = (p, (state.year_eliminated(p) - FIRST_YEAR)/100)
            dots.sort(key=itemgetter(1), reverse=True)
            # Tweak the ranking points to allow for ties
            rank_pts = _adjust_rank_score_lower(dots, self.position_points)
            for i, (p, c) in enumerate(dots):
                if c < 1:
                    retval[p] = 1 + state.year_eliminated(p) - FIRST_YEAR + rank_pts[i]
                else:
                    retval[p] = 10 * c + rank_pts[i]
            # Add leader bonus for lone board topper, if applicable
            if dots[0][1] != dots[1][1]:
                retval[dots[0][0]] += 5 * (dots[0][1] - dots[1][1])
        return _sorted_scores(retval, state)
