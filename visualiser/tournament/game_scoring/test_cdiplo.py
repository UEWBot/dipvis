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


class CDiploGameScoringTests(TestCase):
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

    def test_g_scoring_cdiplo_no_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        system = find_game_scoring_system('CDiplo 100')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sgs.sc_counts[p] == 4:
                self.assertEqual(s, 1 + 4)
            else:
                self.assertEqual(s, 1 + (38 + 14 + 7) / 4 + 5)
        # With 2 neutrals, the total of all scores should be 100-2=98
        self.assertEqual(sum(scores.values()), 100 - 2)
        check_score_order(self, scores)

    def test_g_scoring_cdiplo_solo(self):
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
        system = find_game_scoring_system('CDiplo 100')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if sgs.sc_counts[p] == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)
        check_score_order(self, scores)

    def test_g_scoring_cdiplo80_no_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 5,
                                         self.england: 4,
                                         self.france: 5,
                                         self.germany: 5,
                                         self.italy: 4,
                                         self.russia: 5,
                                         self.turkey: 4},
                              final_year=1901,
                              elimination_years={})
        system = find_game_scoring_system('CDiplo 80')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sgs.sc_counts[p] == 4:
                self.assertEqual(s, 4)
            else:
                self.assertEqual(s, (25 + 14 + 7) / 4 + 5)
        # With 2 neutrals, the total of all scores should be 80-2=78
        self.assertEqual(sum(scores.values()), 80 - 2)
        check_score_order(self, scores)

    def test_g_scoring_cdiplo80_solo(self):
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
        system = find_game_scoring_system('CDiplo 80')
        scores = system.scores(sgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if sgs.sc_counts[p] == 18:
                self.assertEqual(s, 80)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 80)
        check_score_order(self, scores)
