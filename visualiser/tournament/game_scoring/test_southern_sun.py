# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2025 Chris Brand
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


class SouthernSunGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    SOUTHERN_SUN = 'Southern Sun'

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

    def test_g_scoring_southern_sun_no_solo1(self):
        EXPECT = {self.austria: 21,
                  self.england: 30 + 14 * 10 + 80,
                  self.france: 30 + 4 * 10 + 50,
                  self.germany: 30 + 1 * 10 + 30,
                  self.italy: 6,
                  self.russia: 12,
                  self.turkey: 30 + 15 * 10 + 130}
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 14,
                                         self.france: 4,
                                         self.germany: 1,
                                         self.italy: 0,
                                         self.russia: 0,
                                         self.turkey: 15},
                              final_year=1909,
                              elimination_years={self.italy: 1902,
                                                 self.russia: 1904,
                                                 self.austria: 1907})
        check_score_for_state(self, sgs, self.SOUTHERN_SUN, EXPECT)

    def test_g_scoring_southern_sun_no_solo2(self):
        EXPECT = {self.austria: 30 + 12 * 10 + 130,
                  self.england: 30 + 11 * 10 + 80,
                  self.france: 30 + 5 * 10 + round((50 + 30) / 2),
                  self.germany: 30 + 5 * 10 + round((50 + 30) / 2),
                  self.italy: 30 + 1 * 10 + 20,
                  self.russia: 9,
                  self.turkey: 18}
        sgs = SimpleGameState(sc_counts={self.austria: 12,
                                         self.england: 11,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 1,
                                         self.russia: 0,
                                         self.turkey: 0},
                              final_year=1909,
                              elimination_years={self.russia: 1903,
                                                 self.turkey: 1906})
        check_score_for_state(self, sgs, self.SOUTHERN_SUN, EXPECT)

    def test_g_scoring_southern_sun_no_solo3(self):
        EXPECT = {self.austria: 30 + 11 * 10 + 130,
                  self.england: 30 + 10 * 10 + 80,
                  self.france: 30 + 7 * 10 + 50,
                  self.germany: 30 + 3 * 10 + 30,
                  self.italy: 30 + 2 * 10 + 20,
                  self.russia: 30 + 1 * 10 + 10,
                  self.turkey: 12}
        sgs = SimpleGameState(sc_counts={self.austria: 11,
                                         self.england: 10,
                                         self.france: 7,
                                         self.germany: 3,
                                         self.italy: 2,
                                         self.russia: 1,
                                         self.turkey: 0},
                              final_year=1909,
                              elimination_years={self.turkey: 1904})
        check_score_for_state(self, sgs, self.SOUTHERN_SUN, EXPECT)

    def test_g_scoring_southern_sun_no_solo4(self):
        EXPECT = {self.austria: 30 + 10 * 10 + 130,
                  self.england: 30 + 9 * 10 + 80,
                  self.france: 30 + 5 * 10 + round((50 + 30)/2),
                  self.germany: 30 + 5 * 10 + round((50 + 30)/2),
                  self.italy: 30 + 4 * 10 + 20,
                  self.russia: 30 + 1 * 10 + 10,
                  self.turkey: 21}
        sgs = SimpleGameState(sc_counts={self.austria: 10,
                                         self.england: 9,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 1,
                                         self.turkey: 0},
                              final_year=1909,
                              elimination_years={self.turkey: 1907})
        check_score_for_state(self, sgs, self.SOUTHERN_SUN, EXPECT)

    def test_g_scoring_southern_sun_no_solo5(self):
        EXPECT = {self.austria: 30 + 8 * 10 + 130,
                  self.england: 30 + 7 * 10 + 80,
                  self.france: 30 + 6 * 10 + round((50 + 30)/2),
                  self.germany: 30 + 6 * 10 + round((50 + 30)/2),
                  self.italy: 30 + 3 * 10 + round((20 + 10)/2),
                  self.russia: 30 + 3 * 10 + round((20 + 10)/2),
                  self.turkey: 30 + 1 * 10 + 10}
        sgs = SimpleGameState(sc_counts={self.austria: 8,
                                         self.england: 7,
                                         self.france: 6,
                                         self.germany: 6,
                                         self.italy: 3,
                                         self.russia: 3,
                                         self.turkey: 1},
                              final_year=1909,
                              elimination_years={})
        check_score_for_state(self, sgs, self.SOUTHERN_SUN, EXPECT)

    def test_g_scoring_southern_sun_no_solo6(self):
        EXPECT = {self.austria: 30 + 11 * 10 + round((130 + 80 + 50)/3),
                  self.england: 30 + 11 * 10 + round((130 + 80 + 50)/3),
                  self.france: 30 + 11 * 10 + round((130 + 80 + 50)/3),
                  self.germany: 30 + 1 * 10 + 30,
                  self.italy: 12,
                  self.russia: 27,
                  self.turkey: 9}
        sgs = SimpleGameState(sc_counts={self.austria: 11,
                                         self.england: 11,
                                         self.france: 11,
                                         self.germany: 1,
                                         self.italy: 0,
                                         self.russia: 0,
                                         self.turkey: 0},
                              final_year=1909,
                              elimination_years={self.italy: 1904,
                                                 self.russia: 1909,
                                                 self.turkey: 1903})
        check_score_for_state(self, sgs, self.SOUTHERN_SUN, EXPECT)

    def test_g_scoring_southern_sun_no_solo7(self):
        EXPECT = {self.austria: 30 + 17 * 10 + round((130 + 80)/2),
                  self.england: 30 + 17 * 10 + round((130 + 80)/2),
                  self.france: 9,
                  self.germany: 18,
                  self.italy: 12,
                  self.russia: 27,
                  self.turkey: 9}
        sgs = SimpleGameState(sc_counts={self.austria: 17,
                                         self.england: 17,
                                         self.france: 0,
                                         self.germany: 0,
                                         self.italy: 0,
                                         self.russia: 0,
                                         self.turkey: 0},
                              final_year=1909,
                              elimination_years={self.france: 1903,
                                                 self.germany: 1906,
                                                 self.italy: 1904,
                                                 self.russia: 1909,
                                                 self.turkey: 1903})
        check_score_for_state(self, sgs, self.SOUTHERN_SUN, EXPECT)

    def test_g_scoring_southern_sun_solo(self):
        EXPECT = {self.austria: 0,
                  self.england: 0,
                  self.france: 0,
                  self.germany: 500,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey: 0}
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
        check_score_for_state(self, sgs, self.SOUTHERN_SUN, EXPECT)
