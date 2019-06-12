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

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, TournamentPlayer
from tournament.models import Round, RoundPlayer
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.players import Player

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

        # Some Players
        p1 = Player.objects.create(first_name='Angela',
                                   last_name='Ampersand')
        p2 = Player.objects.create(first_name='Bobby',
                                   last_name='Bandersnatch')
        p3 = Player.objects.create(first_name='Cassandra',
                                   last_name='Cucumber')
        p4 = Player.objects.create(first_name='Derek',
                                   last_name='Dromedary')
        p5 = Player.objects.create(first_name='Ethel',
                                   last_name='Elephant')
        p6 = Player.objects.create(first_name='Frank',
                                   last_name='Frankfurter')
        p7 = Player.objects.create(first_name='Georgette',
                                   last_name='Grape')
        p8 = Player.objects.create(first_name='Harry',
                                   last_name='Heffalump')
        p9 = Player.objects.create(first_name='Iris',
                                   last_name='Ignoramus')
        p10 = Player.objects.create(first_name='Jake',
                                    last_name='Jalopy')
        p11 = Player.objects.create(first_name='Katrina',
                                    last_name='Kingpin')
        p12 = Player.objects.create(first_name='Lucas',
                                    last_name='Lemon')
        p13 = Player.objects.create(first_name='Margaret',
                                    last_name='Maleficent')

        now = timezone.now()
        # Published Tournament so it's visible to all
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=now,
                                          end_date=now,
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=Tournament.SECRET,
                                          is_published=True)
        cls.r1 = Round.objects.create(tournament=cls.t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=cls.t.start_date)
        # Add TournamentPlayers
        tp = TournamentPlayer.objects.create(player=p1,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p2,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p3,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p4,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p5,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p6,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p7,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p8,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p9,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p10,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p11,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p12,
                                             tournament=cls.t)
        tp = TournamentPlayer.objects.create(player=p13,
                                             tournament=cls.t)
        # And RoundPlayers
        RoundPlayer.objects.create(player=p1, the_round=cls.r1)
        RoundPlayer.objects.create(player=p2, the_round=cls.r1)
        RoundPlayer.objects.create(player=p3, the_round=cls.r1)
        RoundPlayer.objects.create(player=p4, the_round=cls.r1)
        RoundPlayer.objects.create(player=p5, the_round=cls.r1)
        RoundPlayer.objects.create(player=p6, the_round=cls.r1)
        RoundPlayer.objects.create(player=p7, the_round=cls.r1)
        RoundPlayer.objects.create(player=p8, the_round=cls.r1)
        RoundPlayer.objects.create(player=p9, the_round=cls.r1)
        RoundPlayer.objects.create(player=p10, the_round=cls.r1)
        RoundPlayer.objects.create(player=p11, the_round=cls.r1)
        RoundPlayer.objects.create(player=p12, the_round=cls.r1)
        RoundPlayer.objects.create(player=p13, the_round=cls.r1)

    def test_detail(self):
        response = self.client.get(reverse('round_detail', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_detail_non_existant_round(self):
        response = self.client.get(reverse('round_detail', args=(self.t.pk, 2)))
        self.assertEqual(response.status_code, 404)

    def test_roll_call_not_logged_in(self):
        response = self.client.get(reverse('round_roll_call', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_roll_call(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('round_roll_call', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_get_seven_not_logged_in(self):
        response = self.client.get(reverse('get_seven', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_get_seven(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('get_seven', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_seed_games_not_logged_in(self):
        response = self.client.get(reverse('seed_games', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_seed_games_odd_number(self):
        # if we dont have a mutiple of 7 players, this view should redirect to fix that
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('get_seven', args=(self.t.pk, 1)))

    def test_create_games_not_logged_in(self):
        response = self.client.get(reverse('create_games', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_create_games(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('create_games', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_game_scores_not_logged_in(self):
        response = self.client.get(reverse('game_scores', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_game_scores(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('game_scores', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_game_index(self):
        response = self.client.get(reverse('game_index', args=(self.t.pk, 1)))
        self.assertEqual(response.status_code, 200)
