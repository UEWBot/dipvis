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
This module contains a class that implements the C-Diplo scoring systems.
"""
from operator import itemgetter

from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import WINNING_SCS
from tournament.game_scoring.game_scoring_system import GameScoringSystem
from tournament.game_scoring.utils import _adjust_rank_score
from tournament.game_scoring.utils import _sorted_scores


class GScoringCDiplo(GameScoringSystem):
    """
    C-Diplo scoring system

    If there is a solo:
    - Soloers score a set number of points (soloer_pts).
    - Losers to a solo may optionally also score some set number of
      points (loss_pts).
    Otherwise:
    - Participants get some points (played_pts).
    - Everyone gets one point per centre owned.
    - Power with the most centres gets a set number of points (first_pts).
    - Power with the second most centres gets a set number of
      points (second_pts).
    - Power with the third most centres gets a set number of
      points (third_pts).
    - if powers are tied for rank, they split the points for their ranks.
    """
    def __init__(self, name, soloer_pts, played_pts,
                 first_pts, second_pts, third_pts, loss_pts=0.0):
        self.name = name
        self.dead_score_can_change = loss_pts != played_pts
        self.soloer_pts = soloer_pts
        self.played_pts = played_pts
        self.position_pts = [first_pts, second_pts, third_pts]
        self.loss_pts = loss_pts

    @property
    def description(self):
        return _("""
                 If there is a solo:
                 - Soloers score %(soloer_pts)d.
                 - Losers to a solo score %(loss_pts)d.
                 Otherwise:
                 - Participants get %(played_pts)d.
                 - Everyone gets one point per centre owned.
                 - Power with the most centres gets %(first_pts)d.
                 - Power with the second most centres gets %(second_pts)d.
                 - Power with the third most centres gets %(third_pts)d.
                 - if powers are tied for rank, they split the points for their ranks.
                 """) % {'soloer_pts': self.soloer_pts,
                        'played_pts': self.played_pts,
                        'first_pts': self.position_pts[0],
                        'second_pts': self.position_pts[1],
                        'third_pts': self.position_pts[2],
                        'loss_pts': self.loss_pts}

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        dots.sort(key = itemgetter(1), reverse=True)
        # Tweak the ranking points to allow for ties
        rank_pts = _adjust_rank_score(dots, self.position_pts)
        for i, (p, c) in enumerate(dots):
            if dots[0][1] >= WINNING_SCS:
                retval[p] = self.loss_pts
                if c >= WINNING_SCS:
                    retval[p] = self.soloer_pts
            else:
                retval[p] = self.played_pts + c + rank_pts[i]
        return _sorted_scores(retval, state)
