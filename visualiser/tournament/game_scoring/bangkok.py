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
    Bangkok scoring system

    In a draw,
      Everyone gets 1 point per centre.
      12 points is divided between dominating players:
        Some shares to topping players (top_shares)
        Some shares to players 1 centre from the top (one_away_shares)
        Some shares to players 2 centres from the top (two_away_shares)
        points = 12 * (player's shares) / sum of all shares
      3 points to all surviving players
      0.3 points per year survived for eliminated players
    In a solo:
      Soloer gets some points (soloer_points)
      Everyone else gets some points per centre (loser_points_per_dot)
    """
    def __init__(self, name, soloer_points, loser_points_per_dot, top_shares, one_away_shares, two_away_shares):
        self.name = name
        self.soloer_points = soloer_points
        self.loser_points_per_dot = loser_points_per_dot
        self.top_shares = top_shares
        self.one_away_shares = one_away_shares
        self.two_away_shares = two_away_shares
        self.dead_score_can_change = True

    @property
    def description(self):
        if self.loser_points_per_dot > 0:
            loser_str = _('Everyone else gets %(points).1f points per centre') % {'points': self.loser_points_per_dot}
        else:
            loser_str = _('Everyone else gets no points')
        return _("""
                 In a draw,
                   Everyone gets 1 point per centre.
                   12 points is divided between dominating players:
                     %(top_shares).1f shares to topping players
                     %(one_away_shares).1f shares to players 1 centre from the top
                     %(two_away_shares).1f shares to players 2 centres from the top
                     points = 12 * (player's shares) / sum of all shares
                   3 points to all surviving players
                   0.3 points per year survived for eliminated players
                 In a solo:
                   Soloer gets %(soloer_points)d points
                 """) % {'soloer_points': self.soloer_points,
                         'top_shares': self.top_shares,
                         'one_away_shares': self.one_away_shares,
                         'two_away_shares': self.two_away_shares} + loser_str

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
                    retval[p] = self.soloer_points
                else:
                    retval[p] = self.loser_points_per_dot * dots
        else:
            shares = {}
            leader_scs = state.highest_dot_count()
            for p in all_powers:
                dots = state.dot_count(p)
                retval[p] = dots
                # Store shares for domination bonus
                if dots == leader_scs:
                    shares[p] = self.top_shares
                elif dots == leader_scs - 1:
                    shares[p] = self.one_away_shares
                elif dots == leader_scs - 2:
                    shares[p] = self.two_away_shares
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
