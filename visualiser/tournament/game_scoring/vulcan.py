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
This module contains a class that implements the Vulcan scoring system.
"""
from operator import itemgetter

from django.utils.translation import gettext as _

from tournament.game_scoring.game_scoring_system import GameScoringSystem
from tournament.game_scoring.utils import _adjust_rank_score, _sorted_scores


class GScoringVulcan(GameScoringSystem):
    """
    Vulcan scoring system

    Eliminated players score zero.
    If there is a solo:
    - Soloers get 130 points
    - Losers to a solo get 5 points if they survived.
    Otherwise, players score as follows:
    1 point per centre
    1 point for each centre between you and everyone below you (including eliminated players)
    10 point bonus for topping, split between topping players if there's a joint top.
    5 points for suriving the game
    """
    def __init__(self):
        self.name = 'Vulcan'
        self.dead_score_can_change = False

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        soloer = state.soloer()
        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        # sort lowest-to-highest dot count
        dots.sort(key = itemgetter(1))
        max_dots = dots[-1][1]
        # This is the dot count of the last player we looked at (if any)
        last_dots = 0
        # This is the gap bonus for the last player we looked at
        last_gap_bonus = 0
        for n, (p,c) in enumerate(dots):
            if c == 0:
                retval[p] = 0
            elif soloer is None:
                # 1 point per centre plus 5 for survival
                retval[p] = c + 5
                #retval[p] = 5
                # plus 1 point for each centre between you and everyone below you
                gap_bonus = last_gap_bonus + (c - last_dots) * n
                retval[p] += gap_bonus
                last_gap_bonus = gap_bonus
                # 10 points for topping, split between toppers
                if c == max_dots:
                    retval[p] += 10 / state.num_powers_with(max_dots)
            else:
                # 5 points for survival
                retval[p] = 5
                # Soloer gets 130
                if p == soloer:
                    retval[p] = 130
            # Remember this centrecount
            last_dots = c
        return _sorted_scores(retval, state)
