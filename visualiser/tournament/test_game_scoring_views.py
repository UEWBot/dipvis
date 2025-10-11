# Diplomacy Tournament Visualiser
# Copyright (C) 2020 Chris Brand
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
from django.urls import reverse

from tournament.game_scoring.g_scoring_systems import G_SCORING_SYSTEMS
from tournament.game_scoring_system_views import SimpleGameState, InvalidState

class GameScoringViewTests(TestCase):
    fixtures = ['game_sets.json']

    def test_index(self):
        response = self.client.get(reverse('game_scoring_index'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Check sorting - systems should be listed in alphabetical order
        # TODO Probably needs work for translation
        names = [s.name for s in G_SCORING_SYSTEMS]
        last_i = 0
        last_name = None
        for name in sorted(names):
            with self.subTest(previous=last_name, current=name):
                i = response.content.find(str.encode('>'+name+'<'))
                self.assertTrue(i > last_i)
            last_i = i
            last_name = name

    def test_detail_invalid_system(self):
        response = self.client.get(reverse('game_scoring_detail',
                                           kwargs={'slug': 'invalid-scoring-system'}),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_detail(self):
        """Don't have to be logged in to see a scoring system"""
        response = self.client.get(reverse('game_scoring_detail',
                                           args=(G_SCORING_SYSTEMS[0].slug,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_detail_all(self):
        for sys in G_SCORING_SYSTEMS:
            with self.subTest(sys):
                response = self.client.get(reverse('game_scoring_detail',
                                                   args=(sys.slug,)),
                                           secure=True)
                self.assertEqual(response.status_code, 200)

    def test_invalid_simplegamestate_1(self):
        too_many_dots = {'A': 10, 'E': 0, 'F': 2, 'G': 10, 'I': 1, 'R': 10, 'T': 2}
        self.assertRaises(InvalidState, SimpleGameState, too_many_dots, 1908, {'E': 1902})

    def test_invalid_simplegamestate_2(self):
        sc_counts = {'A': 10, 'E': 0, 'F': 2, 'G': 10, 'I': 1, 'R': 10, 'T': 1}
        self.assertRaises(InvalidState, SimpleGameState, sc_counts, 1908, {'E': 1900})

    def test_invalid_simplegamestate_3(self):
        sc_counts = {'A': 10, 'E': 0, 'F': 2, 'G': 10, 'I': 1, 'R': 10, 'T': 1}
        self.assertRaises(InvalidState, SimpleGameState, sc_counts, 1908, {'E': 1909})

    def test_invalid_simplegamestate_4(self):
        sc_counts = {'A': 10, 'E': 1, 'F': 1, 'G': 10, 'I': 1, 'R': 10, 'T': 1}
        self.assertRaises(InvalidState, SimpleGameState, sc_counts, 1908, {'E': 1902})
