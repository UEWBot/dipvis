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

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tournament.diplomacy import GameSet
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, Round, Game
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS

class RoundViewTests(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # A superuser
        cls.USERNAME1 = 'superuser'
        cls.PWORD1 = 'l33tPw0rd'
        u1 = User.objects.create_user(username=cls.USERNAME1,
                                      password=cls.PWORD1,
                                      is_superuser=True)
        u1.save()

        now = timezone.now()
        # Published Tournament so it's visible to all
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=now,
                                          end_date=now,
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=Tournament.SECRET,
                                          is_published=True)
        cls.r = Round.objects.create(tournament=cls.t,
                                     scoring_system=G_SCORING_SYSTEMS[0].name,
                                     dias=True,
                                     start=cls.t.start_date)
        Game.objects.create(name='Game1',
                            started_at=cls.r.start,
                            the_round=cls.r,
                            the_set=GameSet.objects.first())

    def test_detail(self):
        response = self.client.get(reverse('game_detail', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_detail_non_existant_game(self):
        response = self.client.get(reverse('game_detail', args=(self.t.pk, 'Game42')))
        self.assertEqual(response.status_code, 404)

    def test_sc_chart(self):
        response = self.client.get(reverse('game_sc_chart', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_sc_chart_refresh(self):
        response = self.client.get(reverse('game_sc_chart_refresh', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_enter_scs_not_logged_in(self):
        response = self.client.get(reverse('enter_scs', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 302)

    def test_enter_scs(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('enter_scs', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_sc_owners(self):
        response = self.client.get(reverse('game_sc_owners', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_sc_owners_refresh(self):
        response = self.client.get(reverse('game_sc_owners_refresh', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_enter_sc_owners_not_logged_in(self):
        response = self.client.get(reverse('enter_sc_owners', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 302)

    def test_enter_sc_owners(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('enter_sc_owners', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_current_game_image(self):
        response = self.client.get(reverse('current_game_image', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_game_image(self):
        response = self.client.get(reverse('game_image', args=(self.t.pk, 'Game1', 'S1901M')))
        self.assertEqual(response.status_code, 200)

    def test_timelapse(self):
        response = self.client.get(reverse('game_timelapse', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_game_image_seq(self):
        response = self.client.get(reverse('game_image_seq', args=(self.t.pk, 'Game1', 'S1901M')))
        self.assertEqual(response.status_code, 200)

    def test_add_position_not_logged_in(self):
        response = self.client.get(reverse('add_game_image', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 302)

    def test_add_position(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('add_game_image', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_news(self):
        response = self.client.get(reverse('game_news', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_news_ticker(self):
        response = self.client.get(reverse('game_news_ticker', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_background(self):
        response = self.client.get(reverse('game_background', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_background_ticker(self):
        response = self.client.get(reverse('game_background_ticker', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_ticker(self):
        response = self.client.get(reverse('game_ticker', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_draw_vote_not_logged_in(self):
        response = self.client.get(reverse('draw_vote', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 302)

    def test_draw_vote(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('draw_vote', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_views(self):
        response = self.client.get(reverse('game_views', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_overview(self):
        response = self.client.get(reverse('game_overview', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_overview2(self):
        response = self.client.get(reverse('game_overview_2', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_overview3(self):
        response = self.client.get(reverse('game_overview_3', args=(self.t.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)
