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
from tournament.game_scoring_system_views import SimpleGameState
from tournament.models import find_game_scoring_system


class Detour09GameScoringTests(TestCase):
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

    def test_g_scoring_detour09_no_solo1(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 4,
                                         self.germany: 8,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 8},
                              final_year=1904,
                              elimination_years={self.austria: 1904})
        system = find_game_scoring_system('Detour09')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 4:
                    # 4+2+0+0=6
                    self.assertAlmostEqual(s, 100 * 6 / (6+6+8+8+13+13))
                elif sgs.sc_counts[p] == 5:
                    # 5+2+0+1=8
                    self.assertAlmostEqual(s, 100 * 8 / (6+6+8+8+13+13))
                elif sgs.sc_counts[p] == 8:
                    # 8+2+0+3=13
                    self.assertAlmostEqual(s, 100 * 13 / (6+6+8+8+13+13))
                else:
                    self.assertAlmostEqual(s, 0.75)
        check_score_order(self, scores)

    def test_g_scoring_detour09_no_solo2(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 3,
                                         self.germany: 13,
                                         self.italy: 3,
                                         self.russia: 4,
                                         self.turkey: 6},
                              final_year=1905,
                              elimination_years={self.austria: 1904})
        system = find_game_scoring_system('Detour09')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 3:
                    # 3+2+0+0=5
                    self.assertAlmostEqual(s, 100 * 5 / (5+5+7+9+11+26))
                elif sgs.sc_counts[p] == 4:
                    # 4+2+0+1=7
                    self.assertAlmostEqual(s, 100 * 7 / (5+5+7+9+11+26))
                elif sgs.sc_counts[p] == 5:
                    # 5+2+0+2=9
                    self.assertAlmostEqual(s, 100 * 9 / (5+5+7+9+11+26))
                elif sgs.sc_counts[p] == 6:
                    # 6+2+0+3=11
                    self.assertAlmostEqual(s, 100 * 11 / (5+5+7+9+11+26))
                elif sgs.sc_counts[p] == 13:
                    # 13+2+7+4=26
                    self.assertAlmostEqual(s, 100 * 26 / (5+5+7+9+11+26))
                else:
                    self.assertAlmostEqual(s, 0.75)
        check_score_order(self, scores)

    def test_g_scoring_detour09_no_solo3(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 5,
                                         self.france: 0,
                                         self.germany: 17,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 7},
                              final_year=1909,
                              elimination_years={self.austria: 1904,
                                                 self.france: 1909,
                                                 self.italy: 1909})
        system = find_game_scoring_system('Detour09')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 5:
                    # 5+2+0+1=8
                    self.assertAlmostEqual(s, 100 * 8 / (8+8+12+33))
                elif sgs.sc_counts[p] == 7:
                    # 7+2+0+3=12
                    self.assertAlmostEqual(s, 100 * 12 / (8+8+12+33))
                elif sgs.sc_counts[p] == 17:
                    # 17+2+10+4=33
                    self.assertAlmostEqual(s, 100 * 33 / (8+8+12+33))
                else:
                    if p == self.austria:
                        self.assertAlmostEqual(s, 0.75)
                    elif p == self.france:
                        self.assertAlmostEqual(s, 2.00)
                    else:
                        # Italy
                        self.assertAlmostEqual(s, 2.00)
        check_score_order(self, scores)

    def test_g_scoring_detour09_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 0,
                                         self.england: 4,
                                         self.france: 0,
                                         self.germany: 18,
                                         self.italy: 0,
                                         self.russia: 5,
                                         self.turkey: 7},
                              final_year=1910,
                              elimination_years={self.austria: 1904,
                                                 self.france: 1909,
                                                 self.italy: 1909})
        system = find_game_scoring_system('Detour09')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 18:
                    self.assertEqual(s, 110)
                else:
                    if p == self.austria:
                        self.assertAlmostEqual(s, 0.75)
                    else:
                        # Suvival bonus is capped at 2.0
                        self.assertAlmostEqual(s, 2.00)
        check_score_order(self, scores)

    def test_g_scoring_detour09_3_equal_top(self):
        sgs = SimpleGameState(sc_counts={self.austria: 4,
                                         self.england: 4,
                                         self.france: 4,
                                         self.germany: 6,
                                         self.italy: 4,
                                         self.russia: 6,
                                         self.turkey: 6},
                              final_year=1902,
                              elimination_years={})
        system = find_game_scoring_system('Detour09')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 4:
                    # 4+2+0+0=6
                    self.assertAlmostEqual(s, 100 * 6 / (6+6+6+6++10+10+10))
                else:
                    # sc.count == 6
                    # 6+2+0+2=10
                    self.assertAlmostEqual(s, 100 * 10 / (6+6+6+6+10+10+10))
        check_score_order(self, scores)

    def test_g_scoring_detour09_4_equal_top(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        system = find_game_scoring_system('Detour09')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 4:
                    # 4+2+0+0=6
                    self.assertAlmostEqual(s, 100 * 6 / (6+6+6+8+8+8+8))
                else:
                    # sc.count == 5
                    # 5+2+0+1=8
                    self.assertAlmostEqual(s, 100 * 8 / (6+6+6+8+8+8+8))
        check_score_order(self, scores)

    def test_g_scoring_detour09_2_equal_below_top(self):
        sgs = SimpleGameState(sc_counts={self.austria: 2,
                                         self.england: 3,
                                         self.france: 4,
                                         self.germany: 10,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 6},
                              final_year=1907,
                              elimination_years={})
        system = find_game_scoring_system('Detour09')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 10:
                    # 1st
                    # 10+2+4+4=20
                    self.assertAlmostEqual(s, 100 * 20 / (20+11+9+6+6+5+4))
                elif sgs.sc_counts[p] == 6:
                    # 2nd
                    # 6+2+3=11
                    self.assertAlmostEqual(s, 100 * 11 / (20+11+9+6+6+5+4))
                elif sgs.sc_counts[p] == 5:
                    # 3rd
                    # 5+2+2=9
                    self.assertAlmostEqual(s, 100 * 9 / (20+11+9+6+6+5+4))
                elif sgs.sc_counts[p] == 4:
                    # Joint 4th
                    # 4+2=6
                    self.assertAlmostEqual(s, 100 * 6 / (20+11+9+6+6+5+4))
                elif sgs.sc_counts[p] == 3:
                    # 6th
                    # 3+2=5
                    self.assertAlmostEqual(s, 100 * 5 / (20+11+9+6+6+5+4))
                else:
                    # 7th
                    # 2+2=4
                    self.assertAlmostEqual(s, 100 * 4 / (20+11+9+6+6+5+4))
        check_score_order(self, scores)

    def test_g_scoring_detour09_3_equal_below_top(self):
        sgs = SimpleGameState(sc_counts={self.austria: 2,
                                         self.england: 3,
                                         self.france: 4,
                                         self.germany: 10,
                                         self.italy: 4,
                                         self.russia: 4,
                                         self.turkey: 7},
                              final_year=1907,
                              elimination_years={})
        system = find_game_scoring_system('Detour09')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 10:
                    # 1st
                    # 10+2+3+4=19
                    self.assertAlmostEqual(s, 100 * 19 / (19+12+6+6+6+5+4))
                elif sgs.sc_counts[p] == 7:
                    # 2nd
                    # 7+2+3=12
                    self.assertAlmostEqual(s, 100 * 12 / (19+12+6+6+6+5+4))
                elif sgs.sc_counts[p] == 4:
                    # Joint 3rd
                    # 4+2=6
                    self.assertAlmostEqual(s, 100 * 6 / (19+12+6+6+6+5+4))
                elif sgs.sc_counts[p] == 3:
                    # 6th
                    # 3+2=5
                    self.assertAlmostEqual(s, 100 * 5 / (19+12+6+6+6+5+4))
                else:
                    # 7th
                    # 2+2=4
                    self.assertAlmostEqual(s, 100 * 4 / (19+12+6+6+6+5+4))
        check_score_order(self, scores)
