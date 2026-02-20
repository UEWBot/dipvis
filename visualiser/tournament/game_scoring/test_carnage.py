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
from tournament.diplomacy.values.diplomacy_values import TOTAL_SCS
from tournament.game_scoring.simple_game_state import SimpleGameState
from tournament.game_scoring.test_general import check_score_for_state


class CarnageGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    # Scoring systems tested
    CARNAGE_DEAD_EQUAL = 'Carnage with dead equal'
    CARNAGE_ELIM_ORDER = 'Carnage with elimination order'
    CARNAGE_2023 = 'Carnage 2023'
    CENTER_COUNT_CARNAGE = 'Center-count Carnage'

    # For most Carnage scoring, the sum of all scores is known
    EXPECTED_TOTAL = 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS

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

    # GScoringCarnage (with dead equal)
    def test_g_scoring_carnage1_simple(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        EXPECT = {self.austria: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.england: (3000 + 2000 + 1000) / 3 + 4,
                  self.france: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.germany: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.italy: (3000 + 2000 + 1000) / 3 + 4,
                  self.russia: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.turkey: (3000 + 2000 + 1000) / 3 + 4}
        # 2 SCs are still neutral
        check_score_for_state(self, sgs, self.CARNAGE_DEAD_EQUAL, EXPECT, self.EXPECTED_TOTAL - 2)

    def test_g_scoring_carnage1_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 4,
                                         self.france: 0,
                                         self.germany: 18,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 7},
                              final_year=1907,
                              elimination_years={self.austria: 1904,
                                                 self.france: 1906,
                                                 self.italy: 1906})
        EXPECT = {self.austria: 0,
                  self.england: 0,
                  self.france: 0,
                  self.germany: self.EXPECTED_TOTAL,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey: 0}
        check_score_for_state(self, sgs, self.CARNAGE_DEAD_EQUAL, EXPECT, self.EXPECTED_TOTAL)

    def test_g_scoring_carnage1_eliminations(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 0,
                                         self.germany: 17,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 7},
                              final_year=1906,
                              elimination_years={self.austria: 1904,
                                                 self.france: 1906,
                                                 self.italy: 1906})
        EXPECT = {self.austria: (3000 + 2000 + 1000) / 3 + 0,
                  self.england: (5000 + 4000) / 2 + 5,
                  self.france: (3000 + 2000 + 1000) / 3 + 0,
                  self.germany: 7000 + 17,
                  self.italy: (3000 + 2000 + 1000) / 3 + 0,
                  self.russia: (5000 + 4000) / 2 + 5,
                  self.turkey: 6000 + 7}
        check_score_for_state(self, sgs, self.CARNAGE_DEAD_EQUAL, EXPECT, self.EXPECTED_TOTAL)

    # Carnage with elimination order
    def test_g_scoring_carnage2_simple(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        EXPECT = {self.austria: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.england: (3000 + 2000 + 1000) / 3 + 4,
                  self.france: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.germany: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.italy: (3000 + 2000 + 1000) / 3 + 4,
                  self.russia: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.turkey: (3000 + 2000 + 1000) / 3 + 4}
        # 2 SCs are still neutral
        check_score_for_state(self, sgs, self.CARNAGE_ELIM_ORDER, EXPECT, self.EXPECTED_TOTAL - 2)

    def test_g_scoring_carnage2_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 4,
                                         self.france: 0,
                                         self.germany: 18,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 7},
                              final_year=1907,
                              elimination_years={self.austria: 1904,
                                                 self.france: 1906,
                                                 self.italy: 1906})
        EXPECT = {self.austria: 0,
                  self.england: 0,
                  self.france: 0,
                  self.germany: self.EXPECTED_TOTAL,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey: 0}
        check_score_for_state(self, sgs, self.CARNAGE_ELIM_ORDER, EXPECT, self.EXPECTED_TOTAL)

    def test_g_scoring_carnage2_eliminations(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 0,
                                         self.germany: 17,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 7},
                              final_year=1906,
                              elimination_years={self.austria: 1904,
                                                 self.france: 1906,
                                                 self.italy: 1906})
        EXPECT = {self.austria: 1000 + 0,
                  self.england: (5000 + 4000) / 2 + 5,
                  self.france: (3000 + 2000) / 2 + 0,
                  self.germany: 7000 + 17,
                  self.italy: (3000 + 2000) / 2 + 0,
                  self.russia: (5000 + 4000) / 2 + 5,
                  self.turkey: 6000 + 7}
        check_score_for_state(self, sgs, self.CARNAGE_ELIM_ORDER, EXPECT, self.EXPECTED_TOTAL)

    # Carnage 2023 (elimination order and leader gap bonus)
    def test_g_scoring_carnage2023_simple(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        EXPECT = {self.austria: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.england: (3000 + 2000 + 1000) / 3 + 4,
                  self.france: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.germany: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.italy: (3000 + 2000 + 1000) / 3 + 4,
                  self.russia: (7000 + 6000 + 5000 + 4000) / 4 + 5,
                  self.turkey: (3000 + 2000 + 1000) / 3 + 4}
        check_score_for_state(self, sgs, self.CARNAGE_2023, EXPECT, self.EXPECTED_TOTAL - 2)

    def test_g_scoring_carnage2023_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 4,
                                         self.france: 0,
                                         self.germany: 18,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 7},
                              final_year=1907,
                              elimination_years={self.austria: 1904,
                                                 self.france: 1906,
                                                 self.italy: 1906})
        EXPECT = {self.austria: 0,
                  self.england: 0,
                  self.france: 0,
                  self.germany: self.EXPECTED_TOTAL,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey: 0}
        check_score_for_state(self, sgs, self.CARNAGE_2023, EXPECT, self.EXPECTED_TOTAL)

    def test_g_scoring_carnage2023_eliminations(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 0,
                                         self.germany: 17,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 7},
                              final_year=1906,
                              elimination_years={self.austria: 1904,
                                                 self.france: 1906,
                                                 self.italy: 1906})
        EXPECT = {self.austria: 1000 + 0,
                  self.england: (5000 + 4000) / 2 + 5,
                  self.france: (3000 + 2000) / 2 + 0,
                  # Bonus 300 points per dot ahead of second place
                  self.germany: 7000 + 17 + (17 - 7) * 300,
                  self.italy: (3000 + 2000) / 2 + 0,
                  self.russia: (5000 + 4000) / 2 + 5,
                  self.turkey: 6000 + 7}
        check_score_for_state(self, sgs, self.CARNAGE_2023, EXPECT)

    # GScoringCentreCarnage
    def test_g_scoring_centrecarnage_1(self):
        # There used to be an "example 1" and "example 2" in the doc, but no more :-(
        example_1 = SimpleGameState(sc_counts={self.austria: 11,
                                               self.england: 10,
                                               self.france: 8,
                                               self.germany: 2,
                                               self.italy: 2,
                                               self.russia: 1,
                                               self.turkey: 0},
                                    final_year=1908,
                                    elimination_years={self.turkey: 1904},
                                    draw=None)
        EXPECT = {self.austria: 11 * 500 + 7007,
                  self.england: 10 * 500 + 6006,
                  self.france: 8 * 500 + 5005,
                  self.germany: 2 * 500 + (4004 + 3003) / 2,
                  self.italy: 2 * 500 + (4004 + 3003) / 2,
                  self.russia: 1 * 500 + 2002,
                  self.turkey: 1001}
        check_score_for_state(self, example_1, self.CENTER_COUNT_CARNAGE, EXPECT)

    def test_g_scoring_centrecarnage_2(self):
        # There used to be an "example 1" and "example 2" in the doc, but no more :-(
        example_2 = SimpleGameState(sc_counts={self.austria: 13,
                                               self.england: 7,
                                               self.france: 5,
                                               self.germany: 5,
                                               self.italy: 4,
                                               self.russia: 0,
                                               self.turkey: 0},
                                    final_year=1908,
                                    elimination_years={self.russia: 1905,
                                                       self.turkey: 1904},
                                    draw=None)
        EXPECT = {self.austria: 13 * 500 + 7007,
                  self.england: 7 * 500 + 6006,
                  self.france: 5 * 500 + (5005 + 4004) / 2,
                  self.germany: 5 * 500 + (5005 + 4004) / 2,
                  self.italy: 4 * 500 + 3003,
                  self.russia: 2002,
                  self.turkey: 1001}
        check_score_for_state(self, example_2, self.CENTER_COUNT_CARNAGE, EXPECT)
