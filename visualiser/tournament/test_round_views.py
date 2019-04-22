# Diplomacy Tournament Visualiser
# Copyright (C) 2019 Chris Brand
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
from django.utils import timezone

from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, Round
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS

class RoundViewTests(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        # Published Tournament so it's visible to all
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=now,
                                          end_date=now,
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=Tournament.SECRET,
                                          is_published=True)
        Round.objects.create(tournament=cls.t,
                             scoring_system=G_SCORING_SYSTEMS[0].name,
                             dias=True,
                             start=cls.t.start_date)

    def test_detail(self):
        response = self.client.get(reverse('round_detail', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_create_games_not_logged_in(self):
        response = self.client.get(reverse('create_games', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_get_seven_not_logged_in(self):
        response = self.client.get(reverse('get_seven', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_seed_games_not_logged_in(self):
        response = self.client.get(reverse('seed_games', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_game_scores_not_logged_in(self):
        response = self.client.get(reverse('game_scores', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_games(self):
        response = self.client.get(reverse('game_index', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_roll_call_not_logged_in(self):
        response = self.client.get(reverse('round_roll_call', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 302)
