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
This module contains scoring systems for individual diplomacy games.
"""
import operator

from abc import ABC, abstractmethod

from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import ugettext as _

from tournament.diplomacy import TOTAL_SCS, WINNING_SCS


def _the_game(centre_counts):
    """Returns the game in question."""
    return centre_counts.first().game


def _final_year(centre_counts):
    """Returns the most recent year we have centre counts for."""
    return centre_counts.order_by('-year')[0].year


def _final_year_scs(centre_counts):
    """
    Returns the CentreCounts for the most recent year only,
    ordered largest-to-smallest.
    """
    return centre_counts.filter(year=_final_year(centre_counts)).order_by('-count')


class GameScoringSystem(ABC):
    # TODO This doesn't deal with multiple players playing one power
    """
    A scoring system for a Game.
    Provides a method to calculate a score for each player of one game.
    """
    name = u''

    @abstractmethod
    def scores(self, centre_counts):
        """
        Takes the set of CentreCount objects for one Game.
        Returns a dict, indexed by power id, of scores.
        """
        raise NotImplementedError

    @property
    def slug(self):
        """Slug for the system"""
        # In theory, two systems could have matching slugs, but the usage means that should never happen
        return slugify(self.name)

    @property
    def description(self):
        """Returns a string describing the scoring system"""
        # By default, use the docstring for the class
        return _(self.__doc__)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('game_scoring_detail', args=(self.slug,))


class GScoringSolos(GameScoringSystem):
    """
    Solos score 100 points.
    Other results score 0.
    """
    def __init__(self):
        self.name = _(u'Solo or bust')

    def scores(self, centre_counts):
        """
        If any power soloed, they get 100 points.
        Otherwise, they get 0.
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        # We only care about the most recent centrecounts
        for sc in _final_year_scs(centre_counts):
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
        self.name = _(u'Draw size')

    def scores(self, centre_counts):
        """
        If any power soloed, they get 100 points.
        Otherwise, if a draw passed, all powers in the draw equally shared 100
        points between them.
        Otherwise, all surviving powers equally share 100 points between them.
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        the_game = _the_game(centre_counts)
        draw = the_game.passed_draw()
        final_scs = _final_year_scs(centre_counts)
        survivors = final_scs.filter(count__gt=0).count()
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


def _adjust_rank_score(centre_counts, rank_points):
    """
    Takes a list of CentreCounts for one year of one game,
    ordered highest-to-lowest, and a list of ranking points for positions,
    ordered from first place to last.
    Returns a list of ranking points for positions, ordered to correspond to
    the centre counts, having made adjustments for any tied positions.
    Where two or more powers have the same number of SCs, the ranking points
    for their positions are shared eveny between them.
    """
    if not rank_points:
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
    for j in range(0, i):
        if j < len(rank_points):
            rank_points[j] = points / count
        else:
            rank_points.append(points / count)
    # And recursively continue
    return rank_points[0:i] + _adjust_rank_score(centre_counts[i:],
                                                 rank_points[i:])


class GScoringCDiplo(GameScoringSystem):
    """
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
                 first_pts, second_pts, third_pts, loss_pts=0):
        self.name = name
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

    def scores(self, centre_counts):
        retval = {}
        final_scs = _final_year_scs(centre_counts)
        # Tweak the ranking points to allow for ties
        rank_pts = _adjust_rank_score(list(final_scs), self.position_pts)
        for i, sc in enumerate(final_scs):
            if final_scs[0].count >= WINNING_SCS:
                retval[sc.power] = self.loss_pts
                if sc.count >= WINNING_SCS:
                    retval[sc.power] = self.soloer_pts
            else:
                retval[sc.power] = self.played_pts + sc.count + rank_pts[i]
        return retval


class _DummySC(object):
    """
    Used by Carnage scoring with elimination ordering.
    Just has power and count attributes.
    """
    def __init__(self, power, count):
        self.power = power
        self.count = count


class GScoringCarnage(GameScoringSystem):
    """
    Position grants a set number of points (7000, 6000, 5000, 4000, 3000,
    2000, or 1000), with ties splitting those points.
    Each power gets 1 point per centre owned at the end, unless there's
    a solo, in which case the soloer gets the 34 SC points.
    Eliminated powers either get position points based on when they were
    eliminated or all split position points.
    """
    def __init__(self, name, dead_equal=True):
        self.name = name
        self.dead_equal = dead_equal
        self.position_pts = [7000, 6000, 5000, 4000, 3000, 2000, 1000]

    @property
    def description(self):
        base = _("""
                 Position grants a set number of points (%(pos_1)d, %(pos_2)d, %(pos_3)d, %(pos_4)d, %(pos_5)d,
                 %(pos_6)d, or %(pos_7)d), with ties splitting those points.
                 Each power gets 1 point per centre owned at the end, unless there's
                 a solo, in which case the soloer gets the 34 SC points.
                 """) % {'pos_1': self.position_pts[0],
                         'pos_2': self.position_pts[1],
                         'pos_3': self.position_pts[2],
                         'pos_4': self.position_pts[3],
                         'pos_5': self.position_pts[4],
                         'pos_6': self.position_pts[5],
                         'pos_7': self.position_pts[6],
                         }
        if self.dead_equal:
            return base + 'Eliminated powers all split position points.'
        else:
            return base + 'Eliminated powers get position points based on when they were eliminated.'


    def scores(self, centre_counts):
        retval = {}
        final_scs = _final_year_scs(centre_counts)

        # Solos are special
        if final_scs[0].count >= WINNING_SCS:
            retval[final_scs[0].power] = sum(self.position_pts) + TOTAL_SCS
            for sc in final_scs[1:]:
                retval[sc.power] = 0
            return retval

        # Giving all the dead powers equal scores is easy
        if self.dead_equal:
            # Tweak the ranking points to allow for ties
            rank_pts = _adjust_rank_score(list(final_scs),
                                          list(self.position_pts))
            for i, sc in enumerate(final_scs):
                retval[sc.power] = sc.count + rank_pts[i]
            return retval

        # Split out the eliminated powers
        live_scs = list(final_scs.exclude(count=0))
        pos_pts = list(self.position_pts)
        pos_pts_1 = pos_pts[:len(live_scs)]
        # Tweak the alive powers points to allow for ties
        rank_pts = _adjust_rank_score(live_scs, pos_pts_1)
        for i, sc in enumerate(live_scs):
            retval[sc.power] = sc.count + rank_pts[i]

        # If nobody was eliminated, we're done
        if len(pos_pts) == len(pos_pts_1):
            return retval

        dead_scs = final_scs.filter(count=0)
        pos_pts_2 = pos_pts[len(pos_pts_1)-len(pos_pts):]
        # Find when the dead powers died
        dummys = []
        for sc in dead_scs:
            p = sc.power
            year = sc.game.centrecount_set.filter(power=p).filter(count=0).order_by('year').first().year
            # For both year and SC count, higher is better
            dummys.append(_DummySC(p, year))
        dummys.sort(key=operator.attrgetter('count'), reverse=True)
        rank_pts = _adjust_rank_score(dummys, pos_pts_2)
        for i, sc in enumerate(dummys):
            retval[sc.power] = rank_pts[i]
        return retval


class GScoringSumOfSquares(GameScoringSystem):
    """
    Soloer gets 100 points, everyone else gets zero.
    If there is no solo, square each power's final centre-count
    and normalize those numbers to sum to 100 points.
    """
    def __init__(self):
        self.name = _(u'Sum of Squares')

    def scores(self, centre_counts):
        retval = {}
        retval_solo = {}
        solo_found = False
        final_scs = _final_year_scs(centre_counts)
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


class GScoringJanus(GameScoringSystem):
    """
    1 point per dot, board leader gets 6 more (split evenly if
    there are multiple board leaders), survivors split 60 points
    equally between them.
    If there's a lone board leader, every other player loses
    a number of their survival points to the leader equal to the
    dot gap between first and second place.
    With a solo, soloer gets 100, everyone else gets 0.
    """
    def __init__(self):
        self.name = _('Janus')

    def scores(self, centre_counts):
        retval = {}
        final_scs = _final_year_scs(centre_counts)
        survivors = final_scs.filter(count__gt=0).count()
        survival_points = 60 / survivors
        leader_scs = final_scs[0].count
        leaders = final_scs.filter(count=leader_scs).count()
        second_scs = final_scs[1].count
        margin = leader_scs - second_scs
        bonus_per_survivor = min(survival_points, margin)
        soloed = leader_scs >= WINNING_SCS
        for sc in final_scs:
            if soloed:
                if sc.count == leader_scs:
                    retval[sc.power] = 100
                else:
                    retval[sc.power] = 0
                continue
            retval[sc.power] = sc.count
            if sc.count == leader_scs:
                retval[sc.power] += 6 / leaders
            if sc.count:
                retval[sc.power] += survival_points
            # Is there a lone leader?
            if margin:
                if sc.power == final_scs[0].power:
                    retval[sc.power] += bonus_per_survivor * (survivors - 1)
                elif sc.count:
                    retval[sc.power] -= bonus_per_survivor
        return retval


class GScoringTribute(GameScoringSystem):
    """
    1 point per dot, survivors split 66 points
    equally between them.
    Each player pays the board leader(s) 1 point for each dot
    the leader has over 6. This payment cannot exceed the survival points.
    With a solo, soloer gets 100, everyone else gets 0.
    """
    def __init__(self):
        self.name = _('Tribute')

    def scores(self, centre_counts):
        retval = {}
        final_scs = _final_year_scs(centre_counts)
        survivors = final_scs.filter(count__gt=0).count()
        survival_points = 66 / survivors
        leader_scs = final_scs[0].count
        leaders = final_scs.filter(count=leader_scs).count()
        if leader_scs > 6:
            bonus_per_survivor = min(survival_points, leader_scs - 6)
        else:
            bonus_per_survivor = 0
        soloed = leader_scs >= WINNING_SCS
        for sc in final_scs:
            if soloed:
                if sc.count == leader_scs:
                    retval[sc.power] = 100
                else:
                    retval[sc.power] = 0
                continue
            # 1 point per dot
            retval[sc.power] = sc.count
            # Plus the survival points
            if sc.count:
                retval[sc.power] += survival_points
            # Leader(s) gets tribute
            if sc.count == leader_scs:
                retval[sc.power] += bonus_per_survivor * (survivors - leaders) / leaders
            # from all the rest
            elif sc.count:
                retval[sc.power] -= bonus_per_survivor
        return retval


class GScoringWorldClassic(GameScoringSystem):
    """
    Solo gets 420. Others get 0.
    Otherwise 10 points per SC, 30 for surviving to the end/draw, 48 pool for board topping.
    1 point for year survived if eliminated by a non-solo.
    """
    def __init__(self):
        self.name = _('World Classic')

    def scores(self, centre_counts):
        retval = {}
        final_scs = _final_year_scs(centre_counts)
        leader_scs = final_scs[0].count
        leaders = final_scs.filter(count=leader_scs).count()
        soloed = leader_scs >= WINNING_SCS
        if soloed:
            solo_year = final_scs[0].year
        for sc in final_scs:
            # 1 point per year survived if eliminated, regardless of the game result
            if sc.count == 0:
                year = sc.game.centrecount_set.filter(power=sc.power).filter(count=0).order_by('year').first().year
                retval[sc.power] = year - 1901
                continue
            # Scoring a soloed game is different
            if soloed:
                if sc.count == leader_scs:
                    retval[sc.power] = 420
                else:
                    # Everyone else does still get survival points up to the solo year
                    retval[sc.power] = solo_year - 1901
                continue
            # 10 points per SC
            retval[sc.power] = 10 * sc.count
            # 30 for surviving
            if sc.count:
                retval[sc.power] += 30
            # 48 split between board toppers
            if sc.count == leader_scs:
                retval[sc.power] += 48 / leaders
        return retval


class GScoringManorCon(GameScoringSystem):
    """
    Solo gets 75. Others get 0.1 per year they survived.
    Otherwise calculate N = S^2 + 4*S + 16 for each power, where S is their centre-count (including N=16 for dead powers).
    Then each surviving power scored 100 * N/(sum of all Ns), and each dead power still scores 0.1 per year they survived.
    """
    def __init__(self):
        self.name = _('ManorCon')

    def scores(self, centre_counts):
        retval = {}
        final_scs = _final_year_scs(centre_counts)
        leader_scs = final_scs[0].count
        leaders = final_scs.filter(count=leader_scs).count()
        soloed = leader_scs >= WINNING_SCS
        if soloed:
            solo_year = final_scs[0].year
        sum_of_n = 0.0
        for sc in final_scs:
            # Scoring a soloed game is different
            if soloed:
                # In this case, "sum of N" is irrelevant, so retval is the actual score
                if sc.count == leader_scs:
                    retval[sc.power] = 75
                # Everyone else does still get survival points up to the solo year or their elimination year
                else:
                    if sc.count == 0:
                        year = sc.game.centrecount_set.filter(power=sc.power).filter(count=0).order_by('year').first().year
                    else:
                        year = solo_year
                    retval[sc.power] = 0.1 * (year - 1901)
            else:
                # 0.1 point per season survived if eliminated, regardless of the game result
                if sc.count == 0:
                    year = sc.game.centrecount_set.filter(power=sc.power).filter(count=0).order_by('year').first().year
                    n = 16
                    # retval gets the actual score
                    retval[sc.power] = 0.1 * (year - 1901)
                else:
                    # Calculate N for the power
                    n = sc.count * sc.count + 4 * sc.count + 16
                    # Retval gets N, which still needs to be divided
                    retval[sc.power] = n
                # And add N for this power to the total
                sum_of_n += n
        if not soloed:
            for sc in final_scs:
                if sc.count > 0:
                    retval[sc.power] *= 100/sum_of_n
        return retval


# All the game scoring systems we support
G_SCORING_SYSTEMS = [
    GScoringSolos(),
    GScoringDrawSize(),
    GScoringCDiplo(_('CDiplo 100'), 100.0, 1.0, 38.0, 14.0, 7.0),
    GScoringCDiplo(_('CDiplo 80'), 80.0, 0.0, 25.0, 14.0, 7.0),
    GScoringSumOfSquares(),
    GScoringCarnage(_('Carnage with dead equal'), True),
    GScoringCarnage(_('Carnage with elimination order'), False),
    GScoringJanus(),
    GScoringTribute(),
    GScoringWorldClassic(),
    GScoringManorCon(),
]
