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

from django.contrib.auth.models import Permission, User
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
        # A regular user with no special permissions or ownership
        cls.USERNAME1 = 'regular'
        cls.PWORD1 = 'CleverPassword'
        u1 = User.objects.create_user(username=cls.USERNAME1, password=cls.PWORD1)
        u1.save()

        # A superuser
        cls.USERNAME2 = 'superuser'
        cls.PWORD2 = 'L33tPw0rd'
        u2 = User.objects.create_user(username=cls.USERNAME2,
                                      password=cls.PWORD2,
                                      is_superuser=True)
        u2.save()

        # A user who is a manager of a tournament (t2)
        # We give managers the appropriate permissions
        cls.USERNAME3 = 'manager'
        cls.PWORD3 = 'MyPassword'
        perm = Permission.objects.get(name='Can change round player')
        u3 = User.objects.create_user(username=cls.USERNAME3,
                                      password=cls.PWORD3)
        u3.user_permissions.add(perm)
        u3.save()

        now = timezone.now()
        # Published Tournament, so it's visible to all
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           is_published=True)
        p = Player.objects.create(first_name='Angela',
                                  last_name='Ampersand')
        cls.tp = TournamentPlayer.objects.create(player=p,
                                                 tournament=cls.t1,
                                                 uuid_str=str(uuid.uuid4()))

        # Unpublished Tournament, with a manager (u3)
        cls.t2 = Tournament.objects.create(name='t2',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           is_published=False)
        cls.t2.managers.add(u3)

        # Unpublished Tournament, without a manager
        cls.t3 = Tournament.objects.create(name='t3',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           is_published=False)

        # Published Tournament, without a manager, but not editable
        cls.t4 = Tournament.objects.create(name='t4',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           is_published=True,
                                           editable=False)
        # Hopefully this isn't the pk for any Tournament
        cls.INVALID_T_PK = 99999

    def test_index(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_detail_invalid_tournament(self):
        response = self.client.get(reverse('tournament_detail', args=(self.INVALID_T_PK,)))
        self.assertEqual(response.status_code, 404)

    def test_detail_manager_wrong_tournament(self):
        # A manager can't see an unpublished tournament that isn't theirs
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('tournament_detail', args=(self.t3.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_detail(self):
        # Don't have to be logged in to see a published tournament
        response = self.client.get(reverse('tournament_detail', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_detail_regular_user(self):
        # Any user can see a published tournament
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('tournament_detail', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_detail_superuser(self):
        # A superuser can see any tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('tournament_detail', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_detail_manager(self):
        # A manager see their unpublished tournament
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('tournament_detail', args=(self.t2.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_framesets(self):
        response = self.client.get(reverse('framesets', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_3x3(self):
        response = self.client.get(reverse('frameset_3x3', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_top_board(self):
        response = self.client.get(reverse('frameset_top_board', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_2x2(self):
        response = self.client.get(reverse('frameset_2x2', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_1x1(self):
        response = self.client.get(reverse('frameset_1x1', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_views(self):
        response = self.client.get(reverse('tournament_views', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_overview(self):
        response = self.client.get(reverse('tournament_overview', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_overview2(self):
        response = self.client.get(reverse('tournament_overview_2', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_overview3(self):
        response = self.client.get(reverse('tournament_overview_3', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_scores(self):
        response = self.client.get(reverse('tournament_scores', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_scores_refresh(self):
        response = self.client.get(reverse('tournament_scores_refresh', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_game_results(self):
        response = self.client.get(reverse('tournament_game_results', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_best_countries(self):
        response = self.client.get(reverse('tournament_best_countries', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_best_countries_refresh(self):
        response = self.client.get(reverse('tournament_best_countries_refresh', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_enter_scores_not_logged_in(self):
        response = self.client.get(reverse('enter_scores', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_enter_scores_regular_user(self):
        # A regular user can't enter scores for any old tournament
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('enter_scores', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_enter_scores_manager_wrong_tournament(self):
        # A manager can't enter scores for a tournament that isn't theirs
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_scores', args=(self.t3.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_enter_scores_archived(self):
        # Nobody can enter scores for an archived tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('enter_scores', args=(self.t4.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_enter_scores_superuser(self):
        # A superuser can enter scores for any tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('enter_scores', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_enter_scores_manager(self):
        # A manager can enter scores for their tournament
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_scores', args=(self.t2.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_roll_call_not_logged_in(self):
        response = self.client.get(reverse('roll_call', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_current_round(self):
        response = self.client.get(reverse('tournament_round', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_game_image_not_logged_in(self):
        response = self.client.get(reverse('add_game_image', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_news(self):
        response = self.client.get(reverse('tournament_news', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_news_ticker(self):
        response = self.client.get(reverse('tournament_news_ticker', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_background(self):
        response = self.client.get(reverse('tournament_background', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_ticker(self):
        response = self.client.get(reverse('tournament_ticker', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_background_ticker(self):
        response = self.client.get(reverse('tournament_background_ticker', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_rounds(self):
        response = self.client.get(reverse('round_index', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_prefs_not_logged_in(self):
        response = self.client.get(reverse('enter_prefs', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_upload_prefs_not_logged_in(self):
        response = self.client.get(reverse('upload_prefs', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_prefs_csv(self):
        response = self.client.get(reverse('prefs_csv', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_player_prefs(self):
        response = self.client.get(reverse('player_prefs', args=(self.t1.pk, self.tp.uuid_str)))
        self.assertEqual(response.status_code, 200)
