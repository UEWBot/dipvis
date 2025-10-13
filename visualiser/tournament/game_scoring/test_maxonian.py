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

from django.test import TestCase

from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR, TOTAL_SCS, WINNING_SCS
from tournament.game_scoring.base import DotCountUnknown
from tournament.game_scoring.base import GameState
from tournament.game_scoring.test_general import check_score_order
from tournament.models import find_game_scoring_system


class InvalidState(Exception):
    """The game state is invalid"""
    pass


class SCChartGameState(GameState):
    """
    State of a single Game
    """

    def __init__(self, powers, sc_counts):
        """
        Create a SCChartGameState from a supply centre chart.

        powers should be an iterable representing the Great Powers.
        sc_counts should be a dict, keyed by year, of dicts, keyed by power, of ints.
        """
        # Note that we use a reference to the parameters
        self.powers = powers
        self.sc_counts = sc_counts
        self.final_year = FIRST_YEAR
        # Minimal sanity-check of the parameter
        for year, counts in sc_counts.items():
            if year > self.final_year:
                self.final_year = year
            total = sum(counts.values())
            if total > TOTAL_SCS:
                raise InvalidState(f'(Total SC count in {year} is {total}')

    def all_powers(self):
        return self.powers

    def soloer(self):
        for year, counts in self.sc_counts.items():
            for power, count in counts.items():
                if count >= WINNING_SCS:
                    return power
        return None

    def survivors(self):
        counts = self.sc_counts[self.final_year]
        return [p for p, c in counts.items() if c > 0]

    def powers_in_draw(self):
        return self.survivors()

    def solo_year(self):
        counts = self.sc_counts[self.final_year]
        for power, count in counts.items():
            if count >= WINNING_SCS:
                return self.final_year
        return None

    def num_powers_with(self, centres):
        counts = self.sc_counts[self.final_year]
        return len([c for c in counts.values() if c == centres])

    def highest_dot_count(self):
        counts = self.sc_counts[self.final_year]
        return max(counts.values())

    def dot_count(self, power, year=None):
        if year is None:
            year = self.final_year
        try:
            counts = self.sc_counts[year]
        except KeyError:
            raise DotCountUnknown(f'{power} for year {year}')
        return counts[power]

    def year_eliminated(self, power):
        for year in sorted(self.sc_counts.keys()):
            if self.sc_counts[year][power] == 0:
                return year
        return None

    def elimination_year_list(self):
        retval = []
        counts = self.sc_counts[self.final_year]
        for p in self.powers:
            if counts[p]:
                retval.append[None]
            else:
                retval.append(self.year_eliminated(p))
        return retval

    def last_full_year(self):
        return self.final_year


class MaxonianGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        cls.powers = [cls.austria, cls.england, cls.france, cls.germany, cls.italy, cls.russia, cls.turkey]

        cls.year1901 = {cls.austria: 5,
                        cls.england: 4,
                        cls.france: 5,
                        cls.germany: 5,
                        cls.italy: 4,
                        cls.russia: 5,
                        cls.turkey: 4}
        cls.year1902 = {cls.austria: 4,
                        cls.england: 4,
                        cls.france: 4,
                        cls.germany: 6,
                        cls.italy: 4,
                        cls.russia: 6,
                        cls.turkey: 6}
        # Missing counts for 1903
        cls.year1904 = {cls.austria: 0,
                        cls.england: 5,
                        cls.france: 4,
                        cls.germany: 8,
                        cls.italy: 4,
                        cls.russia: 5,
                        cls.turkey: 8}
        cls.year1905 = {cls.austria: 0,
                        cls.england: 5,
                        cls.france: 3,
                        cls.germany: 13,
                        cls.italy: 3,
                        cls.russia: 4,
                        cls.turkey: 6}
        # Two powers over the bonus threshold
        cls.year1906 = {cls.austria: 0,
                        cls.england: 2,
                        cls.france: 0,
                        cls.germany: 17,
                        cls.italy: 0,
                        cls.russia: 1,
                        cls.turkey: 14}
        # Two powers over the bonus threshold
        cls.year1907 = {cls.austria: 0,
                        cls.england: 1,
                        cls.france: 0,
                        cls.germany: 18,
                        cls.italy: 0,
                        cls.russia: 1,
                        cls.turkey: 14}

    def test_g_scoring_maxonian_no_solo1(self):
        sc_counts = {1901: self.year1901,
                     1902: self.year1902,
                     1904: self.year1904}
        tgs = SCChartGameState(self.powers, sc_counts)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif p == self.england:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                elif p == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif p == self.germany:
                    # 1st
                    self.assertAlmostEqual(s, 7)
                elif p == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif p == self.russia:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                else:
                    # 2nd
                    self.assertAlmostEqual(s, 6)
        check_score_order(self, scores)

    def test_g_scoring_maxonian_no_solo2(self):
        sc_counts = {1901: self.year1901,
                     1902: self.year1902,
                     1904: self.year1904,
                     1905: self.year1905}
        tgs = SCChartGameState(self.powers, sc_counts)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif p == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif p == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif p == self.germany:
                    # 1st
                    self.assertAlmostEqual(s, 7)
                elif p == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif p == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd
                    self.assertAlmostEqual(s, 6)
        check_score_order(self, scores)

    def test_g_scoring_maxonian_no_solo3(self):
        sc_counts = {1901: self.year1901,
                     1902: self.year1902,
                     1904: self.year1904,
                     1905: self.year1905,
                     1906: self.year1906}
        tgs = SCChartGameState(self.powers, sc_counts)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif p == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif p == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif p == self.germany:
                    # 1st, 4 over threshold
                    self.assertAlmostEqual(s, 7+4)
                elif p == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif p == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd, 1 over threshold
                    self.assertAlmostEqual(s, 6+1)
        check_score_order(self, scores)

    def test_g_scoring_7eleven_no_solo3(self):
        sc_counts = {1901: self.year1901,
                     1902: self.year1902,
                     1904: self.year1904,
                     1905: self.year1905,
                     1906: self.year1906}
        tgs = SCChartGameState(self.powers, sc_counts)
        system = find_game_scoring_system('7Eleven')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif p == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif p == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif p == self.germany:
                    # 1st, 6 over threshold
                    self.assertAlmostEqual(s, 7+6)
                elif p == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif p == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd, 3 over threshold
                    self.assertAlmostEqual(s, 6+3)
        check_score_order(self, scores)

    def test_g_scoring_maxonian_solo(self):
        sc_counts = {1901: self.year1901,
                     1902: self.year1902,
                     1904: self.year1904,
                     1905: self.year1905,
                     1906: self.year1906,
                     1907: self.year1907}
        tgs = SCChartGameState(self.powers, sc_counts)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif p == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif p == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif p == self.germany:
                    # 1st, 5 over threshold
                    self.assertAlmostEqual(s, 7+5)
                elif p == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif p == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd
                    self.assertAlmostEqual(s, 6)
        check_score_order(self, scores)

    def test_g_scoring_maxonian_3_equal_top(self):
        sc_counts = {1901: self.year1901,
                     1902: self.year1902}
        tgs = SCChartGameState(self.powers, sc_counts)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if (p == self.austria) or (p == self.france):
                    # Joint 4th
                    self.assertAlmostEqual(s, (4 + 3) / 2)
                elif (p == self.england) or (p == self.italy):
                    # Joint 6th
                    self.assertAlmostEqual(s, (2 + 1) / 2)
                elif (p == self.germany) or (p == self.russia):
                    # Joint 1st
                    self.assertAlmostEqual(s, (7 + 6) / 2)
                else:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
        check_score_order(self, scores)

    def test_g_scoring_maxonian_4_equal_top(self):
        sc_counts = {1901: self.year1901}
        tgs = SCChartGameState(self.powers, sc_counts)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                count = self.year1901[p]
                if count == 5:
                    # Joint 1st
                    self.assertAlmostEqual(s, (7 + 6 + 5 + 4) / 4)
                else:
                    # Joint 5th
                    self.assertAlmostEqual(s, (3 + 2 + 1) / 3)
        check_score_order(self, scores)
