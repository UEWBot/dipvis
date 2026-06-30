# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2026 Chris Brand
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


class MischiefGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    # Scoring systems tested
    MISCHIEF = 'Mischief'

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

    def test_g_scoring_mischief_lone_top(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 6,
                                         self.france: 8,
                                         self.germany: 7,
                                         self.italy: 9,
                                         self.russia: 0,
                                         self.turkey: 4},
                              final_year=1904,
                              elimination_years={self.austria: 1904,
                                                 self.russia: 1904})
        EXPECT = {self.austria: 0,
                  self.england: 6,
                  self.france: 8,
                  self.germany: 7,
                  self.italy: 9 + 5,
                  self.russia: 0,
                  self.turkey: 4}
        check_score_for_state(self, sgs, self.MISCHIEF, EXPECT)

    def test_g_scoring_mischief_2way(self):
        sgs = SimpleGameState(sc_counts={self.austria: 8,
                                         self.england: 5,
                                         self.france: 7,
                                         self.germany: 0,
                                         self.italy: 0,
                                         self.russia: 6,
                                         self.turkey: 8},
                              final_year=1912,
                              elimination_years={self.germany: 1904,
                                                 self.italy: 1908})
        EXPECT = {self.austria: 8 + 1,
                  self.england: 5,
                  self.france: 7,
                  self.germany: 0,
                  self.italy: 0,
                  self.russia: 6,
                  self.turkey: 8 + 1}
        check_score_for_state(self, sgs, self.MISCHIEF, EXPECT)

    def test_g_scoring_mischief_3way(self):
        sgs = SimpleGameState(sc_counts={self.austria: 9,
                                         self.england: 5,
                                         self.france: 0,
                                         self.germany: 0,
                                         self.italy: 9,
                                         self.russia: 2,
                                         self.turkey: 9},
                              final_year=1912,
                              elimination_years={self.france: 1903,
                                                 self.germany: 1904})
        EXPECT = {self.austria: 9,
                  self.england: 5,
                  self.france: 0,
                  self.germany: 0,
                  self.italy: 9,
                  self.russia: 2,
                  self.turkey: 9}
        check_score_for_state(self, sgs, self.MISCHIEF, EXPECT)

    def test_g_scoring_mischief_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 18,
                                         self.england: 8,
                                         self.france: 6,
                                         self.germany: 0,
                                         self.italy: 0,
                                         self.russia: 2,
                                         self.turkey: 0},
                              final_year=1907,
                              elimination_years={self.germany: 1904,
                                                 self.italy: 1906,
                                                 self.turkey: 1906})
        EXPECT = {self.austria: 34,
                  self.england: 0,
                  self.france: 0,
                  self.germany: 0,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey: 0}
        check_score_for_state(self, sgs, self.MISCHIEF, EXPECT)
