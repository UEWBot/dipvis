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
This module contains a class that implements the Carnage scoring systems.
"""
from operator import itemgetter

from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import TOTAL_SCS
from tournament.game_scoring.base import GameScoringSystem
from tournament.game_scoring.utils import _adjust_rank_score
from tournament.game_scoring.utils import _sorted_scores


class GScoringCarnage(GameScoringSystem):
    """
    Carnage scoring system

    Position grants a set number of points, with ties splitting those points.
    Each power gets some set points per centre owned at the end, unless there's
    a solo, in which case the soloer gets all the SC points.
    Eliminated powers either get position points based on when they were
    eliminated or all split position points.
    In the centre-based version, losers to a solo also get some points.
    """
    def __init__(self, name, centre_based, dead_equal, pts_per_dot_lead):
        self.name = name
        self.dead_score_can_change = True
        self.dead_equal = dead_equal
        self.pts_per_dot_lead = pts_per_dot_lead
        if centre_based:
            self.points_per_dot = 500
            self.position_pts = [7007, 6006, 5005, 4004, 3003, 2002, 1001]
            self.solo_pts = 39028
            self.loss_pts = 1000
        else:
            self.points_per_dot = 1
            self.position_pts = [7000, 6000, 5000, 4000, 3000, 2000, 1000]
            self.solo_pts = sum(self.position_pts) + TOTAL_SCS
            self.loss_pts = 0

    @property
    def description(self):
        if self.pts_per_dot_lead != 0:
            lead_str = _(' Leader gets an additional %(points)d points per centre ahead of second place power.') % {'points': self.pts_per_dot_lead}
        else:
            lead_str = ''
        base = _("""
                 If any power soloed, they get %(solo_pts)d points and all others get %(loss_pts)d.
                 Otherwise, all powers score %(dot_pts)d point per centre owned at the end plus
                 points for their final position.%(lead_str)s
                 Position points are %(pos_1)d, %(pos_2)d, %(pos_3)d, %(pos_4)d, %(pos_5)d,
                 %(pos_6)d, or %(pos_7)d, with ties splitting those points.
                 """) % {'solo_pts': self.solo_pts,
                         'loss_pts': self.loss_pts,
                         'dot_pts': self.points_per_dot,
                         'pos_1': self.position_pts[0],
                         'pos_2': self.position_pts[1],
                         'pos_3': self.position_pts[2],
                         'pos_4': self.position_pts[3],
                         'pos_5': self.position_pts[4],
                         'pos_6': self.position_pts[5],
                         'pos_7': self.position_pts[6],
                         'lead_str': lead_str,
                         }
        if self.dead_equal:
            return base + _('Eliminated powers all split position points.')
        else:
            return base + _('Eliminated powers get position points based on when they were eliminated.')


    def scores(self, state):
        """
        Return a dict, indexed by power id, of scores.
        """
        retval = {}

        # Solos are special
        soloer = state.soloer()
        if soloer is not None:
            for p in state.all_powers():
                if p == soloer:
                    retval[p] = self.solo_pts
                else:
                    retval[p] = self.loss_pts
            return retval

        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        dots.sort(key = itemgetter(1), reverse=True)

        # Giving all the dead powers equal scores is easy
        if self.dead_equal:
            # Tweak the ranking points to allow for ties
            rank_pts = _adjust_rank_score(dots, self.position_pts)
            for i, (p, c) in enumerate(dots):
                retval[p] = c + rank_pts[i]
            return _sorted_scores(retval, state)

        # Split out the eliminated powers
        live_scs = [(p, c) for (p, c) in dots if c > 0]
        pos_pts_1 = self.position_pts[:len(live_scs)]
        # Tweak the alive powers points to allow for ties
        rank_pts = _adjust_rank_score(live_scs, pos_pts_1)
        for i, (p, c) in enumerate(live_scs):
            retval[p] = self.points_per_dot * c + rank_pts[i]
 
        # Give the leader additional points per centre ahead
        dots_1 = live_scs[0][1]
        dots_2 = live_scs[1][1]
        lead = dots_1 - dots_2
        if lead:
            retval[live_scs[0][0]] += lead * self.pts_per_dot_lead

        # If nobody was eliminated, we're done
        if len(self.position_pts) == len(pos_pts_1):
            return _sorted_scores(retval, state)

        dead_scs = [(p, c) for (p, c) in dots if c == 0]
        pos_pts_2 = self.position_pts[len(pos_pts_1) - len(self.position_pts):]
        # Find when the dead powers died
        dummys = []
        for p, c in dead_scs:
            year = state.year_eliminated(p)
            # For both year and SC count, higher is better
            dummys.append((p, year))
        dummys.sort(key=itemgetter(1), reverse=True)
        rank_pts = _adjust_rank_score(dummys, pos_pts_2)
        for i, (p, c) in enumerate(dummys):
            retval[p] = rank_pts[i]
        return _sorted_scores(retval, state)
