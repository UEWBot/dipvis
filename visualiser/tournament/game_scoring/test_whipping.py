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
from tournament.game_scoring.test_general import check_score_order
from tournament.game_scoring.simple_game_state import SimpleGameState
from tournament.models import find_game_scoring_system


class WhippingGameScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

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
        system = find_game_scoring_system('Whipping')
        scores = system.scores(example_a)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, 4)
            elif p == self.england:
                self.assertEqual(s, (120 + 12 + 24))
            elif p == self.france:
                self.assertEqual(s, (30 + 12))
            elif p == self.germany:
                self.assertEqual(s, (60 + 12))
            elif p == self.italy:
                self.assertEqual(s, (90 + 12))
            elif p == self.russia:
                self.assertEqual(s, 8)
            else:
                # Turkey
                self.assertEqual(s, (40 + 12))
        check_score_order(self, scores)

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
        system = find_game_scoring_system('Whipping')
        scores = system.scores(example_b)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, (170 + 15 + 34))
            elif p == self.england:
                self.assertEqual(s, 11)
            elif p == self.france:
                self.assertEqual(s, (10 + 15))
            elif p == self.germany:
                self.assertEqual(s, (120 + 15))
            elif p == self.italy:
                self.assertEqual(s, 6)
            elif p == self.russia:
                self.assertEqual(s, (40 + 15))
            else:
                # Turkey
                self.assertEqual(s, 5)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('Whipping')
        scores = system.scores(example_c)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, (340 + 60 + 68))
            elif p == self.england:
                self.assertEqual(s, 11)
            elif p == self.france:
                self.assertEqual(s, 11)
            elif p == self.germany:
                self.assertEqual(s, 8)
            elif p == self.italy:
                self.assertEqual(s, 5)
            elif p == self.russia:
                self.assertEqual(s, 11)
            else:
                # Turkey
                self.assertEqual(s, 4)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('Whipping')
        scores = system.scores(example_d)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, (40 + 15))
            elif p == self.england:
                self.assertEqual(s, (110 + 15 + 0))
            elif p == self.france:
                self.assertEqual(s, (110 + 15 + 0))
            elif p == self.germany:
                self.assertEqual(s, 4)
            elif p == self.italy:
                self.assertEqual(s, 7)
            elif p == self.russia:
                self.assertEqual(s, 6)
            else:
                # Turkey
                self.assertEqual(s, (80 + 15))
        check_score_order(self, scores)
