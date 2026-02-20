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


class WorldClassicGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    # Scoring systems tested
    WORLD_CLASSIC = 'World Classic'
    SUMMER_CLASSIC = 'Summer Classic'

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

    def test_g_scoring_world_classic_no_solo1(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 4,
                                         self.germany: 8,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 8},
                              final_year=1904,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 3,
                  self.england: 30 + 10 * 5,
                  self.france: 30 + 10 * 4,
                  self.germany: 30 + 10 * 8 + 48/2,
                  self.italy: 30 + 10 * 4,
                  self.russia: 30 + 10 * 5,
                  self.turkey: 30 + 10 * 8 + 48/2}
        check_score_for_state(self, sgs, self.WORLD_CLASSIC, EXPECT)

    def test_g_scoring_world_classic_no_solo2(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 3,
                                         self.germany: 13,
                                         self.italy: 3,
                                         self.russia: 4,
                                         self.turkey: 6},
                              final_year=1905,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 3,
                  self.england: 30 + 10 * 5,
                  self.france: 30 + 10 * 3,
                  self.germany: 30 + 10 * 13 + 48,
                  self.italy: 30 + 10 * 3,
                  self.russia: 30 + 10 * 4,
                  self.turkey: 30 + 10 * 6}
        check_score_for_state(self, sgs, self.WORLD_CLASSIC, EXPECT)

    def test_g_scoring_world_classic_no_solo3(self):
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
        EXPECT = {self.austria: 3,
                  self.england: 30 + 10 * 5,
                  self.france: 5,
                  self.germany: 30 + 10 * 17 + 48,
                  self.italy: 5,
                  self.russia: 30 + 10 * 5,
                  self.turkey: 30 + 10 * 7}
        check_score_for_state(self, sgs, self.WORLD_CLASSIC, EXPECT)

    def test_g_scoring_world_classic_3way(self):
        sgs = SimpleGameState(sc_counts={self.austria: 4,
                                         self.england: 4,
                                         self.france: 4,
                                         self.germany: 6,
                                         self.italy: 4,
                                         self.russia: 6,
                                         self.turkey: 6},
                              final_year=1902,
                              elimination_years={})
        EXPECT = {self.austria: 30 + 10 * 4,
                  self.england: 30 + 10 * 4,
                  self.france: 30 + 10 * 4,
                  self.germany: 30 + 10 * 6 + 48/3,
                  self.italy: 30 + 10 * 4,
                  self.russia: 30 + 10 * 6 + 48/3,
                  self.turkey: 30 + 10 * 6 + 48/3}
        check_score_for_state(self, sgs, self.WORLD_CLASSIC, EXPECT)

    def test_g_scoring_summer_classic_3way(self):
        sgs = SimpleGameState(sc_counts={self.austria: 4,
                                         self.england: 4,
                                         self.france: 4,
                                         self.germany: 6,
                                         self.italy: 4,
                                         self.russia: 6,
                                         self.turkey: 6},
                              final_year=1902,
                              elimination_years={})
        EXPECT = {self.austria: 30 + 10 * 4,
                  self.england: 30 + 10 * 4,
                  self.france: 30 + 10 * 4,
                  self.germany: 30 + 10 * 6,
                  self.italy: 30 + 10 * 4,
                  self.russia: 30 + 10 * 6,
                  self.turkey: 30 + 10 * 6}
        check_score_for_state(self, sgs, self.SUMMER_CLASSIC, EXPECT)

    def test_g_scoring_world_classic_solo(self):
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
        EXPECT = {self.austria: 3,
                  self.england: 6,
                  self.france: 5,
                  self.germany: 420,
                  self.italy: 5,
                  self.russia: 6,
                  self.turkey: 6}
        check_score_for_state(self, sgs, self.WORLD_CLASSIC, EXPECT)
