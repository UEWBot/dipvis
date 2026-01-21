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
from tournament.game_scoring.test_general import check_score_for_state
from tournament.game_scoring.simple_game_state import SimpleGameState


class ManorConGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    # Scoring systems tested
    MANORCON = 'ManorCon'
    ORIGINAL_MANORCON = 'Original ManorCon'
    MANORCON_V2 = 'ManorCon v2'

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

    def test_g_scoring_manorcon_no_solo1(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 4,
                                         self.germany: 8,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 8},
                              final_year=1904,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0.3,
                  self.england: 100 * 61 / 458,
                  self.france: 100 * 48 / 458,
                  self.germany: 100 * 112 / 458,
                  self.italy: 100 * 48 / 458,
                  self.russia: 100 * 61 / 458,
                  self.turkey: 100 * 112 / 458}
        check_score_for_state(self, sgs, self.MANORCON, EXPECT)

    def test_g_scoring_manorcon_no_solo2(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 3,
                                         self.germany: 13,
                                         self.italy: 3,
                                         self.russia: 4,
                                         self.turkey: 6},
                              final_year=1905,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0.3,
                  self.england: 100 * 61 / 512,
                  self.france: 100 * 37 / 512,
                  self.germany: 100 * 237 / 512,
                  self.italy: 100 * 37 / 512,
                  self.russia: 100 * 48 / 512,
                  self.turkey: 100 * 76 / 512}
        check_score_for_state(self, sgs, self.MANORCON, EXPECT)

    def test_g_scoring_manorcon_no_solo3(self):
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
        EXPECT = {self.austria: 0.3,
                  self.england: 100 * 61 / 636,
                  self.france: 0.5,
                  self.germany: 100 * 373 / 636,
                  self.italy: 0.5,
                  self.russia: 100 * 61 / 636,
                  self.turkey: 100 * 93 / 636}
        check_score_for_state(self, sgs, self.MANORCON, EXPECT)

    def test_g_scoring_manorcon_solo(self):
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
        EXPECT = {self.austria: 0.3,
                  self.england: 0.6,
                  self.france: 0.5,
                  self.germany: 75,
                  self.italy: 0.5,
                  self.russia: 0.6,
                  self.turkey: 0.6}
        check_score_for_state(self, sgs, self.MANORCON, EXPECT)

    def test_g_scoring_manorcon2_no_solo1(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 4,
                                         self.germany: 8,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 8},
                              final_year=1904,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0.3,
                  self.england: 100 * 61 / 458,
                  self.france: 100 * 48 / 458,
                  self.germany: 100 * 112 / 458,
                  self.italy: 100 * 48 / 458,
                  self.russia: 100 * 61 / 458,
                  self.turkey: 100 * 112 / 458}
        check_score_for_state(self, sgs, self.ORIGINAL_MANORCON, EXPECT)

    def test_g_scoring_manorcon2_no_solo2(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 3,
                                         self.germany: 13,
                                         self.italy: 3,
                                         self.russia: 4,
                                         self.turkey: 6},
                              final_year=1905,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0.3,
                  self.england: 100 * 61 / 512,
                  self.france: 100 * 37 / 512,
                  self.germany: 100 * 237 / 512,
                  self.italy: 100 * 37 / 512,
                  self.russia: 100 * 48 / 512,
                  self.turkey: 100 * 76 / 512}
        check_score_for_state(self, sgs, self.ORIGINAL_MANORCON, EXPECT)

    def test_g_scoring_manorcon2_no_solo3(self):
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
        EXPECT = {self.austria: 0.3,
                  self.england: 100 * 61 / 636,
                  self.france: 0.5,
                  self.germany: 100 * 373 / 636,
                  self.italy: 0.5,
                  self.russia: 100 * 61 / 636,
                  self.turkey: 100 * 93 / 636}
        check_score_for_state(self, sgs, self.ORIGINAL_MANORCON, EXPECT)

    def test_g_scoring_manorcon2_solo(self):
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
        EXPECT = {self.austria: 0.3,
                  self.england: 0.6,
                  self.france: 0.5,
                  self.germany: 100,
                  self.italy: 0.5,
                  self.russia: 0.6,
                  self.turkey: 0.6}
        check_score_for_state(self, sgs, self.ORIGINAL_MANORCON, EXPECT)

    def test_g_scoring_manorconv2_no_solo1(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 4,
                                         self.germany: 8,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 8},
                              final_year=1904,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0.3,
                  self.england: 100 * 61 / 442,
                  self.france: 100 * 48 / 442,
                  self.germany: 100 * 112 / 442,
                  self.italy: 100 * 48 / 442,
                  self.russia: 100 * 61 / 442,
                  self.turkey: 100 * 112 / 442}
        check_score_for_state(self, sgs, self.MANORCON_V2, EXPECT)

    def test_g_scoring_manorconv2_no_solo2(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 3,
                                         self.germany: 13,
                                         self.italy: 3,
                                         self.russia: 4,
                                         self.turkey: 6},
                              final_year=1905,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0.3,
                  self.england: 100 * 61 / 496,
                  self.france: 100 * 37 / 496,
                  self.germany: 100 * 237 / 496,
                  self.italy: 100 * 37 / 496,
                  self.russia: 100 * 48 / 496,
                  self.turkey: 100 * 76 / 496}
        check_score_for_state(self, sgs, self.MANORCON_V2, EXPECT)

    def test_g_scoring_manorconv2_no_solo3(self):
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
        EXPECT = {self.austria: 0.3,
                  self.england: 100 * 61 / 588,
                  self.france: 0.5,
                  self.germany: 100 * 373 / 588,
                  self.italy: 0.5,
                  self.russia: 100 * 61 / 588,
                  self.turkey: 100 * 93 / 588}
        check_score_for_state(self, sgs, self.MANORCON_V2, EXPECT)

    def test_g_scoring_manorconv2_solo(self):
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
        EXPECT = {self.austria: 0.3,
                  self.england: 0.6,
                  self.france: 0.5,
                  self.germany: 100,
                  self.italy: 0.5,
                  self.russia: 0.6,
                  self.turkey: 0.6}
        check_score_for_state(self, sgs, self.MANORCON_V2, EXPECT)
