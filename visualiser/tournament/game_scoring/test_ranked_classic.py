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


class RankedClassicGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    RANKED_CLASSIC = 'Ranked Classic'

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

    def test_g_scoring_rankedclassic_no_solo1(self):
        example_a = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 10,
                                               self.france: 9,
                                               self.germany: 8,
                                               self.italy: 5,
                                               self.russia: 0,
                                               self.turkey: 2},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.russia: 1908},
                                    draw=None)
        EXPECT = {self.austria: 3,
                  self.england: 30 + 10 * 10 + 200,
                  self.france: 30 + 9 * 10 + 90,
                  self.germany: 30 + 8 * 10 + 60,
                  self.italy: 30 + 5 * 10 + 40,
                  self.russia: 7,
                  self.turkey: 30 + 2 * 10 + 30}
        check_score_for_state(self, example_a, self.RANKED_CLASSIC, EXPECT)

    def test_g_scoring_rankedclassic_no_solo2(self):
        example_b = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 17,
                                               self.france: 0,
                                               self.germany: 10,
                                               self.italy: 4,
                                               self.russia: 0,
                                               self.turkey: 3},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        EXPECT = {self.austria: 3,
                  self.england: 30 + 17 * 10 + 200,
                  self.france: 7,
                  self.germany: 30 + 10 * 10 + 90,
                  self.italy: 30 + 4 * 10 + 60,
                  self.russia: 7,
                  self.turkey: 30 + 3 * 10 + 40}
        check_score_for_state(self, example_b, self.RANKED_CLASSIC, EXPECT)

    def test_g_scoring_rankedclassic_no_solo3(self):
        example_c = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 11,
                                               self.france: 0,
                                               self.germany: 11,
                                               self.italy: 11,
                                               self.russia: 0,
                                               self.turkey: 1},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        EXPECT = {self.austria: 3,
                  self.england: 30 + 11 * 10 + 60,
                  self.france: 7,
                  self.germany: 30 + 11 * 10 + 60,
                  self.italy: 30 + 11 * 10 + 60,
                  self.russia: 7,
                  self.turkey: 30 + 1 * 10 + 40}
        check_score_for_state(self, example_c, self.RANKED_CLASSIC, EXPECT)

    def test_g_scoring_rankedclassic_no_solo4(self):
        example_d = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 12,
                                               self.france: 0,
                                               self.germany: 11,
                                               self.italy: 11,
                                               self.russia: 0,
                                               self.turkey: 0},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1907,
                                                       self.turkey: 1907},
                                    draw=None)
        EXPECT = {self.austria: 3,
                  self.england: 30 + 12 * 10 + 200,
                  self.france: 7,
                  self.germany: 30 + 11 * 10 + 70,
                  self.italy: 30 + 11 * 10 + 70,
                  self.russia: 6,
                  self.turkey: 6}
        check_score_for_state(self, example_d, self.RANKED_CLASSIC, EXPECT)

    def test_g_scoring_rankedclassic_no_solo5(self):
        example_e = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 12,
                                               self.france: 0,
                                               self.germany: 10,
                                               self.italy: 10,
                                               self.russia: 0,
                                               self.turkey: 2},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        EXPECT = {self.austria: 3,
                  self.england: 30 + 12 * 10 + 200,
                  self.france: 7,
                  self.germany: 30 + 10 * 10 + 70,
                  self.italy: 30 + 10 * 10 + 70,
                  self.russia: 7,
                  self.turkey: 30 + 2 * 10 + 40}
        check_score_for_state(self, example_e, self.RANKED_CLASSIC, EXPECT)

    def test_g_scoring_rankedclassic_solo(self):
        example_f = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 18,
                                               self.france: 0,
                                               self.germany: 10,
                                               self.italy: 4,
                                               self.russia: 0,
                                               self.turkey: 2},
                                    final_year=1911,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        EXPECT = {self.austria: 3,
                  self.england: 550,
                  self.france: 7,
                  self.germany: 10,
                  self.italy: 10,
                  self.russia: 7,
                  self.turkey: 10}
        check_score_for_state(self, example_f, self.RANKED_CLASSIC, EXPECT)
