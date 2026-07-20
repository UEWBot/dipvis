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

from tournament.diplomacy import GreatPower

from .simple_game_state import SimpleGameState
from .test_general import check_score_for_state


class DuctTapeV2GameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    # Scoring systems tested
    DUCT_TAPE_DEAD_EQUAL = 'Duct Tape V2'
    DUCT_TAPE_ELIM_ORDER = 'Duct Tape V2 (elimination order)'

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

    # Duct Tape V2 (with dead equal)
    def test_g_scoring_duct_tape_v2_simple(self):
        # No ties, no eliminations
        sgs = SimpleGameState(sc_counts={self.austria: 7,
                                         self.england: 6,
                                         self.france: 5,
                                         self.germany: 4,
                                         self.italy: 3,
                                         self.russia: 2,
                                         self.turkey: 1},
                              final_year=1901,
                              elimination_years={})
        EXPECT = {self.austria: 40 + 7,
                  self.england: 24 + 6,
                  self.france: 15 + 5,
                  self.germany: 9 + 4,
                  self.italy: 6 + 3,
                  self.russia: 3 + 2,
                  self.turkey: 3 + 1}
        check_score_for_state(self, sgs, self.DUCT_TAPE_DEAD_EQUAL, EXPECT, sum(EXPECT.values()))

    def test_g_scoring_duct_tape_v2_ties(self):
        # A 3-way tie for the lead and a 4-way tie for last, no eliminations
        sgs = SimpleGameState(sc_counts={self.austria: 1,
                                         self.england: 10,
                                         self.france: 1,
                                         self.germany: 1,
                                         self.italy: 10,
                                         self.russia: 10,
                                         self.turkey: 1},
                              final_year=1907,
                              elimination_years={})
        EXPECT = {self.austria: (9 + 6 + 3 + 3) / 4 + 1,
                  self.england: (40 + 24 + 15) / 3 + 10,
                  self.france: (9 + 6 + 3 + 3) / 4 + 1,
                  self.germany: (9 + 6 + 3 + 3) / 4 + 1,
                  self.italy: (40 + 24 + 15) / 3 + 10,
                  self.russia: (40 + 24 + 15) / 3 + 10,
                  self.turkey: (9 + 6 + 3 + 3) / 4 + 1}
        check_score_for_state(self, sgs, self.DUCT_TAPE_DEAD_EQUAL, EXPECT, sum(EXPECT.values()))

    def test_g_scoring_duct_tape_v2_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 18,
                                         self.france: 0,
                                         self.germany: 5,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 6},
                              final_year=1907,
                              elimination_years={self.austria: 1903,
                                                 self.france: 1905,
                                                 self.italy: 1906})
        EXPECT = {self.austria: 0,
                  self.england: 75,
                  self.france: 0,
                  self.germany: 0,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey: 0}
        check_score_for_state(self, sgs, self.DUCT_TAPE_DEAD_EQUAL, EXPECT, 75)

    def test_g_scoring_duct_tape_v2_eliminations(self):
        # Eliminated powers all tie and split their position points equally,
        # regardless of when they were eliminated
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 17,
                                         self.france: 0,
                                         self.germany: 0,
                                         self.italy: 16,
                                         self.russia: 1,
                                         self.turkey: 0},
                              final_year=1907,
                              elimination_years={self.austria: 1903,
                                                 self.france: 1907,
                                                 self.germany: 1905,
                                                 self.turkey: 1905})
        EXPECT = {self.austria: (9 + 6 + 3 + 3) / 4,
                  self.england: 40 + 17,
                  self.france: (9 + 6 + 3 + 3) / 4,
                  self.germany: (9 + 6 + 3 + 3) / 4,
                  self.italy: 24 + 16,
                  self.russia: 15 + 1,
                  self.turkey: (9 + 6 + 3 + 3) / 4}
        check_score_for_state(self, sgs, self.DUCT_TAPE_DEAD_EQUAL, EXPECT, sum(EXPECT.values()))

    # Duct Tape V2 (with elimination order)
    def test_g_scoring_duct_tape_v2_elim_order_simple(self):
        # No ties, no eliminations - same result as with dead equal
        sgs = SimpleGameState(sc_counts={self.austria: 7,
                                         self.england: 6,
                                         self.france: 5,
                                         self.germany: 4,
                                         self.italy: 3,
                                         self.russia: 2,
                                         self.turkey: 1},
                              final_year=1901,
                              elimination_years={})
        EXPECT = {self.austria: 40 + 7,
                  self.england: 24 + 6,
                  self.france: 15 + 5,
                  self.germany: 9 + 4,
                  self.italy: 6 + 3,
                  self.russia: 3 + 2,
                  self.turkey: 3 + 1}
        check_score_for_state(self, sgs, self.DUCT_TAPE_ELIM_ORDER, EXPECT, sum(EXPECT.values()))

    def test_g_scoring_duct_tape_v2_elim_order_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 18,
                                         self.france: 0,
                                         self.germany: 5,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 6},
                              final_year=1907,
                              elimination_years={self.austria: 1903,
                                                 self.france: 1905,
                                                 self.italy: 1906})
        EXPECT = {self.austria: 0,
                  self.england: 75,
                  self.france: 0,
                  self.germany: 0,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey: 0}
        check_score_for_state(self, sgs, self.DUCT_TAPE_ELIM_ORDER, EXPECT, 75)

    def test_g_scoring_duct_tape_v2_elim_order_eliminations(self):
        # Eliminated powers have ties broken by elimination year, with those
        # eliminated later scoring higher. Germany and Turkey were both
        # eliminated in 1905 and so still tie with each other.
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 17,
                                         self.france: 0,
                                         self.germany: 0,
                                         self.italy: 16,
                                         self.russia: 1,
                                         self.turkey: 0},
                              final_year=1907,
                              elimination_years={self.austria: 1903,
                                                 self.france: 1907,
                                                 self.germany: 1905,
                                                 self.turkey: 1905})
        EXPECT = {self.austria: 3,
                  self.england: 40 + 17,
                  self.france: 9,
                  self.germany: (6 + 3) / 2,
                  self.italy: 24 + 16,
                  self.russia: 15 + 1,
                  self.turkey: (6 + 3) / 2}
        check_score_for_state(self, sgs, self.DUCT_TAPE_ELIM_ORDER, EXPECT, sum(EXPECT.values()))
