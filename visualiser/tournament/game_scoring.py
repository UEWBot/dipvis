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
from operator import itemgetter

from abc import ABC, abstractmethod

from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import ugettext as _

from tournament.diplomacy import TOTAL_SCS, WINNING_SCS, FIRST_YEAR


class GameState(ABC):
    """
    The state of a Game to be scored.
    Encapsulates all the information needed to calculate a score for each power.
    """

    @abstractmethod
    def all_powers(self):
        """Returns an iterable of all the powers."""
        raise NotImplementedError

    @abstractmethod
    def soloer(self):
        """Returns the power that soloed the game or was conceded to, or None."""
        raise NotImplementedError

    @abstractmethod
    def survivors(self):
        """
        Returns an iterable of the subset of powers that are still alive.
        """
        raise NotImplementedError

    @abstractmethod
    def powers_in_draw(self):
        """
        Returns an iterable of all the powers that are included in a draw.
        For a concession, return an iterable containing just the power conceded to.
        If there is no passed draw vote or concession, returns survivors().
        """
        raise NotImplementedError

    @abstractmethod
    def solo_year(self):
        """Returns the year in which a solo occurred, or None."""
        raise NotImplementedError

    @abstractmethod
    def num_powers_with(self, centres):
        """returns the number of powers that own the specified number of supply centres."""
        raise NotImplementedError

    @abstractmethod
    def highest_dot_count(self):
        """Returns the number of supply centres owned by the strongest power(s)."""
        raise NotImplementedError

    @abstractmethod
    def dot_count(self, power):
        """Returns the number of supply centres owned by the specified power."""
        raise NotImplementedError

    @abstractmethod
    def year_eliminated(self, power):
        """Returns the year in which the specified power was eliminated, or None."""
        raise NotImplementedError


class GameScoringSystem(ABC):
    # TODO This doesn't deal with multiple players playing one power
    """
    A scoring system for a Game.
    Provides a method to calculate a score for each player of one game.
    """
    MAX_NAME_LENGTH = 40
    name = u''

    @abstractmethod
    def scores(self, state):
        """
        Takes a GameState object.
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

    def scores(self, state):
        """
        If any power soloed, they get 100 points.
        Otherwise, they get 0.
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        for p in state.all_powers():
            retval[p] = 0
            if state.soloer() == p:
                retval[p] = 100.0
        return retval


class GScoringDrawSize(GameScoringSystem):
    """
    Solos score 100 points.
    Draw sharers split 100 points between them.
    """
    def __init__(self):
        self.name = _(u'Draw size')

    def scores(self, state):
        """
        If any power soloed, they get 100 points.
        Otherwise, if a draw passed, all powers in the draw equally shared 100
        points between them.
        Otherwise, all surviving powers equally share 100 points between them.
        Return a dict, indexed by power id, of scores.
        """
        retval = {}
        survivors = state.powers_in_draw()
        soloed = state.soloer() is not None
        for p in state.all_powers():
            retval[p] = 0.0
            if p == state.soloer():
                retval[p] = 100.0
            elif soloed:
                # Leave the score at zero
                pass
            elif p in survivors:
                retval[p] = 100.0 / len(survivors)
            # This leaves dead powers, or those excluded from a draw, with zero
        return retval


def _adjust_rank_score(centre_counts, rank_points):
    """
    Takes a list of (power, centre count) 2-tuples for one year of one game,
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
    scs = centre_counts[0][1]
    while (i < len(centre_counts)) and (centre_counts[i][1] == scs):
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

    def scores(self, state):
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
        return retval


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
        self.solo_pts = sum(self.position_pts) + TOTAL_SCS

    @property
    def description(self):
        base = _("""
                 If any power soloed, they get %(solo_pts)d points and all others get zero.
                 Otherwise, all powers score 1 point per centre owned at the end plus
                 points for their final position.
                 Position points are %(pos_1)d, %(pos_2)d, %(pos_3)d, %(pos_4)d, %(pos_5)d,
                 %(pos_6)d, or %(pos_7)d, with ties splitting those points.
                 """) % {'solo_pts': self.solo_pts,
                         'pos_1': self.position_pts[0],
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


    def scores(self, state):
        retval = {}

        # Solos are special
        soloer = state.soloer()
        if soloer is not None:
            for p in state.all_powers():
                if p == soloer:
                    retval[p] = self.solo_pts
                else:
                    retval[p] = 0
            return retval

        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        dots.sort(key = itemgetter(1), reverse=True)

        # Giving all the dead powers equal scores is easy
        if self.dead_equal:
            # Tweak the ranking points to allow for ties
            rank_pts = _adjust_rank_score(dots, list(self.position_pts))
            for i, (p, c) in enumerate(dots):
                retval[p] = c + rank_pts[i]
            return retval

        # Split out the eliminated powers
        live_scs = [(p, c) for (p, c) in dots if c > 0]
        pos_pts = list(self.position_pts)
        pos_pts_1 = pos_pts[:len(live_scs)]
        # Tweak the alive powers points to allow for ties
        rank_pts = _adjust_rank_score(live_scs, pos_pts_1)
        for i, (p, c) in enumerate(live_scs):
            retval[p] = c + rank_pts[i]

        # If nobody was eliminated, we're done
        if len(pos_pts) == len(pos_pts_1):
            return retval

        dead_scs = [(p, c) for (p, c) in dots if c == 0]
        pos_pts_2 = pos_pts[len(pos_pts_1)-len(pos_pts):]
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
        return retval


class GScoringSumOfSquares(GameScoringSystem):
    """
    Soloer gets 100 points, everyone else gets zero.
    If there is no solo, square each power's final centre-count
    and normalize those numbers to sum to 100 points.
    """
    def __init__(self):
        self.name = _(u'Sum of Squares')

    def scores(self, state):
        retval = {}
        retval_solo = {}
        soloer = state.soloer()
        sum_of_squares = 0
        all_powers = state.all_powers()
        for p in all_powers:
            retval_solo[p] = 0
            dots = state.dot_count(p)
            retval[p] = dots * dots * 100.0
            sum_of_squares += dots * dots
            if p == soloer:
                retval_solo[p] = 100.0
        if soloer is not None:
            return retval_solo
        # Now that we have sum_of_squares, we can divide each score by it
        for p in all_powers:
            retval[p] /= sum_of_squares
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

    def scores(self, state):
        retval = {}
        num_survivors = len(state.survivors())
        survival_points = 60 / num_survivors
        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        dots.sort(key = itemgetter(1), reverse=True)
        leader_scs = dots[0][1]
        second_scs = dots[1][1]
        margin = leader_scs - second_scs
        bonus_per_survivor = min(survival_points, margin)
        num_leaders = len([c for (p, c) in dots if c == leader_scs])
        soloer = state.soloer()
        soloed = soloer is not None
        for p, c in dots:
            if soloed:
                if p == soloer:
                    retval[p] = 100
                else:
                    retval[p] = 0
                continue
            retval[p] = c
            if c == leader_scs:
                retval[p] += 6 / num_leaders
            if c:
                retval[p] += survival_points
            # Is there a lone leader?
            if margin:
                if p == dots[0][0]:
                    retval[p] += bonus_per_survivor * (num_survivors - 1)
                elif c:
                    retval[p] -= bonus_per_survivor
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

    def scores(self, state):
        retval = {}
        num_survivors = len(state.survivors())
        survival_points = 66 / num_survivors
        leader_scs = state.highest_dot_count()
        num_leaders = state.num_powers_with(leader_scs)
        if leader_scs > 6:
            bonus_per_survivor = min(survival_points, leader_scs - 6)
        else:
            bonus_per_survivor = 0
        soloer = state.soloer()
        soloed = soloer is not None
        for p in state.all_powers():
            if soloed:
                if p == soloer:
                    retval[p] = 100
                else:
                    retval[p] = 0
                continue
            # 1 point per dot
            dots = state.dot_count(p)
            retval[p] = dots
            # Plus the survival points
            if dots:
                retval[p] += survival_points
            # Leader(s) gets tribute
            if dots == leader_scs:
                retval[p] += bonus_per_survivor * (num_survivors - num_leaders) / num_leaders
            # from all the rest
            elif dots:
                retval[p] -= bonus_per_survivor
        return retval


class GScoringWorldClassic(GameScoringSystem):
    """
    Solo gets 420. Others get 0.
    Otherwise 10 points per SC, 30 for surviving to the end/draw, 48 pool for board topping.
    1 point for year survived if eliminated by a non-solo.
    """
    def __init__(self):
        self.name = _('World Classic')

    def scores(self, state):
        retval = {}
        leader_scs = state.highest_dot_count()
        num_leaders = state.num_powers_with(leader_scs)
        soloer = state.soloer()
        soloed = soloer is not None
        if soloed:
            solo_year = state.solo_year()
        for p in state.all_powers():
            dots = state.dot_count(p)
            # 1 point per year survived if eliminated, regardless of the game result
            if dots == 0:
                retval[p] = state.year_eliminated(p) - FIRST_YEAR
                continue
            # Scoring a soloed game is different
            if soloed:
                if dots == leader_scs:
                    retval[p] = 420
                else:
                    # Everyone else does still get survival points up to the solo year
                    retval[p] = solo_year - FIRST_YEAR
                continue
            # 10 points per SC
            retval[p] = 10 * dots
            # 30 for surviving
            if dots:
                retval[p] += 30
            # 48 split between board toppers
            if dots == leader_scs:
                retval[p] += 48 / num_leaders
        return retval


class GScoringManorCon(GameScoringSystem):
    """
    Solo gets 75. Others get 0.1 per year they survived.
    Otherwise calculate N = S^2 + 4*S + 16 for each power, where S is their centre-count (including N=16 for dead powers).
    Then each surviving power scored 100 * N/(sum of all Ns), and each dead power still scores 0.1 per year they survived.
    """
    def __init__(self):
        self.name = _('ManorCon')

    def scores(self, state):
        retval = {}
        leader_scs = state.highest_dot_count()
        #num_leaders = state.num_powers_with(leader_scs)
        soloer = state.soloer()
        soloed = soloer is not None
        if soloed:
            solo_year = state.solo_year()
        sum_of_n = 0.0
        all_powers = state.all_powers()
        for p in all_powers:
            dots = state.dot_count(p)
            # Scoring a soloed game is different
            if soloed:
                # In this case, "sum of N" is irrelevant, so retval is the actual score
                if dots == leader_scs:
                    retval[p] = 75
                # Everyone else does still get survival points up to the solo year or their elimination year
                else:
                    if dots == 0:
                        year = state.year_eliminated(p)
                    else:
                        year = solo_year
                    retval[p] = 0.1 * (year - FIRST_YEAR)
            else:
                # 0.1 point per season survived if eliminated, regardless of the game result
                if dots == 0:
                    year = state.year_eliminated(p)
                    n = 16
                    # retval gets the actual score
                    retval[p] = 0.1 * (year - FIRST_YEAR)
                else:
                    # Calculate N for the power
                    n = dots * dots + 4 * dots + 16
                    # Retval gets N, which still needs to be divided
                    retval[p] = n
                # And add N for this power to the total
                sum_of_n += n
        if not soloed:
            for p in all_powers:
                if state.dot_count(p) > 0:
                    retval[p] *= 100 / sum_of_n
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
