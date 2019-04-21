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

import uuid

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, TournamentPlayer
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.players import Player

class TournamentViewTests(TestCase):
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
        p = Player.objects.create(first_name='Angela',
                                  last_name='Ampersand')
        cls.tp = TournamentPlayer.objects.create(player=p,
                                                 tournament=cls.t,
                                                 uuid_str=str(uuid.uuid4()))

    def test_detail(self):
        response = self.client.get(reverse('tournament_detail', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_framesets(self):
        response = self.client.get(reverse('framesets', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_3x3(self):
        response = self.client.get(reverse('frameset_3x3', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_top_board(self):
        response = self.client.get(reverse('frameset_top_board', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_2x2(self):
        response = self.client.get(reverse('frameset_2x2', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_1x1(self):
        response = self.client.get(reverse('frameset_1x1', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_views(self):
        response = self.client.get(reverse('tournament_views', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_overview(self):
        response = self.client.get(reverse('tournament_overview', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_overview2(self):
        response = self.client.get(reverse('tournament_overview_2', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_overview3(self):
        response = self.client.get(reverse('tournament_overview_3', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_scores(self):
        response = self.client.get(reverse('tournament_scores', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_scores_refresh(self):
        response = self.client.get(reverse('tournament_scores_refresh', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_game_results(self):
        response = self.client.get(reverse('tournament_game_results', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_best_countries(self):
        response = self.client.get(reverse('tournament_best_countries', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_best_countries_refresh(self):
        response = self.client.get(reverse('tournament_best_countries_refresh', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_enter_scores_not_logged_in(self):
        response = self.client.get(reverse('enter_scores', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_roll_call_not_logged_in(self):
        response = self.client.get(reverse('roll_call', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_current_round(self):
        response = self.client.get(reverse('tournament_round', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_game_image_not_logged_in(self):
        response = self.client.get(reverse('add_game_image', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_news(self):
        response = self.client.get(reverse('tournament_news', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_news_ticker(self):
        response = self.client.get(reverse('tournament_news_ticker', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_background(self):
        response = self.client.get(reverse('tournament_background', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_ticker(self):
        response = self.client.get(reverse('tournament_ticker', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_background_ticker(self):
        response = self.client.get(reverse('tournament_background_ticker', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_rounds(self):
        response = self.client.get(reverse('round_index', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_prefs_not_logged_in(self):
        response = self.client.get(reverse('enter_prefs', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_upload_prefs_not_logged_in(self):
        response = self.client.get(reverse('upload_prefs', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_prefs_csv(self):
        response = self.client.get(reverse('prefs_csv', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_player_prefs(self):
        response = self.client.get(reverse('player_prefs', args=(self.t.pk, self.tp.uuid_str)))
        self.assertEqual(response.status_code, 200)
