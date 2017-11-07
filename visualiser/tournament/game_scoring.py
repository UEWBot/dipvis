# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016 Chris Brand
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

# This file contains scoring systems for individual diplomacy games.

from django.utils.translation import ugettext as _

from tournament.diplomacy import TOTAL_SCS, WINNING_SCS

class GameScoringSystem():
    # TODO This doesn't deal with multiple players playing one power
    """
    A scoring system for a Game.
    Provides a method to calculate a score for each player of one game.
    """
    name = u''
    # True for classes that provide building blocks rather than full scoring systems
    is_abstract = True

    def _the_game(self, centre_counts):
        """Returns the game in question."""
        return centre_counts.first().game

    def _final_year(self, centre_counts):
        """Returns the most recent year we have centre counts for."""
        return centre_counts.order_by('-year')[0].year

    def _final_year_scs(self, centre_counts):
        """Returns the CentreCounts for the most recent year only, ordered largest-to-smallest."""
        return centre_counts.filter(year=self._final_year(centre_counts)).order_by('-count')

    def _survivor_count(self, centre_counts):
        """Returns the number of surviving powers"""
        return self._final_year_scs(centre_counts).filter(count__gt=0).count()

    def scores(self, centre_counts):
        """
        Takes the set of CentreCount objects for one Game.
        Returns a dict, indexed by power id, of scores.
        """
        return {}

class GScoringSolos(GameScoringSystem):
    """
    Solos score 100 points.
    Other results score 0.
    """
    def __init__(self):
        self.is_abstract = False
        self.name = _(u'Solo or bust')

    def scores(self, centre_counts):
        """
        If any power soloed, they get 100 points.
        Otherwise, they get 0.
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        # We only care about the most recent centrecounts
        for sc in self._final_year_scs(centre_counts):
            retval[sc.power] = 0
            if sc.count >= WINNING_SCS:
                retval[sc.power] = 100.0
        return retval

class GScoringDrawSize(GameScoringSystem):
    """
    Solos score 100 points.
    Draw sharers split 100 points between them.
    """
    def __init__(self):
        self.is_abstract = False
        self.name = _(u'Draw size')

    def scores(self, centre_counts):
        """
        If any power soloed, they get 100 points.
        Otherwise, if a draw passed, all powers in the draw equally shared 100 points between them.
        Otherwise, all surviving powers equally share 100 points between them.
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        the_game = self._the_game(centre_counts)
        is_dias = the_game.is_dias()
        draw = the_game.passed_draw()
        survivors = self._survivor_count(centre_counts)
        final_scs = self._final_year_scs(centre_counts)
        soloed = final_scs[0].count >= WINNING_SCS
        # We only care about the most recent centrecounts
        for sc in final_scs:
            retval[sc.power] = 0.0
            if sc.count >= WINNING_SCS:
                retval[sc.power] = 100.0
            elif soloed:
                # Leave the score at zero
                pass
            elif draw:
                if sc.power in draw.powers():
                    retval[sc.power] = 100.0 / draw.draw_size()
            elif sc.count > 0:
                retval[sc.power] = 100.0 / survivors
        return retval

def adjust_rank_score(centre_counts, rank_points):
    """
    Takes a list of CentreCounts for one year of one game, ordered highest-to-lowest
    and a list of ranking points for positions, ordered from first place to last.
    Returns a list of ranking points for positions, ordered to correspond to the centre counts,
    having made adjustments for any tied positions.
    Where two or more powers have the same number of SCs, the ranking points for their positions
    are shared eveny between them.
    """
    if len(rank_points) == 0:
        # The rest of them get zero points
        return [] + [0.0] * len(centre_counts)
    # First count up how many powers tied at the top
    i = 0
    count = 0
    points = 0
    scs = centre_counts[0].count
    while (i < len(centre_counts)) and (centre_counts[i].count == scs):
        count += 1
        if i < len(rank_points):
            points += rank_points[i]
        i += 1
    # Now share the points between those tied players
    for j in range(0,i):
        if j < len(rank_points):
            rank_points[j] = points / count
        else:
            rank_points.append(points / count)
    # And recursively continue
    return rank_points[0:i] + adjust_rank_score(centre_counts[i:], rank_points[i:])

class GScoringCDiplo(GameScoringSystem):
    """
    If there is a solo:
    - Soloers score a set number of points (soloer_pts).
    - Losers to a solo may optionally also score some set number of points (loss_pts).
    Otherwise:
    - Participants get some points (played_pts).
    - Everyone gets one point per centre owned.
    - Power with the most centres gets a set number of points (first_pts).
    - Power with the second most centres gets a set number of points (second_pts).
    - Power with the third most centres gets a set number of points (third_pts).
    - if powers are tied for rank, they split the points for their ranks.
    """
    def __init__(self, name, soloer_pts, played_pts, first_pts, second_pts, third_pts, loss_pts=0):
        self.is_abstract = False
        self.name = name
        self.soloer_pts = soloer_pts
        self.played_pts = played_pts
        self.position_pts = [first_pts, second_pts, third_pts]
        self.loss_pts = loss_pts

    def scores(self, centre_counts):
        retval = {}
        final_scs = self._final_year_scs(centre_counts)
        # Tweak the ranking points to allow for ties
        rank_pts = adjust_rank_score(list(final_scs), self.position_pts)
        i = 0
        for sc in final_scs:
            if final_scs[0].count >= WINNING_SCS:
                retval[sc.power] = self.loss_pts
                if sc.count >= WINNING_SCS:
                    retval[sc.power] = self.soloer_pts
            else:
                retval[sc.power] = self.played_pts + sc.count + rank_pts[i]
            i += 1
        return retval

class GScoringCarnage(GameScoringSystem):
    """
    Position grants a set number of points (7000, 6000, 5000, 4000, 3000, 20000, or 1000),
    with ties splitting those points.
    Eliminated powers just split position points.
    Each power gets 1 point per centre owned at the end, unless there's a solo, in which
    case the soloer gets the 34 SC points.
    """
    # TODO Add support for dead powers scoring based on elimination order
    def __init__(self):
        self.name = _('Carnage with dead equal')
        self.position_pts = [7000, 6000, 5000, 4000, 3000, 2000, 1000]
        self.is_abstract = False

    # TODO There's a lot of overlap with CDiplo here
    def scores(self, centre_counts):
        retval = {}
        final_scs = self._final_year_scs(centre_counts)
        # Tweak the ranking points to allow for ties
        rank_pts = adjust_rank_score(list(final_scs), self.position_pts)
        i = 0
        for sc in final_scs:
            if final_scs[0].count >= WINNING_SCS:
                retval[sc.power] = 0
                if sc.count >= WINNING_SCS:
                    retval[sc.power] = sum(self.position_pts) + TOTAL_SCS
            else:
                retval[sc.power] = sc.count + rank_pts[i]
            i += 1
        return retval

class GScoringSumOfSquares(GameScoringSystem):
    """
    Soloer gets 100 points, everyone else gets zero.
    If there is no solo, square each power's final centre-count and normalize those numbers to
    sum to 100 points.
    """
    def __init__(self):
        self.name = _(u'Sum of Squares')
        self.is_abstract = False

    def scores(self, centre_counts):
        retval = {}
        retval_solo = {}
        solo_found = False
        final_scs = self._final_year_scs(centre_counts)
        sum_of_squares = 0
        for sc in final_scs:
            retval_solo[sc.power] = 0
            retval[sc.power] = sc.count * sc.count * 100.0
            sum_of_squares += sc.count * sc.count
            if sc.count >= WINNING_SCS:
                # Overwrite the previous totals we came up with
                retval_solo[sc.power] = 100.0
                solo_found = True
        if solo_found:
            return retval_solo
        for sc in final_scs:
            retval[sc.power] /= sum_of_squares
        return retval

# All the game scoring systems we support
G_SCORING_SYSTEMS = [
    GScoringSolos(),
    GScoringDrawSize(),
    GScoringCDiplo(_('CDiplo 100'), 100.0, 1.0, 38.0, 14.0, 7.0),
    GScoringCDiplo(_('CDiplo 80'), 80.0, 0.0, 25.0, 14.0, 7.0),
    GScoringSumOfSquares(),
    GScoringCarnage(),
]

