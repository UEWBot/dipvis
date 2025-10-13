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


class HaightGameScoringTests(TestCase):
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

    def test_g_scoring_haight_no_solo1(self):
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
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_a)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 171)
                elif p == self.france:
                    self.assertEqual(s, 145)
                elif p == self.germany:
                    self.assertEqual(s, 124)
                elif p == self.italy:
                    self.assertEqual(s, 83)
                elif p == self.russia:
                    self.assertEqual(s, (8 + 11))
                else:
                    # Turkey
                    self.assertEqual(s, 42)
        check_score_order(self, scores)

    def test_g_scoring_haight_no_solo2(self):
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
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_b)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 271)
                elif p == self.france:
                    self.assertEqual(s, (8 + 11))
                elif p == self.germany:
                    self.assertEqual(s, 155)
                elif p == self.italy:
                    self.assertEqual(s, 84)
                elif p == self.russia:
                    self.assertEqual(s, (8 + 11))
                else:
                    # Turkey
                    self.assertEqual(s, 63)
        check_score_order(self, scores)

    def test_g_scoring_haight_no_solo3(self):
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
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_c)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 154)
                elif p == self.france:
                    self.assertEqual(s, (8 + 11))
                elif p == self.germany:
                    self.assertEqual(s, 154)
                elif p == self.italy:
                    self.assertEqual(s, 154)
                elif p == self.russia:
                    self.assertEqual(s, (8 + 11))
                else:
                    # Turkey
                    self.assertEqual(s, 43)
        check_score_order(self, scores)

    def test_g_scoring_haight_no_solo4(self):
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
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_d)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 191)
                elif p == self.france:
                    self.assertEqual(s, (8 + 33))
                elif p == self.germany:
                    self.assertEqual(s, 154)
                elif p == self.italy:
                    self.assertEqual(s, 154)
                elif p == self.russia:
                    self.assertEqual(s, (7 + 11))
                else:
                    # Turkey
                    self.assertEqual(s, (7 + 11))
        check_score_order(self, scores)

    def test_g_scoring_haight_no_solo5(self):
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
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_e)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 196)
                elif p == self.france:
                    self.assertEqual(s, (8 + 11))
                elif p == self.germany:
                    self.assertEqual(s, 144)
                elif p == self.italy:
                    self.assertEqual(s, 144)
                elif p == self.russia:
                    self.assertEqual(s, (8 + 11))
                else:
                    # Turkey
                    self.assertEqual(s, 53)
        check_score_order(self, scores)

    def test_g_scoring_haight_solo(self):
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
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_f)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 451)
                elif p == self.france:
                    self.assertEqual(s, 8)
                elif p == self.germany:
                    self.assertEqual(s, 50)
                elif p == self.italy:
                    self.assertEqual(s, 20)
                elif p == self.russia:
                    self.assertEqual(s, 8)
                else:
                    # Turkey
                    # Note that this differs from the document because the document
                    # assumes the game end in 1910 or earlier but I want to test the
                    # "or number of years played, if greater" part
                    self.assertEqual(s, 11)
        check_score_order(self, scores)
