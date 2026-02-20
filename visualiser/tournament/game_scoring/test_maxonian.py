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
from tournament.game_scoring.sc_chart_game_state import SCChartGameState
from tournament.game_scoring.test_general import check_score_for_state


class MaxonianGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    # Scoring systems tested
    MAXONIAN = 'Maxonian'
    SEVEN_ELEVEN = '7Eleven'

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
        EXPECT = {self.austria: 1,
                  self.england: 4,
                  self.france: 3,
                  self.germany: 7,
                  self.italy: 2,
                  self.russia: 5,
                  self.turkey: 6}
        tgs = SCChartGameState(self.powers, sc_counts)
        check_score_for_state(self, tgs, self.MAXONIAN, EXPECT)

    def test_g_scoring_maxonian_no_solo2(self):
        sc_counts = {1901: self.year1901,
                     1902: self.year1902,
                     1904: self.year1904,
                     1905: self.year1905}
        EXPECT = {self.austria: 1,
                  self.england: 5,
                  self.france: 3,
                  self.germany: 7,
                  self.italy: 2,
                  self.russia: 4,
                  self.turkey: 6}
        tgs = SCChartGameState(self.powers, sc_counts)
        check_score_for_state(self, tgs, self.MAXONIAN, EXPECT)

    def test_g_scoring_maxonian_no_solo3(self):
        sc_counts = {1901: self.year1901,
                     1902: self.year1902,
                     1904: self.year1904,
                     1905: self.year1905,
                     1906: self.year1906}
        EXPECT = {self.austria: 1,
                  self.england: 5,
                  self.france: 3,
                  self.germany: 7+4,
                  self.italy: 2,
                  self.russia: 4,
                  self.turkey: 6+1}
        tgs = SCChartGameState(self.powers, sc_counts)
        check_score_for_state(self, tgs, self.MAXONIAN, EXPECT)

    def test_g_scoring_7eleven_no_solo3(self):
        sc_counts = {1901: self.year1901,
                     1902: self.year1902,
                     1904: self.year1904,
                     1905: self.year1905,
                     1906: self.year1906}
        EXPECT = {self.austria: 1,
                  self.england: 5,
                  self.france: 3,
                  self.germany: 7+6,
                  self.italy: 2,
                  self.russia: 4,
                  self.turkey: 6+3}
        tgs = SCChartGameState(self.powers, sc_counts)
        check_score_for_state(self, tgs, self.SEVEN_ELEVEN, EXPECT)

    def test_g_scoring_maxonian_solo(self):
        sc_counts = {1901: self.year1901,
                     1902: self.year1902,
                     1904: self.year1904,
                     1905: self.year1905,
                     1906: self.year1906,
                     1907: self.year1907}
        EXPECT = {self.austria: 1,
                  self.england: 5,
                  self.france: 3,
                  self.germany: 7+5,
                  self.italy: 2,
                  self.russia: 4,
                  self.turkey: 6}
        tgs = SCChartGameState(self.powers, sc_counts)
        check_score_for_state(self, tgs, self.MAXONIAN, EXPECT)

    def test_g_scoring_maxonian_3_equal_top(self):
        sc_counts = {1901: self.year1901,
                     1902: self.year1902}
        EXPECT = {self.austria: (4 + 3) / 2,
                  self.england: (2 + 1) / 2,
                  self.france: (4 + 3) / 2,
                  self.germany: (7 + 6) / 2,
                  self.italy: (2 + 1) / 2,
                  self.russia: (7 + 6) / 2,
                  self.turkey: 5}
        tgs = SCChartGameState(self.powers, sc_counts)
        check_score_for_state(self, tgs, self.MAXONIAN, EXPECT)

    def test_g_scoring_maxonian_4_equal_top(self):
        sc_counts = {1901: self.year1901}
        EXPECT = {self.austria: (7 + 6 + 5 + 4) / 4,
                  self.england: (3 + 2 + 1) / 3,
                  self.france: (7 + 6 + 5 + 4) / 4,
                  self.germany: (7 + 6 + 5 + 4) / 4,
                  self.italy: (3 + 2 + 1) / 3,
                  self.russia: (7 + 6 + 5 + 4) / 4,
                  self.turkey: (3 + 2 + 1) / 3}
        tgs = SCChartGameState(self.powers, sc_counts)
        check_score_for_state(self, tgs, self.MAXONIAN, EXPECT)
