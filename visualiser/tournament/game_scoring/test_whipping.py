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


class WhippingGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    WHIPPING = 'Whipping'

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

    def test_g_scoring_whipping_example_a(self):
        example_a = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 12,
                                               self.france: 3,
                                               self.germany: 6,
                                               self.italy: 9,
                                               self.russia: 0,
                                               self.turkey: 4},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.russia: 1908},
                                    draw=None)
        EXPECT = {self.austria: 4,
                  self.england: 120 + 12 + 24,
                  self.france: 30 + 12,
                  self.germany: 60 + 12,
                  self.italy: 90 + 12,
                  self.russia: 8,
                  self.turkey: 40 + 12}
        check_score_for_state(self, example_a, self.WHIPPING, EXPECT)

    def test_g_scoring_whipping_example_b(self):
        example_b = SimpleGameState(sc_counts={self.austria: 17,
                                               self.england: 0,
                                               self.france: 1,
                                               self.germany: 12,
                                               self.italy: 0,
                                               self.russia: 4,
                                               self.turkey: 0},
                                    final_year=1911,
                                    elimination_years={self.england: 1911,
                                                       self.italy: 1906,
                                                       self.turkey: 1905},
                                    draw=None)
        EXPECT = {self.austria: 170 + 15 + 34,
                  self.england: 11,
                  self.france: 10 + 15,
                  self.germany: 120 + 15,
                  self.italy: 6,
                  self.russia: 40 + 15,
                  self.turkey: 5}
        check_score_for_state(self, example_b, self.WHIPPING, EXPECT)

    def test_g_scoring_whipping_example_c(self):
        example_c = SimpleGameState(sc_counts={self.austria: 18,
                                               self.england: 3,
                                               self.france: 4,
                                               self.germany: 0,
                                               self.italy: 0,
                                               self.russia: 9,
                                               self.turkey: 0},
                                    final_year=1911,
                                    elimination_years={self.germany: 1908,
                                                       self.italy: 1905,
                                                       self.turkey: 1904},
                                    draw=None)
        EXPECT = {self.austria: 340 + 60 + 68,
                  self.england: 11,
                  self.france: 11,
                  self.germany: 8,
                  self.italy: 5,
                  self.russia: 11,
                  self.turkey: 4}
        check_score_for_state(self, example_c, self.WHIPPING, EXPECT)

    def test_g_scoring_whipping_example_d(self):
        example_d = SimpleGameState(sc_counts={self.austria: 4,
                                               self.england: 11,
                                               self.france: 11,
                                               self.germany: 0,
                                               self.italy: 0,
                                               self.russia: 0,
                                               self.turkey: 8},
                                    final_year=1911,
                                    elimination_years={self.germany: 1904,
                                                       self.italy: 1907,
                                                       self.russia: 1906},
                                    draw=None)
        EXPECT = {self.austria: 40 + 15,
                  self.england: 110 + 15 + 0,
                  self.france: 110 + 15 + 0,
                  self.germany: 4,
                  self.italy: 7,
                  self.russia: 6,
                  self.turkey: 80 + 15}
        check_score_for_state(self, example_d, self.WHIPPING, EXPECT)
