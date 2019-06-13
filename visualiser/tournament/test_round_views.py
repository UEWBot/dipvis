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

from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tournament.diplomacy import GameSet, GreatPower
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, TournamentPlayer
from tournament.models import Round, RoundPlayer
from tournament.models import Game, GamePlayer, SeederBias
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.players import Player

class RoundViewTests(TestCase):
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
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           is_published=True)
        cls.r11 = Round.objects.create(tournament=cls.t1,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=cls.t1.start_date)
        # Add TournamentPlayers
        TournamentPlayer.objects.create(player=p1,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p2,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p3,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p4,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p5,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p6,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p7,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p8,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p9,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p10,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p11,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p12,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=p13,
                                        tournament=cls.t1)
        # And RoundPlayers
        RoundPlayer.objects.create(player=p1, the_round=cls.r11)
        RoundPlayer.objects.create(player=p2, the_round=cls.r11)
        RoundPlayer.objects.create(player=p3, the_round=cls.r11)
        RoundPlayer.objects.create(player=p4, the_round=cls.r11)
        RoundPlayer.objects.create(player=p5, the_round=cls.r11)
        RoundPlayer.objects.create(player=p6, the_round=cls.r11)
        RoundPlayer.objects.create(player=p7, the_round=cls.r11)
        RoundPlayer.objects.create(player=p8, the_round=cls.r11)
        RoundPlayer.objects.create(player=p9, the_round=cls.r11)
        RoundPlayer.objects.create(player=p10, the_round=cls.r11)
        RoundPlayer.objects.create(player=p11, the_round=cls.r11)
        RoundPlayer.objects.create(player=p12, the_round=cls.r11, game_count=0)
        RoundPlayer.objects.create(player=p13, the_round=cls.r11, game_count=2)

        # Published Tournament so it's visible to all. PREFERENCES power assignment
        cls.t2 = Tournament.objects.create(name='t2',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           power_assignment=Tournament.PREFERENCES,
                                           is_published=True)
        cls.r21 = Round.objects.create(tournament=cls.t2,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=cls.t2.start_date)
        cls.r22 = Round.objects.create(tournament=cls.t2,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=cls.t2.start_date + timedelta(hours=24))
        cls.r23 = Round.objects.create(tournament=cls.t2,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=cls.t2.start_date + timedelta(hours=48))
        TournamentPlayer.objects.create(player=p1,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=p2,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=p3,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=p4,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=p5,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=p6,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=p7,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=p8,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=p9,
                                        tournament=cls.t2)
        # First Round has no RoundPlayers
        # Second Round has only 6 RoundPlayers
        RoundPlayer.objects.create(player=p3, the_round=cls.r22)
        RoundPlayer.objects.create(player=p4, the_round=cls.r22)
        RoundPlayer.objects.create(player=p5, the_round=cls.r22)
        RoundPlayer.objects.create(player=p6, the_round=cls.r22)
        RoundPlayer.objects.create(player=p7, the_round=cls.r22)
        RoundPlayer.objects.create(player=p8, the_round=cls.r22)
        # Third Round has exactly seven RoundPlayers
        RoundPlayer.objects.create(player=p1, the_round=cls.r23)
        RoundPlayer.objects.create(player=p3, the_round=cls.r23)
        RoundPlayer.objects.create(player=p4, the_round=cls.r23)
        RoundPlayer.objects.create(player=p5, the_round=cls.r23)
        RoundPlayer.objects.create(player=p6, the_round=cls.r23)
        RoundPlayer.objects.create(player=p7, the_round=cls.r23)
        RoundPlayer.objects.create(player=p8, the_round=cls.r23)

        # Published Tournament so it's visible to all. AUTO power assignment
        cls.t3 = Tournament.objects.create(name='t3',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           power_assignment=Tournament.AUTO,
                                           is_published=True)
        cls.r31 = Round.objects.create(tournament=cls.t3,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=cls.t3.start_date)
        cls.r32 = Round.objects.create(tournament=cls.t3,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=cls.t3.start_date + timedelta(hours=24))
        TournamentPlayer.objects.create(player=p1,
                                        tournament=cls.t3)
        cls.tp2 = TournamentPlayer.objects.create(player=p2,
                                                  tournament=cls.t3)
        cls.tp3 = TournamentPlayer.objects.create(player=p3,
                                                  tournament=cls.t3)
        TournamentPlayer.objects.create(player=p4,
                                        tournament=cls.t3)
        TournamentPlayer.objects.create(player=p5,
                                        tournament=cls.t3)
        TournamentPlayer.objects.create(player=p6,
                                        tournament=cls.t3)
        TournamentPlayer.objects.create(player=p7,
                                        tournament=cls.t3)
        TournamentPlayer.objects.create(player=p8,
                                        tournament=cls.t3)
        TournamentPlayer.objects.create(player=p9,
                                        tournament=cls.t3)
        # Add SeederBias for a pair of players
        SeederBias.objects.create(player1=cls.tp2, player2=cls.tp3, weight=3)
        # First Round has exactly seven RoundPlayers
        RoundPlayer.objects.create(player=p1, the_round=cls.r31)
        RoundPlayer.objects.create(player=p3, the_round=cls.r31)
        RoundPlayer.objects.create(player=p4, the_round=cls.r31)
        RoundPlayer.objects.create(player=p5, the_round=cls.r31)
        RoundPlayer.objects.create(player=p6, the_round=cls.r31)
        RoundPlayer.objects.create(player=p7, the_round=cls.r31)
        RoundPlayer.objects.create(player=p8, the_round=cls.r31)
        # Second Round has eight RoundPlayers, one sitting out
        RoundPlayer.objects.create(player=p1, the_round=cls.r32)
        RoundPlayer.objects.create(player=p3, the_round=cls.r32)
        RoundPlayer.objects.create(player=p4, the_round=cls.r32)
        RoundPlayer.objects.create(player=p5, the_round=cls.r32)
        RoundPlayer.objects.create(player=p6, the_round=cls.r32)
        RoundPlayer.objects.create(player=p7, the_round=cls.r32)
        RoundPlayer.objects.create(player=p8, the_round=cls.r32, game_count=0)
        RoundPlayer.objects.create(player=p9, the_round=cls.r32)
        # Add a single Game to the first Round
        g = Game.objects.create(name='T3R1G1',
                                started_at=cls.t3.start_date,
                                is_finished=True,
                                the_round=cls.r31,
                                the_set=GameSet.objects.get(name='Avalon Hill'))
        GamePlayer.objects.create(player=p1, game=g, power=cls.turkey)
        GamePlayer.objects.create(player=p3, game=g, power=cls.russia)
        GamePlayer.objects.create(player=p4, game=g, power=cls.italy)
        GamePlayer.objects.create(player=p5, game=g, power=cls.germany)
        GamePlayer.objects.create(player=p6, game=g, power=cls.france)
        GamePlayer.objects.create(player=p7, game=g, power=cls.england)
        GamePlayer.objects.create(player=p8, game=g, power=cls.austria)

    def test_detail(self):
        response = self.client.get(reverse('round_detail', args=(self.t1.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_detail_non_existant_round(self):
        response = self.client.get(reverse('round_detail', args=(self.t1.pk, 2)))
        self.assertEqual(response.status_code, 404)

    def test_roll_call_not_logged_in(self):
        response = self.client.get(reverse('round_roll_call', args=(self.t1.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_roll_call_all_rounds(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('roll_call', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_roll_call_one_round(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('round_roll_call', args=(self.t1.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_get_seven_not_logged_in(self):
        response = self.client.get(reverse('get_seven', args=(self.t1.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_get_seven(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('get_seven', args=(self.t1.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_get_seven_too_few_players(self):
        # Nothing we can do if have fewer than seven players
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('get_seven', args=(self.t2.pk, 2)))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tournament_players', args=(self.t2.pk,)))

    def test_get_seven_good_number(self):
        # No action needed if we have an exact multiple of seven players
        self.assertEqual(self.t2.round_numbered(3).roundplayer_set.count(), 7)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('get_seven', args=(self.t2.pk, 3)))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('seed_games', args=(self.t2.pk, 3)))

    def test_seed_games_not_logged_in(self):
        response = self.client.get(reverse('seed_games', args=(self.t1.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_seed_games_odd_number(self):
        # if we dont have a mutiple of 7 players, this view should redirect to fix that
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games', args=(self.t1.pk, 1)))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('get_seven', args=(self.t1.pk, 1)))

    def test_seed_games_preferences_good_number(self):
        # Simple case with exactly seven players with PREFERENCES power assignment
        self.assertEqual(self.t2.round_numbered(3).roundplayer_set.count(), 7)
        self.assertEqual(self.t2.round_numbered(3).game_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games', args=(self.t2.pk, 3)))
        self.assertEqual(response.status_code, 200)
        # A single Game should have been created
        g_qs = self.t2.round_numbered(3).game_set
        self.assertEqual(g_qs.count(), 1)
        # with seven GamePlayers
        g = g_qs.get()
        self.assertEqual(g.gameplayer_set.count(), 7)
        # Clean up
        g.delete()

    def test_seed_games_auto_good_number(self):
        # Eight players, one sitting out, AUTO power assignment
        self.assertEqual(self.t3.round_numbered(2).game_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games', args=(self.t3.pk, 2)))
        self.assertEqual(response.status_code, 200)
        # A single Game should have been created
        g_qs = self.t3.round_numbered(2).game_set
        self.assertEqual(g_qs.count(), 1)
        # with seven GamePlayers
        g = g_qs.get()
        self.assertEqual(g.gameplayer_set.count(), 7)
        # Clean up
        g.delete()

    def test_create_games_not_logged_in(self):
        response = self.client.get(reverse('create_games', args=(self.t1.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_create_games(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('create_games', args=(self.t1.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_create_games_no_players(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('create_games', args=(self.t2.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_create_games_when_games_exist(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('create_games', args=(self.t3.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_game_scores_not_logged_in(self):
        response = self.client.get(reverse('game_scores', args=(self.t1.pk, 1)))
        self.assertEqual(response.status_code, 302)

    def test_game_scores(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('game_scores', args=(self.t3.pk, 1)))
        self.assertEqual(response.status_code, 200)

    def test_game_index(self):
        response = self.client.get(reverse('game_index', args=(self.t1.pk, 1)))
        self.assertEqual(response.status_code, 200)
