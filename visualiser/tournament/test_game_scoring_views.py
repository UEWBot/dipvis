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

from tournament.game_scoring import GameScoringSystem, G_SCORING_SYSTEMS

class GameScoringViewTests(TestCase):

    def test_index(self):
        response = self.client.get(reverse('game_scoring_index'))
        self.assertEqual(response.status_code, 200)
        # Check sorting - systems should be listed in alphabetical order
        # TODO Probably needs work for translation
        names = [s.name for s in G_SCORING_SYSTEMS]
        last_i = 0
        last_name = None
        for name in sorted(names):
            with self.subTest(previous=last_name, current=name):
                i = response.content.find(str.encode(name))
                self.assertTrue(i > last_i)
            last_i = i
            last_name = name

    def test_detail_invalid_system(self):
        response = self.client.get(reverse('game_scoring_detail', kwargs={'slug': 'invalid-scoring-system'}))
        self.assertEqual(response.status_code, 404)

    def test_detail(self):
        # Don't have to be logged in to see a scoring system
        response = self.client.get(reverse('game_scoring_detail', args=(G_SCORING_SYSTEMS[0].slug,)))
        self.assertEqual(response.status_code, 200)
