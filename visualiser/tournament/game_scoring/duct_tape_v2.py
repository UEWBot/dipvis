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
This module contains a class that implements the Duct Tape V2 scoring system.
"""
from operator import itemgetter

from django.utils.translation import gettext as _

from .game_scoring_system import GameScoringSystem
from .utils import _adjust_rank_score, _sorted_scores


class GScoringDuctTapeV2(GameScoringSystem):
    """
    Duct Tape V2 scoring system

    If any power soloed, they score 75 points and all others score 0.
    Otherwise, all powers score 1 point per centre owned at the end, plus
    points for their final rank.
    Eliminated powers either split rank points equally with other
    eliminated powers, or (if elimination order is used) have ties broken
    by the order in which they were eliminated, with those eliminated
    later scoring higher.
    """
    RANK_PTS = [40, 24, 15, 9, 6, 3, 3]
    SOLO_PTS = 75

    def __init__(self, name, elimination_order):
        self.name = name
        self.dead_score_can_change = True
        self.elimination_order = elimination_order

    @property
    def description(self):
        base = _("""
                 If any power soloed, they score %(solo_pts)d points and all
                 others score 0.
                 Otherwise, all powers score 1 point per centre owned at the
                 end, plus points for their final rank.
                 Rank points are %(rank_1)d, %(rank_2)d, %(rank_3)d, %(rank_4)d,
                 %(rank_5)d, %(rank_6)d, and %(rank_7)d, with ties splitting
                 those points.
                 """) % {'solo_pts': self.SOLO_PTS,
                         'rank_1': self.RANK_PTS[0],
                         'rank_2': self.RANK_PTS[1],
                         'rank_3': self.RANK_PTS[2],
                         'rank_4': self.RANK_PTS[3],
                         'rank_5': self.RANK_PTS[4],
                         'rank_6': self.RANK_PTS[5],
                         'rank_7': self.RANK_PTS[6],
                         }
        if self.elimination_order:
            return base + _('Eliminated powers have ties broken by the order '
                             'in which they were eliminated, with those '
                             'eliminated later scoring higher.')
        else:
            return base + _('Eliminated powers split rank points '
                             'equally with other eliminated powers.')

    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}

        # Solos are special - no centre points for anyone, including the soloer
        soloer = state.soloer()
        if soloer is not None:
            for p in state.all_powers():
                retval[p] = self.SOLO_PTS if p == soloer else 0
            return retval

        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        dots.sort(key=itemgetter(1), reverse=True)

        if not self.elimination_order:
            # Ties (including among eliminated powers) simply split rank points
            rank_pts = _adjust_rank_score(dots, self.RANK_PTS)
            for i, (p, c) in enumerate(dots):
                retval[p] = c + rank_pts[i]
            return _sorted_scores(retval, state)

        # Split out the eliminated powers so ties among them can be broken by elimination order
        live_scs = [(p, c) for (p, c) in dots if c > 0]
        rank_pts_1 = self.RANK_PTS[:len(live_scs)]
        rank_pts = _adjust_rank_score(live_scs, rank_pts_1)
        for i, (p, c) in enumerate(live_scs):
            retval[p] = c + rank_pts[i]

        # If nobody was eliminated, we're done
        if len(self.RANK_PTS) == len(rank_pts_1):
            return _sorted_scores(retval, state)

        dead_scs = [(p, c) for (p, c) in dots if c == 0]
        rank_pts_2 = self.RANK_PTS[len(rank_pts_1):]
        # Powers eliminated later rank (and score) higher than those eliminated earlier
        dummys = [(p, state.year_eliminated(p)) for p, c in dead_scs]
        dummys.sort(key=itemgetter(1), reverse=True)
        rank_pts = _adjust_rank_score(dummys, rank_pts_2)
        for i, (p, c) in enumerate(dummys):
            retval[p] = rank_pts[i]
        return _sorted_scores(retval, state)
