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


class TributeGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    TRIBUTE = 'Tribute'

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

    def test_g_scoring_tribute_no_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        EXPECT = {self.austria: 66 / 7 + 5,
                  self.england: 66 / 7 + 4,
                  self.france: 66 / 7 + 5,
                  self.germany: 66 / 7 + 5,
                  self.italy: 66 / 7 + 4,
                  self.russia: 66 / 7 + 5,
                  self.turkey: 66 / 7 + 4}
        # Total of all scores should be 100 minus 2 (neutrals)
        check_score_for_state(self, sgs, self.TRIBUTE, EXPECT, 98)

    def test_g_scoring_tribute_tied_top(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 4,
                                         self.germany: 8,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 8},
                              final_year=1904,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0,
                  self.england: 5 + 66/6 - 2,
                  self.france: 4 + 66/6 - 2,
                  self.germany: 8 + 66/6 + 2 * 4 / 2,
                  self.italy: 4 + 66/6 - 2,
                  self.russia: 5 + 66/6 - 2,
                  self.turkey: 8 + 66/6 + 2 * 4 / 2}
        # Total of all scores should be 100
        check_score_for_state(self, sgs, self.TRIBUTE, EXPECT, 100)

    def test_g_scoring_tribute_no_solo_2(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 3,
                                         self.germany: 13,
                                         self.italy: 3,
                                         self.russia: 4,
                                         self.turkey: 6},
                              final_year=1905,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0,
                  self.england: 5 + 66/6 - 7,
                  self.france: 3 + 66/6 - 7,
                  self.germany: 13 + 66/6 + 7 * 5,
                  self.italy: 3 + 66/6 - 7,
                  self.russia: 4 + 66/6 - 7,
                  self.turkey: 6 + 66/6 - 7}
        # Total of all scores should be 100
        check_score_for_state(self, sgs, self.TRIBUTE, EXPECT, 100)

    def test_g_scoring_tribute_no_solo_3(self):
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
        EXPECT = {self.austria: 0,
                  self.england: 5 + 66/4 - 11,
                  self.france: 0,
                  self.germany: 17 + 66/4 + 11*3,
                  self.italy: 0,
                  self.russia: 5 + 66/4 - 11,
                  self.turkey: 7 + 66/4 - 11}
        # Total of all scores should be 100
        check_score_for_state(self, sgs, self.TRIBUTE, EXPECT, 100)

    def test_g_scoring_tribute_solo(self):
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
                  self.germany: 100,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey: 0}
        check_score_for_state(self, sgs, self.TRIBUTE, EXPECT, 100)
