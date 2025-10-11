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


class TributeGameScoringTests(TestCase):
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
        system = find_game_scoring_system('Tribute')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
                if sgs.sc_counts[p] == 4:
                    self.assertEqual(s, 66 / 7 + 4)
                else:
                    self.assertEqual(s, 66 / 7 + 5)
        # Total of all scores should be 100 minus 2 (neutrals)
        self.assertAlmostEqual(sum(scores.values()), 98)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('Tribute')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 0:
                    self.assertEqual(s, 0)
                elif sgs.sc_counts[p] == 4:
                    self.assertEqual(s, 4 + 66/6 - 2)
                elif sgs.sc_counts[p] == 5:
                    self.assertEqual(s, 5 + 66/6 - 2)
                else:
                    self.assertEqual(s, 8 + 66/6 + 2 * 4 / 2)
        # Total of all scores should be 100
        self.assertAlmostEqual(sum(scores.values()), 100)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('Tribute')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 0:
                    self.assertEqual(s, 0)
                elif sgs.sc_counts[p] == 3:
                    self.assertEqual(s, 3 + 66/6 - 7)
                elif sgs.sc_counts[p] == 4:
                    self.assertEqual(s, 4 + 66/6 - 7)
                elif sgs.sc_counts[p] == 5:
                    self.assertEqual(s, 5 + 66/6 - 7)
                elif sgs.sc_counts[p] == 6:
                    self.assertEqual(s, 6 + 66/6 - 7)
                else:
                    self.assertEqual(s, 13 + 66/6 + 7 * 5)
        # Total of all scores should be 100
        self.assertAlmostEqual(sum(scores.values()), 100)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('Tribute')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 0:
                    self.assertEqual(s, 0)
                elif sgs.sc_counts[p] == 5:
                    self.assertEqual(s, 5 + 66/4 - 11)
                elif sgs.sc_counts[p] == 7:
                    self.assertEqual(s, 7 + 66/4 - 11)
                else:
                    self.assertEqual(s, 17 + 66/4 + 11*3)
        # Total of all scores should be 100
        self.assertAlmostEqual(sum(scores.values()), 100)
        check_score_order(self, scores)

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
        system = find_game_scoring_system('Tribute')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if sgs.sc_counts[p] == 18:
                    self.assertEqual(s, 100)
                else:
                    self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)
        check_score_order(self, scores)
