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
from tournament.diplomacy.values.diplomacy_values import TOTAL_SCS
from tournament.game_scoring.test_general import check_score_order
from tournament.game_scoring_system_views import SimpleGameState
from tournament.models import find_game_scoring_system


class CarnageGameScoringTests(TestCase):
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

    # GScoringCarnage (with dead equal)
    def test_g_scoring_carnage1_simple(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sgs.sc_counts[p] == 4:
                self.assertEqual(s, (3000 + 2000 + 1000) / 3 + sgs.sc_counts[p])
            else:
                self.assertEqual(s, (7000 + 6000 + 5000 + 4000) / 4 + sgs.sc_counts[p])
        # 2 SCs are still neutral
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS - 2)
        check_score_order(self, scores)

    def test_g_scoring_carnage1_solo(self):
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
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if sgs.sc_counts[p] == 18:
                self.assertEqual(s, 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        check_score_order(self, scores)

    def test_g_scoring_carnage1_eliminations(self):
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
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        for p,s in scores.items():
            # 1 at 17, 1 at 7, 2 at 5, and 3 eliminated
            if sgs.sc_counts[p] == 17:
                self.assertEqual(s, 7000 + sgs.sc_counts[p])
            elif sgs.sc_counts[p] == 7:
                self.assertEqual(s, 6000 + sgs.sc_counts[p])
            elif sgs.sc_counts[p] == 5:
                self.assertEqual(s, (5000 + 4000) / 2 + sgs.sc_counts[p])
            else:
                self.assertEqual(s, (3000 + 2000 + 1000) / 3 + sgs.sc_counts[p])
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        check_score_order(self, scores)

    # Carnage with elimination order
    def test_g_scoring_carnage2_simple(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        system = find_game_scoring_system('Carnage with elimination order')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sgs.sc_counts[p] == 4:
                self.assertEqual(s, (3000 + 2000 + 1000) / 3 + sgs.sc_counts[p])
            else:
                self.assertEqual(s, (7000 + 6000 + 5000 + 4000) / 4 + sgs.sc_counts[p])
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS - 2)
        check_score_order(self, scores)

    def test_g_scoring_carnage2_solo(self):
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
        system = find_game_scoring_system('Carnage with elimination order')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if sgs.sc_counts[p] == 18:
                self.assertEqual(s, 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        check_score_order(self, scores)

    def test_g_scoring_carnage2_eliminations(self):
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
        system = find_game_scoring_system('Carnage with elimination order')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            # 1 at 17, 1 at 7, 2 at 5, and 3 eliminated
            if sgs.sc_counts[p] == 17:
                self.assertEqual(s, 7000 + sgs.sc_counts[p])
            elif sgs.sc_counts[p] == 7:
                self.assertEqual(s, 6000 + sgs.sc_counts[p])
            elif sgs.sc_counts[p] == 5:
                self.assertEqual(s, (5000 + 4000) / 2 + sgs.sc_counts[p])
            else:
                # Austria died in 1904, France and Italy in 1906
                if p in [self.france, self.italy]:
                    self.assertEqual(s, (3000 + 2000) / 2 + sgs.sc_counts[p])
                else:
                    self.assertEqual(s, 1000 + sgs.sc_counts[p])
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        check_score_order(self, scores)

    # Carnage 2023 (elimination order and leader gap bonus)
    def test_g_scoring_carnage2023_simple(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        system = find_game_scoring_system('Carnage 2023')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sgs.sc_counts[p] == 4:
                self.assertEqual(s, (3000 + 2000 + 1000) / 3 + sgs.sc_counts[p])
            else:
                self.assertEqual(s, (7000 + 6000 + 5000 + 4000) / 4 + sgs.sc_counts[p])
        # With tied lead, we know the total score
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS - 2)
        check_score_order(self, scores)

    def test_g_scoring_carnage2023_solo(self):
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
        system = find_game_scoring_system('Carnage 2023')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if sgs.sc_counts[p] == 18:
                self.assertEqual(s, 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
            else:
                self.assertEqual(s, 0)
        # With a solo, we know the total score
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        check_score_order(self, scores)

    def test_g_scoring_carnage2023_eliminations(self):
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
        system = find_game_scoring_system('Carnage 2023')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            # 1 at 17, 1 at 7, 2 at 5, and 3 eliminated
            if sgs.sc_counts[p] == 17:
                # Bonus 300 points per dot ahead of second place
                self.assertEqual(s, 7000 + sgs.sc_counts[p] + (17 - 7) * 300)
            elif sgs.sc_counts[p] == 7:
                self.assertEqual(s, 6000 + sgs.sc_counts[p])
            elif sgs.sc_counts[p] == 5:
                self.assertEqual(s, (5000 + 4000) / 2 + sgs.sc_counts[p])
            else:
                # Austria died in 1904, France and Italy in 1906
                if p in [self.france, self.italy]:
                    self.assertEqual(s, (3000 + 2000) / 2 + sgs.sc_counts[p])
                else:
                    self.assertEqual(s, 1000 + sgs.sc_counts[p])
        check_score_order(self, scores)
        # Total score now varies depending on the lead the leader has

    # GScoringCentreCarnage
    def test_g_scoring_centrecarnage_1(self):
        # There used to be an "example 1" and "example 2" in the doc, but no more :-(
        example_1 = SimpleGameState(sc_counts={self.austria: 11,
                                               self.england: 10,
                                               self.france: 8,
                                               self.germany: 2,
                                               self.italy: 2,
                                               self.russia: 1,
                                               self.turkey: 0},
                                    final_year=1908,
                                    elimination_years={self.turkey: 1904},
                                    draw=None)
        system = find_game_scoring_system('Center-count Carnage')
        scores = system.scores(example_1)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, 11 * 500 + 7007)
            elif p == self.england:
                self.assertEqual(s, 10 * 500 + 6006)
            elif p == self.france:
                self.assertEqual(s, 8 * 500 + 5005)
            elif p == self.germany:
                self.assertEqual(s,  2 * 500 + (4004 + 3003) / 2)
            elif p == self.italy:
                self.assertEqual(s,  2 * 500 + (4004 + 3003) / 2)
            elif p == self.russia:
                self.assertEqual(s, 1 * 500 + 2002)
            else:
                # Turkey:
                self.assertEqual(s, 1001)
        check_score_order(self, scores)

    def test_g_scoring_centrecarnage_2(self):
        # There used to be an "example 1" and "example 2" in the doc, but no more :-(
        example_2 = SimpleGameState(sc_counts={self.austria: 13,
                                               self.england: 7,
                                               self.france: 5,
                                               self.germany: 5,
                                               self.italy: 4,
                                               self.russia: 0,
                                               self.turkey: 0},
                                    final_year=1908,
                                    elimination_years={self.russia: 1905,
                                                       self.turkey: 1904},
                                    draw=None)
        system = find_game_scoring_system('Center-count Carnage')
        scores = system.scores(example_2)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, 13 * 500 + 7007)
            elif p == self.england:
                self.assertEqual(s, 7 * 500 + 6006)
            elif p == self.france:
                self.assertEqual(s, 5 * 500 + (5005 + 4004) / 2)
            elif p == self.germany:
                self.assertEqual(s, 5 * 500 + (5005 + 4004) / 2)
            elif p == self.italy:
                self.assertEqual(s, 4 * 500 + 3003)
            elif p == self.russia:
                self.assertEqual(s, 2002)
            else:
                # Turkey:
                self.assertEqual(s, 1001)
        check_score_order(self, scores)
