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

from tournament.diplomacy.models.great_power import GreatPower
from tournament.game_scoring.test_general import check_score_for_state
from tournament.game_scoring.simple_game_state import SimpleGameState


class YourDrawSizeGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    # Scoring systems tested
    YDS_LONG = 'Your Draw Size (unlimited games)'
    YDS_SHORT = 'Your Draw Size (short games)'

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

    def test_g_scoring_yds_no_solo_1(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        EXPECT = {self.austria: 30,
                  self.england: 30,
                  self.france: 30,
                  self.germany: 30,
                  self.italy: 30,
                  self.russia: 30,
                  self.turkey: 30}
        check_score_for_state(self, sgs, self.YDS_SHORT, EXPECT)

    def test_g_scoring_yds_no_solo_2(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 3,
                                         self.germany: 11,
                                         self.italy: 4,
                                         self.russia: 3,
                                         self.turkey: 8},
                              final_year=1904,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0,
                  self.england: 30,
                  self.france: 21,
                  self.germany: 70,
                  self.italy: 30,
                  self.russia: 21,
                  self.turkey: 42}
        check_score_for_state(self, sgs, self.YDS_SHORT, EXPECT)

    def test_g_scoring_yds_no_solo_3(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 1,
                                         self.germany: 14,
                                         self.italy: 2,
                                         self.russia: 4,
                                         self.turkey: 8},
                              final_year=1905,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 0,
                  self.england: 30,
                  self.france: 21,
                  self.germany: 105,
                  self.italy: 21,
                  self.russia: 30,
                  self.turkey: 42}
        check_score_for_state(self, sgs, self.YDS_SHORT, EXPECT)

    def test_g_scoring_yds_no_solo_4(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 4,
                                         self.france: 0,
                                         self.germany: 17,
                                         self.italy: 0,
                                         self.russia: 6,
                                         self.turkey: 7},
                              final_year=1906,
                              elimination_years={self.austria: 1904,
                                                 self.france: 1906,
                                                 self.italy: 1906})
        EXPECT = {self.austria: 0,
                  self.england: 30,
                  self.france: 0,
                  self.germany: 105,
                  self.italy: 0,
                  self.russia: 30,
                  self.turkey: 30}
        check_score_for_state(self, sgs, self.YDS_SHORT, EXPECT)

    def test_g_scoring_yds_short_solo(self):
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
                  self.germany: 300,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey: 0}
        check_score_for_state(self, sgs, self.YDS_SHORT, EXPECT, 300)

    def test_g_scoring_yds_long_solo(self):
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
                  self.germany: 320,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey: 0}
        check_score_for_state(self, sgs, self.YDS_LONG, EXPECT, 320)
