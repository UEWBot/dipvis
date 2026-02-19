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
This module contains a class that implements the Ranked Classic scoring system.
"""
from operator import itemgetter

from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import (FIRST_YEAR,
                                                          WINNING_SCS)
from tournament.game_scoring.game_scoring_system import GameScoringSystem
from tournament.game_scoring.utils import (_adjust_rank_score_lower_special,
                                           _sorted_scores)


class GScoringRankedClassic(GameScoringSystem):
    """
    Ranked Classic scoring system

    Games that end by draw vote or timing out score as follows:
     - Players score 10 points per supply center.
     - Eliminated players get 1 point for every year survived.
     - Surviving players get a 30 point survival bonus.
     - Surviving players are ranked by their ending supply center count
       and score a ranking bonus as follows:
         7th: 10 points
         6th: 20 points (15 if tied by 2 players)
         5th: 30 points (25 if tied by 2 players)
         4th: 40 points (35 if tied by 2 players)
         3rd: 60 points (50 if tied by 2 players)
         2nd: 90 points (70 if tied by 2 players)
         1st: 200 points (135 if tied by 2 players)
       If there is a tie for a particular rank between three or more players,
       those players receive the score for the lower of the rankings (i.e.,
       in a 3-way tie for 1st place, those players are all ranked third; in
       a 4-way tie for 4th, those players are ranked seventh, etc).
    Games that end in solos score as follows:
     - The soloing player gets 550 points.
     - All other players get 1 point for every year survived.
    """
    def __init__(self):
        self.name = _('Ranked Classic')
        self.position_points = [200, 90, 60, 40, 30, 20, 10]
        self.position_points_2_tied = [135, 70, 50, 35, 25, 15]
        self.dead_score_can_change = False

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
                    retval[p] = 550
                elif c > 0:
                    # Player counts as eliminated in the solo year
                    retval[p] = solo_year - FIRST_YEAR
                else:
                    retval[p] = state.year_eliminated(p) - FIRST_YEAR
        else:
            dots.sort(key = itemgetter(1), reverse=True)
            # Tweak the ranking points to allow for ties
            rank_pts = _adjust_rank_score_lower_special(dots,
                                                        self.position_points,
                                                        self.position_points_2_tied)
            for i, (p, c) in enumerate(dots):
                if c < 1:
                    # Eliminated players only get participation points
                    retval[p] = state.year_eliminated(p) - FIRST_YEAR
                else:
                    retval[p] = 30 + (10 * c) + rank_pts[i]
        return _sorted_scores(retval, state)
