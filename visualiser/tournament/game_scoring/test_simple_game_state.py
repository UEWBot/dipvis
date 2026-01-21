# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2025 Chris Brand
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
from tournament.game_scoring.simple_game_state import SimpleGameState


class SimpleGameStateTests(TestCase):
    """
    Test SimpleGameState
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

    def test_sgs_concession_is_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 1,
                                         self.england: 10,
                                         self.france: 1,
                                         self.germany: 1,
                                         self.italy: 10,
                                         self.russia: 10,
                                         self.turkey: 1},
                              final_year=1907,
                              elimination_years={},
                              draw=[self.italy])
        self.assertEqual(sgs.soloer(), self.italy)
        self.assertEqual(sgs.powers_in_draw(), [self.italy])

    def test_sgs_solo_year_none(self):
        three_survivors = SimpleGameState(sc_counts={self.austria: 0,
                                                     self.england: 17,
                                                     self.france: 0,
                                                     self.germany: 0,
                                                     self.italy: 16,
                                                     self.russia: 1,
                                                     self.turkey: 0},
                                          final_year=1907,
                                          elimination_years={self.austria: 1903,
                                                             self.france: 1907,
                                                             self.germany: 1905,
                                                             self.turkey: 1905},
                                          draw=None)
        self.assertIsNone(three_survivors.solo_year())

    def test_dot_count_for_final_year(self):
        sc_counts={self.austria: 1,
                   self.england: 10,
                   self.france: 0,
                   self.germany: 2,
                   self.italy: 10,
                   self.russia: 10,
                   self.turkey: 1}
        sgs = SimpleGameState(sc_counts=sc_counts,
                              final_year=1907,
                              elimination_years={self.france: 1906},
                              draw=[self.italy])
        for p, c in sc_counts.items():
            with self.subTest(power=p):
                # Should not raise DotCountUnknown
                self.assertEqual(c, sgs.dot_count(p, year=1907))

