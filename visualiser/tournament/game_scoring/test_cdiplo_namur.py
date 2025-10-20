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


class CDiploNamurGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    C_DIPLO_NAMUR = 'C-Diplo Namur'

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

    def test_g_scoring_cdiplo_namur_no_solo1(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 4,
                                         self.germany: 8,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 8},
                              final_year=1904,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 1,
                  self.england: 1 + 16 + 7/2,
                  self.france: 1 + 14,
                  self.germany: 1 + 20 + (38 + 14)/2,
                  self.italy: 1 + 14,
                  self.russia: 1 + 16 + 7/2,
                  self.turkey: 1 + 20 + (38 + 14)/2}
        check_score_for_state(self, sgs, self.C_DIPLO_NAMUR, EXPECT)

    def test_g_scoring_cdiplo_namur_no_solo2(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 3,
                                         self.germany: 13,
                                         self.italy: 3,
                                         self.russia: 4,
                                         self.turkey: 6},
                              final_year=1905,
                              elimination_years={self.austria: 1904})
        EXPECT = {self.austria: 1,
                  self.england: 1 + 16 + 7,
                  self.france: 1 + 12,
                  self.germany: 1 + (18 + 7) + 38,
                  self.italy: 1 + 12,
                  self.russia: 1 + 14,
                  self.turkey: 1 + 18 + 14}
        check_score_for_state(self, sgs, self.C_DIPLO_NAMUR, EXPECT)

    def test_g_scoring_cdiplo_namur_no_solo3(self):
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
        EXPECT = {self.austria: 1,
                  self.england: 1 + 16 + 7/2,
                  self.france: 1,
                  self.germany: 1 + (18 + 11) + 38,
                  self.italy: 1,
                  self.russia: 1 + 16 + 7/2,
                  self.turkey: 1 + (18 + 1) + 14}
        check_score_for_state(self, sgs, self.C_DIPLO_NAMUR, EXPECT)

    def test_g_scoring_cdiplo_namur_3way(self):
        sgs = SimpleGameState(sc_counts={self.austria: 4,
                                         self.england: 4,
                                         self.france: 4,
                                         self.germany: 6,
                                         self.italy: 4,
                                         self.russia: 6,
                                         self.turkey: 6},
                              final_year=1902,
                              elimination_years={})
        EXPECT = {self.austria: 1 + 14,
                  self.england: 1 + 14,
                  self.france: 1 + 14,
                  self.germany: 1 + 18 + (38 + 14 + 7)/3,
                  self.italy: 1 + 14,
                  self.russia: 1 + 18 + (38 + 14 + 7)/3,
                  self.turkey: 1 + 18 + (38 + 14 + 7)/3}
        check_score_for_state(self, sgs, self.C_DIPLO_NAMUR, EXPECT)

    def test_g_scoring_cdiplo_namur_solo(self):
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
                  self.germany: 85,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey: 0}
        check_score_for_state(self, sgs, self.C_DIPLO_NAMUR, EXPECT)
