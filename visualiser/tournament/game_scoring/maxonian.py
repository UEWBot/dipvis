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
This module contains a class that implements the Maxonian and 7Eleven scoring systems
"""
from django.utils.translation import gettext as _

from tournament.diplomacy import WINNING_SCS

from .game_scoring_system import GameScoringSystem
from .utils import _countback_rank_scores, _sorted_scores


class GScoringMaxonian(GameScoringSystem):
    """
    Maxonian scoring system

    Players are ranked by supply centre count.
    Top-ranked player gets 7 points, second gets 6, third gets 5,
    fourth gets 4, fifth gets 3, sixth gets 2, and last gets 1.
    If two players are tied, their SC counts in previous years
    are compared, and the player who most recently was ahead gets
    the higher score.
    If two players had the same supply centre count every year,
    they each score the average of their place and the place below.
    Any player with more than (threshold) supply centres scores 1 additional
    point per SC above that threshold, unless the game was soloed,
    in which case only the soloer gets these points.
    """
    def __init__(self, name, threshold=13):
        self.name = name
        self.rank_points = [7, 6, 5, 4, 3, 2, 1]
        self.bonus_threshold = threshold

    @property
    def description(self):
        return _("""
                 Players are ranked by supply centre count.
                 Top-ranked player gets 7 points, second gets 6, third gets 5,
                 fourth gets 4, fifth gets 3, sixth gets 2, and last gets 1.
                 If two players are tied, their SC counts in previous years
                 are compared, and the player who most recently was ahead gets
                 the higher score.
                 If two players had the same supply centre count every year,
                 they each score the average of their place and the place below.
                 Any player with more than %(threshold)d supply centres scores 1 additional
                 point per SC above that threshold, unless the game was soloed,
                 in which case only the soloer gets these points.
                 """) % {'threshold': self.bonus_threshold}

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        # Get rank points for each power
        retval = _countback_rank_scores(state,
                                        state.last_full_year(),
                                        state.all_powers(),
                                        self.rank_points)
        soloer = state.soloer()

        # add bonus points
        for p in retval.keys():
            d = state.dot_count(p)
            if d > self.bonus_threshold:
                if (soloer is None) or (soloer == p):
                    # All solos score as if they had 18 dots
                    d = min(d, WINNING_SCS)
                    retval[p] += d - self.bonus_threshold

        return _sorted_scores(retval, state)
