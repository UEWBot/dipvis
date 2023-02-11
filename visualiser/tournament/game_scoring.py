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
from abc import ABC, abstractmethod
from math import floor
from operator import itemgetter

from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _

from tournament.diplomacy.values.diplomacy_values import TOTAL_SCS, WINNING_SCS, FIRST_YEAR


class InvalidYear(Exception):
    """The specified year is invalid for the GameState."""
    pass


class DotCountUnknown(Exception):
    """The dot count for the specified year is unknown."""
    pass


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
    def dot_count(self, power, year=None):
        """
        Returns the number of supply centres owned by the specified power.
        If year is specified, returns the numer of centres owned at the end
        of that year. Otherwise, returns the latest number.
        May raise InvaidYear or DotCountUnknown if year is provided.
        """
        raise NotImplementedError

    @abstractmethod
    def year_eliminated(self, power):
        """Returns the year in which the specified power was eliminated, or None."""
        raise NotImplementedError

    @abstractmethod
    def last_full_year(self):
        """
        Returns the year that the SC counts are for.
        As SC ownerships change after Fall retreats, this will be the previous year
        if currently playing spring or fall, and the current year if currently doing
        adjustments.
        """
        raise NotImplementedError


class GameScoringSystem(ABC):
    # TODO This doesn't deal with multiple players playing one power
    """
    A scoring system for a Game.
    Provides a method to calculate a score for each player of one game.
    """
    MAX_NAME_LENGTH = 40
    name = u''
    """
    Returns False if a power's score is fixed at elimination,
    True if their score may still change.
    """
    dead_score_can_change = False

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


def _normalise_scores(scores, total=100.0):
    """
    Adjusts all the scores to sum to total while keeping the same ratios.
    scores should be a dict, indexed by power, of raw scores.
    """
    old_total = sum(scores.values())
    for p in scores.keys():
        scores[p] = scores[p] * total / old_total


def _adjust_rank_score(centre_counts, rank_points):
    """
    Takes a list of (power, centre count) 2-tuples for one year of one game,
    ordered highest-to-lowest, and a list of ranking points for positions,
    ordered from first place to last.
    Returns a list of ranking points for positions, ordered to correspond to
    the centre counts, having made adjustments for any tied positions.
    Where two or more powers have the same number of SCs, the ranking points
    for their positions are shared evenly between them.
    """
    if not rank_points:
        # The rest of them get zero points
        return [] + [0.0] * len(centre_counts)
    # Work with a copy of rank_points
    rank_pts = rank_points.copy()
    # First count up how many powers tied at the top
    i = 0
    count = 0
    points = 0
    scs = centre_counts[0][1]
    while (i < len(centre_counts)) and (centre_counts[i][1] == scs):
        count += 1
        if i < len(rank_pts):
            points += rank_pts[i]
        i += 1
    # Now share the points between those tied players
    for j in range(0, i):
        if j < len(rank_pts):
            rank_pts[j] = points / count
        else:
            rank_pts.append(points / count)
    # And recursively continue
    return rank_pts[0:i] + _adjust_rank_score(centre_counts[i:],
                                              rank_pts[i:])


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
            retval[p] = 0.0
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


class GScoringWhipping(GameScoringSystem):
    """
    If there is a solo:
    - Soloers score a set number of points (soloer_pts).
    - Survivors who lose to a solo score as if they were eliminated when the solo occurred.
    Otherwise:
    - Eliminated powers get one point per year played.
    - Everyone gets ten points per centre owned.
    - Surviving powers share 60 points equally between them.
    - The power with the most centres gets a bonus of twice the number of SCs owned.
    - If multiple powers are tied for board top, no board topping bonus is awarded.
    """
    def __init__(self, name, soloer_pts):
        self.soloer_pts = soloer_pts
        self.name = name

    @property
    def description(self):
        return _("""
                 If there is a solo:
                 - Soloers score %(soloer_pts)d.
                 - Survivors who lose to a solo score as if they were eliminated when the solo occurred.
                 Otherwise:
                 - Eliminated powers get one point per year played.
                 - Everyone gets ten points per centre owned.
                 - Surviving powers share 60 points equally between them.
                 - The power with the most centres gets a bonus of twice the number of SCs owned.
                 - If multiple powers are tied for board top, no board topping bonus is awarded.
                 """) % {'soloer_pts': self.soloer_pts}

    def scores(self, state):
        retval = {}
        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        dots.sort(key = itemgetter(1), reverse=True)
        topper_scs = dots[0][1]
        for i, (p, c) in enumerate(dots):
            if topper_scs >= WINNING_SCS:
                if c >= WINNING_SCS:
                    retval[p] = self.soloer_pts
                elif c > 0:
                    retval[p] = state.solo_year() - (FIRST_YEAR - 1)
                else:
                    retval[p] = state.year_eliminated(p) - (FIRST_YEAR - 1)
            else:
                if c == 0:
                    retval[p] = state.year_eliminated(p) - (FIRST_YEAR - 1)
                else:
                    retval[p] = (10 * c) + (60 / len(state.survivors()))
                    if c == topper_scs:
                        if state.num_powers_with(topper_scs) == 1:
                            retval[p] += topper_scs * 2
        return retval


class GScoringCarnage(GameScoringSystem):
    """
    Position grants a set number of points, with ties splitting those points.
    Each power gets some set points per centre owned at the end, unless there's
    a solo, in which case the soloer gets all the SC points.
    Eliminated powers either get position points based on when they were
    eliminated or all split position points.
    In the centre-based version, losers to a solo also get some points.
    """
    def __init__(self, name, centre_based, dead_equal):
        self.name = name
        self.dead_score_can_change = True
        self.dead_equal = dead_equal
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
        base = _("""
                 If any power soloed, they get %(solo_pts)d points and all others get %(loss_pts)d.
                 Otherwise, all powers score %(dot_pts)d point per centre owned at the end plus
                 points for their final position.
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
            return retval

        # Split out the eliminated powers
        live_scs = [(p, c) for (p, c) in dots if c > 0]
        pos_pts_1 = self.position_pts[:len(live_scs)]
        # Tweak the alive powers points to allow for ties
        rank_pts = _adjust_rank_score(live_scs, pos_pts_1)
        for i, (p, c) in enumerate(live_scs):
            retval[p] = self.points_per_dot * c + rank_pts[i]

        # If nobody was eliminated, we're done
        if len(self.position_pts) == len(pos_pts_1):
            return retval

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
        all_powers = state.all_powers()
        for p in all_powers:
            retval_solo[p] = 0.0
            dots = state.dot_count(p)
            retval[p] = dots * dots
            if p == soloer:
                retval_solo[p] = 100.0
        if soloer is not None:
            return retval_solo
        _normalise_scores(retval)
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

class GScoringOpenTribute(GameScoringSystem):
    """
    Base score of 34 plus 3 points per dot.
    Each player pays the board leader(s) 1 point for each dot
    the leader has more than them.
    Eliminated players lose all remaining points, scoring zero.
    If the board top is shared by N players, each gets 1/(N^2) of the total tribute, rounded down.
    With a solo, soloer gets 340, everyone else gets 0.
    """
    def __init__(self):
        self.name = _('OpenTribute')

    def scores(self, state):
        retval = {}
        num_survivors = len(state.survivors())
        leader_scs = state.highest_dot_count()
        num_leaders = state.num_powers_with(leader_scs)
        soloer = state.soloer()
        soloed = soloer is not None
        tribute = 0
        for p in state.all_powers():
            if soloed:
                if p == soloer:
                    retval[p] = 340
                else:
                    retval[p] = 0
                continue
            dots = state.dot_count(p)
            if dots:
                # Start with 34
                retval[p] = 34
                # 3 points per dot
                retval[p] += 3 * dots
                # pay the tribute
                t = leader_scs - dots
                retval[p] -= t
                tribute += t
            else:
                retval[p] = 0
                # pay the tribute
                tribute += leader_scs
        if not soloed:
            # Leader(s) gets tribute
            for p in state.all_powers():
                dots = state.dot_count(p)
                if dots == leader_scs:
                    retval[p] += floor(tribute / (num_leaders * num_leaders))
        return retval

class GScoringOMG(GameScoringSystem):
    """
    a) Each supply center (SC) is worth 1.5 points (total = 51 points)
    b) Surviving in a draw is worth 9 points (average = 40.5 points per game)
    c) Bonuses for the Top 3: 4.5 points for 1st, 3 points for 2nd, 1.5 points for 3rd.
       If positions are tied, position points are shared between powers
       (e.g. a 2-way tie for second awards each player (3 + 1.5) / 2 = 2.25 points.
    d) Tribute paid to the board topper is equal to 1st place SCs - 2nd place SCs,
       capped at 50% of a players score from a, b, and c
    e) a solo victory is worth 100 points, with others scoring zero.
    """
    def __init__(self):
        self.name = _('OMG')

    def scores(self, state):
        retval = {}
        dots = [(p, state.dot_count(p)) for p in state.all_powers()]
        dots.sort(key = itemgetter(1), reverse=True)
        gap = dots[0][1] - dots[1][1]
        num_leaders = state.num_powers_with(dots[0][1])
        rank_pts = _adjust_rank_score(dots, [4.5, 3, 1.5])
        soloer = state.soloer()
        soloed = soloer is not None
        tribute = 0
        for i, (p, c) in enumerate(dots):
            if soloed:
                if p == soloer:
                    retval[p] = 100
                else:
                    retval[p] = 0
                continue
            # 1.5 point per dot
            retval[p] = 1.5 * c
            # Plus the survival points
            if c:
                retval[p] += 9
            # and position points
            retval[p] += rank_pts[i]
            if num_leaders == 1:
                # Leader(s) gets tribute from all the rest
                x = min(gap, retval[p]/2)
                retval[p] -= x
                tribute += x
        # Tribute goes to the leader
        retval[dots[0][0]] += tribute
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
                if p == soloer:
                    retval[p] = 420
                else:
                    # Everyone else does still get survival points up to the solo year
                    retval[p] = solo_year - FIRST_YEAR
                continue
            # 10 points per SC
            retval[p] = 10 * dots
            # 30 for surviving
            retval[p] += 30
            # 48 split between board toppers
            if dots == leader_scs:
                retval[p] += 48 / num_leaders
        return retval


class GScoringDetour09(GameScoringSystem):
    """
    Soloer gets 110.
    Otherwise, players get 1 per centre held, plus 2 points if they hold any centres,
    If there's a single board topper, that player get points equal to the difference between their
    centre count and that of the player(s) immediately behind them.
    Leader gets 4 points, 2nd gets 3, 3rd gets 2 and 4th gets 1. If players are tied for
    position, they all get the lower position points.
    Finally, scores for a game without a solo are normalised to be out of 100.
    Eliminated players and those who lose to a solo get 0.25 points per year of survival,
    to a maximum of 2 points. A year of survival is when the player has at least 1 centre during
    winter and no other player has 18 or more.
    """
    def __init__(self):
        self.name = _('Detour09')

    def scores(self, state):
        retval = {}
        soloer = state.soloer()
        soloed = soloer is not None
        all_powers = state.all_powers()
        leader_scs = state.highest_dot_count()
        # Scoring a soloed game is different
        if soloed:
            for p in all_powers:
                if p == soloer:
                    retval[p] = 110
                else:
                    retval[p] = 0
        else:
            # Do a first pass to allocate the easy points
            for p in all_powers:
                dots = state.dot_count(p)
                retval[p] = dots
                if dots > 0:
                    retval[p] += 2
            # Figure out which power is in which position
            top_powers = sorted(retval, key=retval.get, reverse=True)
            second = top_powers[1]
            # Now do a second pass to allocate position-based points
            for p in all_powers:
                if state.dot_count(p) == leader_scs:
                    # Add gap to second-place power
                    retval[p] += leader_scs - state.dot_count(second)
            # 1st place gets another 4, 2nd 3, 3rd 2 and 4th 1,
            # with ties getting the lower position points
            i = 0
            bonus = 4
            while (bonus > 0) and (i < 4):
                p = top_powers[i]
                dots = state.dot_count(p)
                if state.num_powers_with(dots) == 1:
                    retval[p] += bonus
                elif state.num_powers_with(dots) == 2:
                    bonus -= 1
                    if bonus > 0:
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                elif state.num_powers_with(dots)  == 3:
                    bonus -= 2
                    if bonus > 0:
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                elif state.num_powers_with(dots)  == 4:
                    bonus -= 3
                    if bonus > 0:
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                        i += 1
                        p = top_powers[i]
                        retval[p] += bonus
                else:
                    # No bonus at all
                    break
                i += 1
                bonus -= 1
            _normalise_scores(retval)
        # Survival points for eliminated players and losers to a solo
        if soloed:
            solo_year = state.solo_year()
        for p in all_powers:
            if state.dot_count(p) == 0:
                year = state.year_eliminated(p)
            elif soloed and (p != soloer):
                year = solo_year
            else:
                # No survival points
                continue
            years = year - FIRST_YEAR
            if years > 8:
                years = 8
            retval[p] += 0.25 * years
        return retval


class GScoringBangkok(GameScoringSystem):
    """
    In a draw,
      Everyone gets 1 point per centre.
      12 points is divided between dominating players:
        3 shares to topping players
        2 shares to players 1 centre from the top
        1 share to players 2 centres from the top
        points = 12 * (player's shares) / sum of all shares
      3 points to all surviving players
      0.3 points per year survived for elimnated players
    In a solo:
      Soloer gets 41 points
      Everyone else gets 0.5 points per centre
    """
    def __init__(self):
        self.name = _('Bangkok')
        self.dead_score_can_change = True

    def scores(self, state):
        retval = {}
        all_powers = state.all_powers()
        soloer = state.soloer()
        soloed = soloer is not None
        if soloed:
            for p in all_powers:
                dots = state.dot_count(p)
                if p == soloer:
                    retval[p] = 41
                else:
                    retval[p] = 0.5 * dots
        else:
            shares = {}
            leader_scs = state.highest_dot_count()
            for p in all_powers:
                dots = state.dot_count(p)
                retval[p] = dots
                # Store shares for domination bonus
                if dots == leader_scs:
                    shares[p] = 3
                elif dots == leader_scs - 1:
                    shares[p] = 2
                elif dots == leader_scs - 2:
                    shares[p] = 1
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


class GScoringMaxonian(GameScoringSystem):
    """
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
        self.position_points = [7, 6, 5, 4, 3, 2, 1]
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

    def _num_equal(self, state, dots, power_list, year):
        """
        How many of the specified powers had the specified dot count in the specified year?
        """
        count = 0
        for p in power_list:
            if state.dot_count(p, year) == dots:
                count += 1
        return count

    def _scores_for_powers(self, state, year, power_list, points_list):
        """
        Recursive function to calculate position points.
        points_list must be ordered highest to lowest
        """
        retval = {}
        if year < FIRST_YEAR:
            # Powers are completely tied
            pts = sum(points_list) / len(power_list)
            for p in power_list:
                retval[p] = pts
            return retval

        dots = [(p, state.dot_count(p, year)) for p in power_list]
        dots.sort(key = itemgetter(1), reverse=True)

        for n, (p, d) in enumerate(dots, start=0):

            # We may already have done this power (if it's tied)
            if p in retval:
                continue

            count = self._num_equal(state, d, power_list, year)
            if count == 1:
                retval[p] = points_list[n]
            else:
                # Recurse with the appropriate subsets
                power_sublist = [p for p, d2 in dots if d2 == d]
                yr = year - 1
                while(True):
                    try:
                        retval.update(self._scores_for_powers(state,
                                                              yr,
                                                              power_sublist,
                                                              points_list[n:n+count]))
                        break
                    except DotCountUnknown:
                        # Try the previous year
                        # We always have 1900 counts,
                        # and if for some reason we don't,
                        # we'll get InvalidYear instead
                        yr = yr - 1

        return retval

    def scores(self, state):
        # Get position points for each power
        retval = self._scores_for_powers(state,
                                         state.last_full_year(),
                                         state.all_powers(),
                                         self.position_points)
        soloer = state.soloer()

        # add bonus points
        for p in retval.keys():
            d = state.dot_count(p)
            if d > self.bonus_threshold:
                if (soloer is None) or (soloer == p):
                    # All solos score as if they had 18 dots
                    d = min(d, WINNING_SCS)
                    retval[p] += d - self.bonus_threshold

        return retval


class GScoringManorCon(GameScoringSystem):
    """
    Solo gets a set number of points. Others get 0.1 per year they survived.
    Otherwise calculate N = S^2 + 4*S + 16 for each power, where S is their centre-count (optionally including N=16 for dead powers).
    Then each surviving power scored 100 * N/(sum of all Ns), and each dead power still scores 0.1 per year they survived.
    """
    def __init__(self, name, solo_score=75, dead_get_16=True):
        self.solo_score = solo_score
        self.dead_get_16 = dead_get_16
        self.name = name

    @property
    def description(self):
        if self.dead_get_16:
            dead_sum_str = ' (including N=16 for dead powers)'
        else:
            dead_sum_str = ''
        return _("""
                 Solo gets %(solo_score)d. Others get 0.1 per year they survived.
                 Otherwise calculate N = S^2 + 4*S + 16 for each power,
                 where S is their centre-count%(dead_sum_str)s.
                 Then each surviving power scored 100 * N/(sum of all Ns),
                 and each dead power still scores 0.1 per year they survived.
                 """) % {'solo_score': self.solo_score,
                         'dead_sum_str': dead_sum_str}

    def scores(self, state):
        retval = {}
        leader_scs = state.highest_dot_count()
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
                if p == soloer:
                    retval[p] = self.solo_score
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
                    if self.dead_get_16:
                        n = 16
                    else:
                        n = 0
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
    GScoringBangkok(),
    GScoringCarnage(_('Carnage with dead equal'), centre_based=False, dead_equal=True),
    GScoringCarnage(_('Carnage with elimination order'), centre_based=False, dead_equal=False),
    GScoringCarnage(_('Center-count Carnage'), centre_based=True, dead_equal=False),
    GScoringCDiplo(_('CDiplo 100'), 100.0, 1.0, 38.0, 14.0, 7.0),
    GScoringCDiplo(_('CDiplo 80'), 80.0, 0.0, 25.0, 14.0, 7.0),
    GScoringDetour09(),
    GScoringDrawSize(),
    GScoringManorCon(_('ManorCon'), 75, True),
    GScoringManorCon(_('Original ManorCon'), 100, True),
    GScoringManorCon(_('ManorCon v2'), 100, False),
    GScoringMaxonian(_('Maxonian'), 13),
    GScoringMaxonian(_('7Eleven'), 11),
    GScoringOMG(),
    GScoringSolos(),
    GScoringSumOfSquares(),
    GScoringTribute(),
    GScoringOpenTribute(),
    GScoringWhipping(_('Whipping'), 468),
    GScoringWorldClassic(),
]
