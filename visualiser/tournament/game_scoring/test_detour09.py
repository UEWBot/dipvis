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
from tournament.game_scoring.simple_game_state import SimpleGameState
from tournament.game_scoring.test_general import check_score_for_state


class Detour09GameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    DETOUR_09 = 'Detour09'

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

    def test_g_scoring_detour09_no_solo1(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 4,
                                         self.germany: 8,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 8},
                              final_year=1904,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0.75,
                  self.england: 100 * 8 / (6+6+8+8+13+13),
                  self.france: 100 * 6 / (6+6+8+8+13+13),
                  self.germany: 100 * 13 / (6+6+8+8+13+13),
                  self.italy: 100 * 6 / (6+6+8+8+13+13),
                  self.russia: 100 * 8 / (6+6+8+8+13+13),
                  self.turkey: 100 * 13 / (6+6+8+8+13+13)}
        check_score_for_state(self, sgs, self.DETOUR_09, EXPECT)

    def test_g_scoring_detour09_no_solo2(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 3,
                                         self.germany: 13,
                                         self.italy: 3,
                                         self.russia: 4,
                                         self.turkey: 6},
                              final_year=1905,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0.75,
                  self.england: 100 * 9 / (5+5+7+9+11+26),
                  self.france: 100 * 5 / (5+5+7+9+11+26),
                  self.germany: 100 * 26 / (5+5+7+9+11+26),
                  self.italy: 100 * 5 / (5+5+7+9+11+26),
                  self.russia: 100 * 7 / (5+5+7+9+11+26),
                  self.turkey: 100 * 11 / (5+5+7+9+11+26)}
        check_score_for_state(self, sgs, self.DETOUR_09, EXPECT)

    def test_g_scoring_detour09_no_solo3(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 0,
                                         self.germany: 17,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 7},
                              final_year=1909,
                              elimination_years={self.austria: 1904,
                                                 self.france: 1909,
                                                 self.italy: 1909})
        EXPECT = {self.austria: 0.75,
                  self.england: 100 * 8 / (8+8+12+33),
                  self.france: 2.0,
                  self.germany: 100 * 33 / (8+8+12+33),
                  self.italy: 2.0,
                  self.russia: 100 * 8 / (8+8+12+33),
                  self.turkey: 100 * 12 / (8+8+12+33)}
        check_score_for_state(self, sgs, self.DETOUR_09, EXPECT)

    def test_g_scoring_detour09_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 4,
                                         self.france: 0,
                                         self.germany: 18,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 7},
                              final_year=1910,
                              elimination_years={self.austria: 1904,
                                                 self.france: 1909,
                                                 self.italy: 1909})
        # Suvival bonus is capped at 2.0
        EXPECT = {self.austria: 0.75,
                  self.england: 2.00,
                  self.france: 2.00,
                  self.germany: 110,
                  self.italy: 2.00,
                  self.russia: 2.00,
                  self.turkey: 2.00}
        check_score_for_state(self, sgs, self.DETOUR_09, EXPECT)

    def test_g_scoring_detour09_3_equal_top(self):
        sgs = SimpleGameState(sc_counts={self.austria: 4,
                                         self.england: 4,
                                         self.france: 4,
                                         self.germany: 6,
                                         self.italy: 4,
                                         self.russia: 6,
                                         self.turkey: 6},
                              final_year=1902,
                              elimination_years={})
        # 4+2+0+0=6
        # 6+2+0+2=10
        EXPECT = {self.austria: 100 * 6 / (6+6+6+6+10+10+10),
                  self.england: 100 * 6 / (6+6+6+6+10+10+10),
                  self.france: 100 * 6 / (6+6+6+6+10+10+10),
                  self.germany: 100 * 10 / (6+6+6+6+10+10+10),
                  self.italy: 100 * 6 / (6+6+6+6+10+10+10),
                  self.russia: 100 * 10 / (6+6+6+6+10+10+10),
                  self.turkey: 100 * 10 / (6+6+6+6+10+10+10)}
        check_score_for_state(self, sgs, self.DETOUR_09, EXPECT)

    def test_g_scoring_detour09_4_equal_top(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        # 4+2+0+0=6
        # 5+2+0+1=8
        EXPECT = {self.austria: 100 * 8 / (6+6+6+8+8+8+8),
                  self.england: 100 * 6 / (6+6+6+8+8+8+8),
                  self.france: 100 * 8 / (6+6+6+8+8+8+8),
                  self.germany: 100 * 8 / (6+6+6+8+8+8+8),
                  self.italy: 100 * 6 / (6+6+6+8+8+8+8),
                  self.russia: 100 * 8 / (6+6+6+8+8+8+8),
                  self.turkey: 100 * 6 / (6+6+6+8+8+8+8)}
        check_score_for_state(self, sgs, self.DETOUR_09, EXPECT)

    def test_g_scoring_detour09_2_equal_below_top(self):
        sgs = SimpleGameState(sc_counts={self.austria: 2,
                                         self.england: 3,
                                         self.france: 4,
                                         self.germany: 10,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 6},
                              final_year=1907,
                              elimination_years={})
        # 10+2+4+4=20
        # 6+2+3=11
        # 5+2+2=9
        # 4+2=6
        # 3+2=5
        # 2+2=4
        EXPECT = {self.austria: 100 * 4 / (20+11+9+6+6+5+4),
                  self.england: 100 * 5 / (20+11+9+6+6+5+4),
                  self.france: 100 * 6 / (20+11+9+6+6+5+4),
                  self.germany: 100 * 20 / (20+11+9+6+6+5+4),
                  self.italy: 100 * 6 / (20+11+9+6+6+5+4),
                  self.russia: 100 * 9 / (20+11+9+6+6+5+4),
                  self.turkey: 100 * 11 / (20+11+9+6+6+5+4)}
        check_score_for_state(self, sgs, self.DETOUR_09, EXPECT)

    def test_g_scoring_detour09_3_equal_below_top(self):
        sgs = SimpleGameState(sc_counts={self.austria: 2,
                                         self.england: 3,
                                         self.france: 4,
                                         self.germany: 10,
                                         self.italy: 4,
                                         self.russia: 4,
                                         self.turkey: 7},
                              final_year=1907,
                              elimination_years={})
        # 10+2+3+4=19
        # 7+2+3=12
        # 4+2=6
        # 3+2=5
        # 2+2=4
        EXPECT = {self.austria: 100 * 4 / (19+12+6+6+6+5+4),
                  self.england: 100 * 5 / (19+12+6+6+6+5+4),
                  self.france: 100 * 6 / (19+12+6+6+6+5+4),
                  self.germany: 100 * 19 / (19+12+6+6+6+5+4),
                  self.italy: 100 * 6 / (19+12+6+6+6+5+4),
                  self.russia: 100 * 6 / (19+12+6+6+6+5+4),
                  self.turkey: 100 * 12 / (19+12+6+6+6+5+4)}
        check_score_for_state(self, sgs, self.DETOUR_09, EXPECT)
