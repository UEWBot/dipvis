# Diplomacy Tournament Visualiser
# Copyright (C) 2026 Chris Brand
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

from tournament.diplomacy import GreatPower

from .sc_chart_game_state import SCChartGameState
from .test_general import check_score_for_state


class GIRSHGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')
        cls.powers = [cls.austria, cls.england, cls.france, cls.germany,
                      cls.italy, cls.russia, cls.turkey]

    def _state(self, sc_counts):
        return SCChartGameState(self.powers, sc_counts)

    def _system(self):
        from tournament.models import find_game_scoring_system
        return find_game_scoring_system('Gap Incentivised Rank SC Hybrid')

    def test_girsh_pdf_example(self):
        """Use the PDF example exactly as provided in the specification."""
        state = self._state({1901: {self.austria: 4, self.england: 5, self.france: 5,
                                   self.germany: 5, self.italy: 5, self.russia: 5,
                                   self.turkey: 5},
                            1902: {self.austria: 6, self.england: 6, self.france: 5,
                                   self.germany: 5, self.italy: 5, self.russia: 4,
                                   self.turkey: 3},
                            1903: {self.austria: 8, self.england: 7, self.france: 5,
                                   self.germany: 4, self.italy: 4, self.russia: 2,
                                   self.turkey: 0},
                            1904: {self.austria: 10, self.england: 9, self.france: 5,
                                   self.germany: 1, self.italy: 3, self.russia: 1,
                                   self.turkey: 0},
                            1905: {self.austria: 12, self.england: 10, self.france: 4,
                                   self.germany: 1, self.italy: 0, self.russia: 1,
                                   self.turkey: 0},
                            1906: {self.austria: 14, self.england: 11, self.france: 2,
                                   self.germany: 1, self.italy: 0, self.russia: 1,
                                   self.turkey: 0},
                            1907: {self.austria: 15, self.england: 12, self.france: 1,
                                   self.germany: 1, self.italy: 0, self.russia: 1,
                                   self.turkey: 0},
                            1908: {self.austria: 15, self.england: 13, self.france: 1,
                                   self.germany: 0, self.italy: 0, self.russia: 1,
                                   self.turkey: 0},
                            1909: {self.austria: 16, self.england: 13, self.france: 1,
                                   self.germany: 0, self.italy: 0, self.russia: 4,
                                   self.turkey: 0}})
        self.assertEqual(state.year_eliminated(self.turkey), 1903)
        self.assertEqual(state.year_eliminated(self.italy), 1905)
        self.assertEqual(state.year_eliminated(self.germany), 1908)
        scores = self._system().scores(state)
        self.assertEqual(scores[self.austria], 130 + 80 + 30 + 9)
        self.assertEqual(scores[self.england], 90 + 65 - 10 + 9)
        self.assertEqual(scores[self.russia], 60 + 20 - 10 + 9)
        self.assertEqual(scores[self.france], 40 + 5 - 10 + 9)
        self.assertEqual(scores[self.germany], 30 + 8)
        self.assertEqual(scores[self.italy], 20 + 5)
        self.assertEqual(scores[self.turkey], 10 + 3)
        self.assertGreater(scores[self.austria], scores[self.england])
        self.assertGreater(scores[self.england], scores[self.russia])

    def test_girsh_no_gap_bonus_below_three(self):
        state = self._state({1901: {self.austria: 5, self.england: 5, self.france: 5,
                                   self.germany: 5, self.italy: 5, self.russia: 5,
                                   self.turkey: 2},
                            1902: {self.austria: 6, self.england: 6, self.france: 5,
                                   self.germany: 4, self.italy: 4, self.russia: 4,
                                   self.turkey: 2},
                            1903: {self.austria: 8, self.england: 7, self.france: 5,
                                   self.germany: 2, self.italy: 2, self.russia: 2,
                                   self.turkey: 2},
                            1904: {self.austria: 10, self.england: 9, self.france: 5,
                                   self.germany: 0, self.italy: 0, self.russia: 0,
                                   self.turkey: 0},
                            1905: {self.austria: 10, self.england: 9, self.france: 5,
                                   self.germany: 0, self.italy: 0, self.russia: 0,
                                   self.turkey: 0},
                            1906: {self.austria: 10, self.england: 9, self.france: 5,
                                   self.germany: 0, self.italy: 0, self.russia: 0,
                                   self.turkey: 0},
                            1907: {self.austria: 10, self.england: 9, self.france: 5,
                                   self.germany: 0, self.italy: 0, self.russia: 0,
                                   self.turkey: 0},
                            1908: {self.austria: 10, self.england: 9, self.france: 5,
                                   self.germany: 0, self.italy: 0, self.russia: 0,
                                   self.turkey: 0}})
        scores = self._system().scores(state)
        self.assertEqual(scores[self.austria], 130 + 10 * 5 + 8)
        self.assertEqual(scores[self.england], 90 + 9 * 5 + 8)
        self.assertEqual(scores[self.france], 60 + 5 * 5 + 8)
        self.assertEqual(scores[self.germany], 30 + 4)
        self.assertEqual(scores[self.italy], 30 + 4)
        self.assertEqual(scores[self.russia], 30 + 4)
        self.assertEqual(scores[self.turkey], 10 + 4)
        self.assertEqual(scores[self.austria] - scores[self.england], 45)

    def test_girsh_gap_bonus_and_penalty(self):
        state = self._state({1901: {self.austria: 5, self.england: 4, self.france: 4,
                                   self.germany: 5, self.italy: 5, self.russia: 5,
                                   self.turkey: 5},
                            1902: {self.austria: 7, self.england: 5, self.france: 5,
                                   self.germany: 6, self.italy: 5, self.russia: 4,
                                   self.turkey: 2},
                            1903: {self.austria: 9, self.england: 7, self.france: 5,
                                   self.germany: 5, self.italy: 5, self.russia: 3,
                                   self.turkey: 0},
                            1904: {self.austria: 12, self.england: 9, self.france: 5,
                                   self.germany: 2, self.italy: 4, self.russia: 2,
                                   self.turkey: 0},
                            1905: {self.austria: 14, self.england: 10, self.france: 5,
                                   self.germany: 4, self.italy: 1, self.russia: 0,
                                   self.turkey: 0},
                            1906: {self.austria: 14, self.england: 10, self.france: 5,
                                   self.germany: 2, self.italy: 1, self.russia: 0,
                                   self.turkey: 0},
                            1907: {self.austria: 14, self.england: 11, self.france: 4,
                                   self.germany: 3, self.italy: 1, self.russia: 0,
                                   self.turkey: 0},
                            1908: {self.austria: 14, self.england: 11, self.france: 4,
                                   self.germany: 3, self.italy: 2, self.russia: 0,
                                   self.turkey: 0},
                            1909: {self.austria: 14, self.england: 11, self.france: 4,
                                   self.germany: 3, self.italy: 2, self.russia: 0,
                                   self.turkey: 0}})
        scores = self._system().scores(state)
        self.assertEqual(scores[self.austria], 130 + 14 * 5 + 30 + 9)
        self.assertEqual(scores[self.england], 90 + 11 * 5 - 7 + 9)
        self.assertEqual(scores[self.france], 60 + 4 * 5 - 7 + 9)
        self.assertEqual(scores[self.germany], 40 + 3 * 5 - 7 + 9)
        self.assertEqual(scores[self.italy], 30 + 2 * 5 - 7 + 9)
        self.assertEqual(scores[self.russia], 20 + 0 + 0 + 5)
        self.assertEqual(scores[self.turkey], 10 + 0 + 0 + 3)

    def test_girsh_solo_bonus(self):
        state = self._state({1901: {self.austria: 4, self.england: 4, self.france: 4,
                                   self.germany: 4, self.italy: 4, self.russia: 4,
                                   self.turkey: 4},
                            1902: {self.austria: 3, self.england: 5, self.france: 3,
                                   self.germany: 5, self.italy: 5, self.russia: 4,
                                   self.turkey: 4},
                            1903: {self.austria: 2, self.england: 7, self.france: 2,
                                   self.germany: 6, self.italy: 5, self.russia: 4,
                                   self.turkey: 5},
                            1904: {self.austria: 0, self.england: 10, self.france: 1,
                                   self.germany: 7, self.italy: 5, self.russia: 3,
                                   self.turkey: 6},
                            1905: {self.austria: 0, self.england: 12, self.france: 1,
                                   self.germany: 8, self.italy: 5, self.russia: 2,
                                   self.turkey: 6},
                            1906: {self.austria: 0, self.england: 15, self.france: 0,
                                   self.germany: 9, self.italy: 4, self.russia: 1,
                                   self.turkey: 5},
                            1907: {self.austria: 0, self.england: 16, self.france: 0,
                                   self.germany: 10, self.italy: 4, self.russia: 0,
                                   self.turkey: 4},
                            1908: {self.austria: 0, self.england: 18, self.france: 0,
                                   self.germany: 10, self.italy: 4, self.russia: 0,
                                   self.turkey: 2}})
        scores = self._system().scores(state)
        self.assertEqual(scores[self.austria], 10 + 4)
        self.assertEqual(scores[self.england], 130 + 90 + 8)
        self.assertEqual(scores[self.france], 20 + 6)
        self.assertEqual(scores[self.germany], 90 + 8)
        self.assertEqual(scores[self.italy], 60 + 8)
        self.assertEqual(scores[self.russia], 30 + 7)
        self.assertEqual(scores[self.turkey], 40 + 8)

    def test_girsh_countback_breaks_ties(self):
        state = self._state({1901: {self.austria: 5, self.england: 5, self.france: 5,
                                   self.germany: 5, self.italy: 5, self.russia: 5,
                                   self.turkey: 4},
                            1902: {self.austria: 4, self.england: 6, self.france: 4,
                                   self.germany: 7, self.italy: 8, self.russia: 4,
                                   self.turkey: 1},
                            1903: {self.austria: 3, self.england: 7, self.france: 3,
                                   self.germany: 9, self.italy: 10, self.russia: 2,
                                   self.turkey: 0},
                            1904: {self.austria: 2, self.england: 7, self.france: 2,
                                   self.germany: 9, self.italy: 10, self.russia: 1,
                                   self.turkey: 0},
                            1905: {self.austria: 2, self.england: 7, self.france: 2,
                                   self.germany: 9, self.italy: 10, self.russia: 1,
                                   self.turkey: 0},
                            1906: {self.austria: 2, self.england: 7, self.france: 2,
                                   self.germany: 9, self.italy: 10, self.russia: 1,
                                   self.turkey: 0},
                            1907: {self.austria: 2, self.england: 7, self.france: 2,
                                   self.germany: 9, self.italy: 10, self.russia: 1,
                                   self.turkey: 0},
                            1908: {self.austria: 2, self.england: 7, self.france: 2,
                                   self.germany: 9, self.italy: 10, self.russia: 1,
                                   self.turkey: 0}})
        scores = self._system().scores(state)
        self.assertEqual(scores[self.austria], (40 + 30) / 2 + 2 * 5 + 8)
        self.assertEqual(scores[self.england], 60 + 7 * 5 + 8)
        self.assertEqual(scores[self.france], (40 + 30) / 2 + 2 * 5 + 8)
        self.assertEqual(scores[self.germany], 90 + 9 * 5 + 8)
        self.assertEqual(scores[self.italy], 130 + 10 * 5 + 8)
        self.assertEqual(scores[self.russia], 20 + 1 * 5 + 8)
        self.assertEqual(scores[self.turkey], 10 + 3)

    def test_girsh_countback_when_leaders_tied(self):
        state = self._state({1901: {self.austria: 4, self.england: 4, self.france: 4,
                                   self.germany: 4, self.italy: 4, self.russia: 4,
                                   self.turkey: 4},
                            1902: {self.austria: 5, self.england: 5, self.france: 3,
                                   self.germany: 3, self.italy: 2, self.russia: 2,
                                   self.turkey: 2},
                            1903: {self.austria: 6, self.england: 6, self.france: 2,
                                   self.germany: 2, self.italy: 1, self.russia: 1,
                                   self.turkey: 1},
                            1904: {self.austria: 6, self.england: 6, self.france: 2,
                                   self.germany: 2, self.italy: 1, self.russia: 1,
                                   self.turkey: 0},
                            1905: {self.austria: 6, self.england: 6, self.france: 2,
                                   self.germany: 2, self.italy: 1, self.russia: 1,
                                   self.turkey: 0},
                            1906: {self.austria: 6, self.england: 6, self.france: 2,
                                   self.germany: 2, self.italy: 1, self.russia: 1,
                                   self.turkey: 0},
                            1907: {self.austria: 6, self.england: 6, self.france: 2,
                                   self.germany: 2, self.italy: 1, self.russia: 1,
                                   self.turkey: 0},
                            1908: {self.austria: 6, self.england: 6, self.france: 2,
                                   self.germany: 2, self.italy: 1, self.russia: 1,
                                   self.turkey: 0}})
        scores = self._system().scores(state)
        self.assertEqual(scores[self.austria], 130 + 10 + 8)
        self.assertEqual(scores[self.england], 90 + 50 + 8)
        self.assertEqual(scores[self.france], 60 + 2 + 6)
        self.assertEqual(scores[self.germany], 60 + 2 + 6)
        self.assertEqual(scores[self.italy], 30 + 4 + 4)
        self.assertEqual(scores[self.russia], 30 + 4 + 4)
        self.assertEqual(scores[self.turkey], 10 + 4)
        self.assertEqual(scores[self.austria], scores[self.england])
