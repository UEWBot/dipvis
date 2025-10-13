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


class ManorConGameScoringTests(TestCase):
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
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 458)
                elif sgs.sc_counts[p] == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 458)
                elif sgs.sc_counts[p] == 8:
                    self.assertAlmostEqual(s, 100 * 112 / 458)
                else:
                    self.assertAlmostEqual(s, 0.3)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 3:
                    self.assertAlmostEqual(s, 100 * 37 / 512)
                elif sgs.sc_counts[p] == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 512)
                elif sgs.sc_counts[p] == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 512)
                elif sgs.sc_counts[p] == 6:
                    self.assertAlmostEqual(s, 100 * 76 / 512)
                elif sgs.sc_counts[p] == 13:
                    self.assertAlmostEqual(s, 100 * 237 / 512)
                else:
                    self.assertAlmostEqual(s, 0.3)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 636)
                elif sgs.sc_counts[p] == 7:
                    self.assertAlmostEqual(s, 100 * 93 / 636)
                elif sgs.sc_counts[p] == 17:
                    self.assertAlmostEqual(s, 100 * 373 / 636)
                else:
                    if p == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif p == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        # Italy
                        self.assertAlmostEqual(s, 0.5)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 18:
                    self.assertEqual(s, 75)
                else:
                    if p == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif p == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    elif p == self.italy:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        self.assertAlmostEqual(s, 0.6)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('Original ManorCon')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 458)
                elif sgs.sc_counts[p] == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 458)
                elif sgs.sc_counts[p] == 8:
                    self.assertAlmostEqual(s, 100 * 112 / 458)
                else:
                    self.assertAlmostEqual(s, 0.3)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('Original ManorCon')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 3:
                    self.assertAlmostEqual(s, 100 * 37 / 512)
                elif sgs.sc_counts[p] == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 512)
                elif sgs.sc_counts[p] == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 512)
                elif sgs.sc_counts[p] == 6:
                    self.assertAlmostEqual(s, 100 * 76 / 512)
                elif sgs.sc_counts[p] == 13:
                    self.assertAlmostEqual(s, 100 * 237 / 512)
                else:
                    self.assertAlmostEqual(s, 0.3)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('Original ManorCon')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 636)
                elif sgs.sc_counts[p] == 7:
                    self.assertAlmostEqual(s, 100 * 93 / 636)
                elif sgs.sc_counts[p] == 17:
                    self.assertAlmostEqual(s, 100 * 373 / 636)
                else:
                    if p == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif p == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        # Italy
                        self.assertAlmostEqual(s, 0.5)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('Original ManorCon')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 18:
                    self.assertEqual(s, 100)
                else:
                    if p == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif p == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    elif p == self.italy:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        self.assertAlmostEqual(s, 0.6)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('ManorCon v2')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 442)
                elif sgs.sc_counts[p] == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 442)
                elif sgs.sc_counts[p] == 8:
                    self.assertAlmostEqual(s, 100 * 112 / 442)
                else:
                    self.assertAlmostEqual(s, 0.3)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('ManorCon v2')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 3:
                    self.assertAlmostEqual(s, 100 * 37 / 496)
                elif sgs.sc_counts[p] == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 496)
                elif sgs.sc_counts[p] == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 496)
                elif sgs.sc_counts[p] == 6:
                    self.assertAlmostEqual(s, 100 * 76 / 496)
                elif sgs.sc_counts[p] == 13:
                    self.assertAlmostEqual(s, 100 * 237 / 496)
                else:
                    self.assertAlmostEqual(s, 0.3)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('ManorCon v2')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 588)
                elif sgs.sc_counts[p] == 7:
                    self.assertAlmostEqual(s, 100 * 93 / 588)
                elif sgs.sc_counts[p] == 17:
                    self.assertAlmostEqual(s, 100 * 373 / 588)
                else:
                    if p == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif p == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        # Italy
                        self.assertAlmostEqual(s, 0.5)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('ManorCon v2')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 18:
                    self.assertEqual(s, 100)
                else:
                    if p == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif p == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    elif p == self.italy:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        self.assertAlmostEqual(s, 0.6)
        check_score_order(self, scores)
