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

import copy

from django.test import TestCase

from tournament.diplomacy.models.great_power import GreatPower
from tournament.game_scoring.g_scoring_systems import G_SCORING_SYSTEMS
from tournament.game_scoring.game_state import InvalidYear
from tournament.game_scoring.sc_chart_game_state import SCChartGameState
from tournament.game_scoring.simple_game_state import SimpleGameState
from tournament.models import find_game_scoring_system


# Function needed by most classes
def check_score_order(self, scores):
    """Check that the scores appear in GreatPower order when iterated through"""
    EXPECT = [p for p in GreatPower.objects.all()]
    order = [k for k in scores.keys()]
    self.assertEqual(EXPECT, order)


def check_score_for_state(self, state, system_name, expected_scores):
    """
    Generic test for a scoring system

    Checks the scores produced by the specified scoring system for the specifed game state.
    """
    system = find_game_scoring_system(system_name)
    scores = system.scores(state)
    self.assertEqual(7, len(scores))
    for p,s in scores.items():
        with self.subTest(power=p):
            self.assertAlmostEqual(s, expected_scores[p])
    check_score_order(self, scores)


class GameScoringTests(TestCase):
    """
    Tests that aren't specific to one scoring system
    """
    fixtures = ['game_sets.json']

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
        powers = [cls.austria, cls.england, cls.france, cls.germany, cls.italy, cls.russia, cls.turkey]

        # SC chart for a game that has made it to 1906 without a solo
        pre_solo_sc_chart = {1901: {cls.austria: 5,
                                    cls.england: 4,
                                    cls.france: 5,
                                    cls.germany: 5,
                                    cls.italy: 4,
                                    cls.russia: 5,
                                    cls.turkey: 4},
                             1902: {cls.austria: 4,
                                    cls.england: 4,
                                    cls.france: 4,
                                    cls.germany: 6,
                                    cls.italy: 4,
                                    cls.russia: 6,
                                    cls.turkey: 6},
                             1904: {cls.austria: 0,
                                    cls.england: 5,
                                    cls.france: 4,
                                    cls.germany: 8,
                                    cls.italy: 4,
                                    cls.russia: 5,
                                    cls.turkey: 8},
                             1905: {cls.austria: 0,
                                    cls.england: 5,
                                    cls.france: 3,
                                    cls.germany: 13,
                                    cls.italy: 3,
                                    cls.russia: 4,
                                    cls.turkey: 6},
                             1906: {cls.austria: 0,
                                    cls.england: 5,
                                    cls.france: 0,
                                    cls.germany: 17,
                                    cls.italy: 0,
                                    cls.russia: 5,
                                    cls.turkey: 7}}
        # Second SC chart that is identical but with a solo in 1907
        post_solo_sc_chart = copy.deepcopy(pre_solo_sc_chart)
        post_solo_sc_chart[1907] = {cls.austria: 0,
                                    cls.england: 4,
                                    cls.france: 0,
                                    cls.germany: 18,
                                    cls.italy: 0,
                                    cls.russia: 5,
                                    cls.turkey: 7}

        # One game as an SCChartGameState
        # To cover Maxonian and 7Eleven, we need more history of the game
        cls.pre_solo_game = SCChartGameState(powers=powers, sc_counts=pre_solo_sc_chart)
        cls.post_solo_game = SCChartGameState(powers=powers, sc_counts=post_solo_sc_chart)

        # SimpleGameStates for two Games
        cls.three_way_tie = SimpleGameState(sc_counts={cls.austria: 1,
                                                       cls.england: 10,
                                                       cls.france: 1,
                                                       cls.germany: 1,
                                                       cls.italy: 10,
                                                       cls.russia: 10,
                                                       cls.turkey: 1},
                                            final_year=1907,
                                            elimination_years={},
                                            draw=None)
        cls.three_survivors = SimpleGameState(sc_counts={cls.austria: 0,
                                                         cls.england: 17,
                                                         cls.france: 0,
                                                         cls.germany: 0,
                                                         cls.italy: 16,
                                                         cls.russia: 1,
                                                         cls.turkey: 0},
                                              final_year=1907,
                                              elimination_years={cls.austria: 1903,
                                                                 cls.france: 1907,
                                                                 cls.germany: 1905,
                                                                 cls.turkey: 1905},
                                              draw=None)

    def test_no_corruption(self):
        """Ensure that calls to calculate scores are independent"""
        # Essentially a test for issue #188
        system = find_game_scoring_system('CDiplo 80')
        scores = system.scores(self.three_way_tie)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = self.three_way_tie.dot_count(p)
            # 3 powers equal on 10 SCs, and 4 equal on 1 SC
            if sc == 1:
                self.assertEqual(s, 1)
            else:
                self.assertEqual(s, (25 + 14 + 7) / 3 + 10)
        self.assertEqual(sum(scores.values()), 80)
        scores = system.scores(self.three_survivors)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = self.three_survivors.dot_count(p)
            if sc == 17:
                self.assertEqual(s, 17 + 25)
            elif sc == 16:
                self.assertEqual(s, 16 + 14)
            elif sc == 1:
                self.assertEqual(s, 1 + 7)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 80)

    # description for all G_SCORING_SYSTEMS
    def test_description(self):
        for system in G_SCORING_SYSTEMS:
            with self.subTest(system=system.name):
                desc = system.description
                # TODO verify desc

    # dead_score_can_change() for all G_SCORING_SYSTEMS
    def test_score_changes(self):
        """Compare score for eliminated power before and after a solo"""
        for system in G_SCORING_SYSTEMS:
            with self.subTest(system=system.name):
                scores1 = system.scores(self.pre_solo_game)
                scores2 = system.scores(self.post_solo_game)
                # Pick an eliminated power, but not the first eliminated
                # Under Haight, the first eliminated power's score can't change, but other's can
                changes = scores1[self.france] != scores2[self.france]
                self.assertEqual(changes, system.dead_score_can_change)
