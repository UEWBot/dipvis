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

from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.game_scoring.g_scoring_systems import G_SCORING_SYSTEMS
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Formats, Game, GamePlayer, Pool,
                               PowerAssignMethods, Round, RoundPlayer,
                               SeederBias, Team, Tournament, TournamentPlayer)
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

        cls.gibsons = GameSet.objects.get(name='Gibsons')
        cls.ah = GameSet.objects.get(name='Avalon Hill')

        # A superuser
        cls.USERNAME1 = 'superuser'
        cls.PWORD1 = 'l33tPw0rd'
        u1 = User.objects.create_user(username=cls.USERNAME1,
                                      password=cls.PWORD1,
                                      is_superuser=True)
        u1.save()

        # Some Players
        cls.p1 = Player.objects.create(first_name='Angela',
                                       last_name='Ampersand')
        cls.p2 = Player.objects.create(first_name='Bobby',
                                       last_name='Bandersnatch')
        cls.p3 = Player.objects.create(first_name='Cassandra',
                                       last_name='Cucumber')
        cls.p4 = Player.objects.create(first_name='Derek',
                                       last_name='Dromedary')
        cls.p5 = Player.objects.create(first_name='Ethel',
                                       last_name='Elephant')
        cls.p6 = Player.objects.create(first_name='Frank',
                                       last_name='Frankfurter')
        cls.p7 = Player.objects.create(first_name='Georgette',
                                       last_name='Grape')
        cls.p8 = Player.objects.create(first_name='Harry',
                                       last_name='Heffalump')
        cls.p9 = Player.objects.create(first_name='Iris',
                                       last_name='Ignoramus')
        cls.p10 = Player.objects.create(first_name='Jake',
                                        last_name='Jalopy')
        cls.p11 = Player.objects.create(first_name='Katrina',
                                        last_name='Kingpin')
        cls.p12 = Player.objects.create(first_name='Lucas',
                                        last_name='Lemon')
        cls.p13 = Player.objects.create(first_name='Margaret',
                                        last_name='Maleficent')
        cls.p14 = Player.objects.create(first_name='Nigel',
                                        last_name='Notorious')

        today = date.today()
        # Published Tournament so it's visible to all
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system='Sum all round scores',
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           is_published=True,
                                           seed_games=False,
                                           format = Formats.VFTF)
        cls.r11 = Round.objects.create(tournament=cls.t1,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=datetime.combine(cls.t1.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        # Add TournamentPlayers
        TournamentPlayer.objects.create(player=cls.p1,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p2,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p3,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p4,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p5,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p6,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p7,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p8,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p9,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p10,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p11,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p12,
                                        tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p13,
                                        tournament=cls.t1)
        # And RoundPlayers
        cls.rp11 = RoundPlayer.objects.create(player=cls.p1, the_round=cls.r11)
        cls.rp12 = RoundPlayer.objects.create(player=cls.p2, the_round=cls.r11)
        cls.rp13 = RoundPlayer.objects.create(player=cls.p3, the_round=cls.r11)
        cls.rp14 = RoundPlayer.objects.create(player=cls.p4, the_round=cls.r11)
        cls.rp15 = RoundPlayer.objects.create(player=cls.p5, the_round=cls.r11)
        cls.rp16 = RoundPlayer.objects.create(player=cls.p6, the_round=cls.r11)
        cls.rp17 = RoundPlayer.objects.create(player=cls.p7, the_round=cls.r11)
        cls.rp18 = RoundPlayer.objects.create(player=cls.p8, the_round=cls.r11)
        cls.rp19 = RoundPlayer.objects.create(player=cls.p9, the_round=cls.r11)
        cls.rp110 = RoundPlayer.objects.create(player=cls.p10, the_round=cls.r11)
        cls.rp111 = RoundPlayer.objects.create(player=cls.p11, the_round=cls.r11)
        cls.rp112 = RoundPlayer.objects.create(player=cls.p12, the_round=cls.r11, game_count=0)
        cls.rp113 = RoundPlayer.objects.create(player=cls.p13, the_round=cls.r11, game_count=2)

        # Published Tournament so it's visible to all. PREFERENCES power assignment
        cls.t2 = Tournament.objects.create(name='t2',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system='Sum all round scores',
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           power_assignment=PowerAssignMethods.PREFERENCES,
                                           is_published=True)
        cls.r21 = Round.objects.create(tournament=cls.t2,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=datetime.combine(cls.t2.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        cls.r22 = Round.objects.create(tournament=cls.t2,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=cls.r21.start + timedelta(hours=24))
        cls.r23 = Round.objects.create(tournament=cls.t2,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=cls.r21.start + timedelta(hours=48))
        TournamentPlayer.objects.create(player=cls.p1,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=cls.p2,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=cls.p3,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=cls.p4,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=cls.p5,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=cls.p6,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=cls.p7,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=cls.p8,
                                        tournament=cls.t2)
        TournamentPlayer.objects.create(player=cls.p9,
                                        tournament=cls.t2)
        # First Round has no RoundPlayers
        # Second Round has only 6 RoundPlayers
        RoundPlayer.objects.create(player=cls.p3, the_round=cls.r22)
        RoundPlayer.objects.create(player=cls.p4, the_round=cls.r22)
        RoundPlayer.objects.create(player=cls.p5, the_round=cls.r22)
        RoundPlayer.objects.create(player=cls.p6, the_round=cls.r22)
        RoundPlayer.objects.create(player=cls.p7, the_round=cls.r22)
        RoundPlayer.objects.create(player=cls.p8, the_round=cls.r22)
        # Third Round has exactly seven RoundPlayers
        cls.rp21 = RoundPlayer.objects.create(player=cls.p1, the_round=cls.r23)
        cls.rp23 = RoundPlayer.objects.create(player=cls.p3, the_round=cls.r23)
        cls.rp24 = RoundPlayer.objects.create(player=cls.p4, the_round=cls.r23)
        cls.rp25 = RoundPlayer.objects.create(player=cls.p5, the_round=cls.r23)
        cls.rp26 = RoundPlayer.objects.create(player=cls.p6, the_round=cls.r23)
        cls.rp27 = RoundPlayer.objects.create(player=cls.p7, the_round=cls.r23)
        cls.rp28 = RoundPlayer.objects.create(player=cls.p8, the_round=cls.r23)

        # Published Tournament so it's visible to all. AUTO power assignment
        cls.t3 = Tournament.objects.create(name='t3',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system='Sum all round scores',
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           power_assignment=PowerAssignMethods.AUTO,
                                           is_published=True,
                                           seed_games=True)
        cls.r31 = Round.objects.create(tournament=cls.t3,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=datetime.combine(cls.t3.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        cls.r32 = Round.objects.create(tournament=cls.t3,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=cls.r31.start + timedelta(hours=24))
        TournamentPlayer.objects.create(player=cls.p1,
                                        tournament=cls.t3)
        cls.tp2 = TournamentPlayer.objects.create(player=cls.p2,
                                                  tournament=cls.t3)
        cls.tp3 = TournamentPlayer.objects.create(player=cls.p3,
                                                  tournament=cls.t3)
        TournamentPlayer.objects.create(player=cls.p4,
                                        tournament=cls.t3)
        TournamentPlayer.objects.create(player=cls.p5,
                                        tournament=cls.t3)
        TournamentPlayer.objects.create(player=cls.p6,
                                        tournament=cls.t3)
        TournamentPlayer.objects.create(player=cls.p7,
                                        tournament=cls.t3)
        TournamentPlayer.objects.create(player=cls.p8,
                                        tournament=cls.t3)
        TournamentPlayer.objects.create(player=cls.p9,
                                        tournament=cls.t3)
        # Add SeederBias for a pair of players
        SeederBias.objects.create(player1=cls.tp2, player2=cls.tp3)
        # First Round has exactly seven RoundPlayers
        RoundPlayer.objects.create(player=cls.p1, the_round=cls.r31)
        RoundPlayer.objects.create(player=cls.p3, the_round=cls.r31)
        RoundPlayer.objects.create(player=cls.p4, the_round=cls.r31)
        RoundPlayer.objects.create(player=cls.p5, the_round=cls.r31)
        RoundPlayer.objects.create(player=cls.p6, the_round=cls.r31)
        RoundPlayer.objects.create(player=cls.p7, the_round=cls.r31)
        RoundPlayer.objects.create(player=cls.p8, the_round=cls.r31)
        # Second Round has eight RoundPlayers, one sitting out
        RoundPlayer.objects.create(player=cls.p1, the_round=cls.r32)
        RoundPlayer.objects.create(player=cls.p3, the_round=cls.r32)
        RoundPlayer.objects.create(player=cls.p4, the_round=cls.r32)
        RoundPlayer.objects.create(player=cls.p5, the_round=cls.r32)
        RoundPlayer.objects.create(player=cls.p6, the_round=cls.r32)
        RoundPlayer.objects.create(player=cls.p7, the_round=cls.r32)
        RoundPlayer.objects.create(player=cls.p8, the_round=cls.r32, game_count=0)
        RoundPlayer.objects.create(player=cls.p9, the_round=cls.r32)
        # Add a single Game to the first Round
        g = Game.objects.create(name='T3R1G1',
                                started_at=cls.r31.start,
                                is_finished=True,
                                the_round=cls.r31,
                                the_set=GameSet.objects.get(name='Avalon Hill'))
        GamePlayer.objects.create(player=cls.p1, game=g, power=cls.turkey)
        GamePlayer.objects.create(player=cls.p3, game=g, power=cls.russia)
        GamePlayer.objects.create(player=cls.p4, game=g, power=cls.italy)
        GamePlayer.objects.create(player=cls.p5, game=g, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=g, power=cls.france)
        GamePlayer.objects.create(player=cls.p7, game=g, power=cls.england)
        GamePlayer.objects.create(player=cls.p8, game=g, power=cls.austria)
        cls.r31.set_is_finished()

        # Published Tournament so it's visible to all. AUTO power assignment
        cls.t4 = Tournament.objects.create(name='t4',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system='Sum all round scores',
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           power_assignment=PowerAssignMethods.AUTO,
                                           is_published=True,
                                           seed_games=True)
        cls.r41 = Round.objects.create(tournament=cls.t4,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=datetime.combine(cls.t4.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        TournamentPlayer.objects.create(player=cls.p1,
                                        tournament=cls.t4)
        TournamentPlayer.objects.create(player=cls.p2,
                                        tournament=cls.t4)
        TournamentPlayer.objects.create(player=cls.p3,
                                        tournament=cls.t4)
        TournamentPlayer.objects.create(player=cls.p4,
                                        tournament=cls.t4)
        TournamentPlayer.objects.create(player=cls.p5,
                                        tournament=cls.t4)
        TournamentPlayer.objects.create(player=cls.p6,
                                        tournament=cls.t4)
        TournamentPlayer.objects.create(player=cls.p7,
                                        tournament=cls.t4)
        TournamentPlayer.objects.create(player=cls.p8,
                                        tournament=cls.t4)
        TournamentPlayer.objects.create(player=cls.p9,
                                        tournament=cls.t4)
        # Round has eight RoundPlayers, 6 playing two games
        RoundPlayer.objects.create(player=cls.p1, the_round=cls.r41)
        RoundPlayer.objects.create(player=cls.p3, the_round=cls.r41, game_count=2)
        RoundPlayer.objects.create(player=cls.p4, the_round=cls.r41, game_count=2)
        RoundPlayer.objects.create(player=cls.p5, the_round=cls.r41, game_count=2)
        RoundPlayer.objects.create(player=cls.p6, the_round=cls.r41, game_count=2)
        RoundPlayer.objects.create(player=cls.p7, the_round=cls.r41, game_count=2)
        RoundPlayer.objects.create(player=cls.p8, the_round=cls.r41, game_count=2)
        RoundPlayer.objects.create(player=cls.p9, the_round=cls.r41)
        # Add two finished Games to the Round
        g1 = Game.objects.create(name='T4R1G1',
                                 started_at=cls.r41.start,
                                 is_finished=True,
                                 the_round=cls.r41,
                                 the_set=GameSet.objects.get(name='Avalon Hill'))
        GamePlayer.objects.create(player=cls.p1, game=g1, power=cls.turkey, score=1)
        GamePlayer.objects.create(player=cls.p3, game=g1, power=cls.russia, score=2)
        GamePlayer.objects.create(player=cls.p4, game=g1, power=cls.italy, score=3)
        GamePlayer.objects.create(player=cls.p5, game=g1, power=cls.germany, score=4)
        GamePlayer.objects.create(player=cls.p6, game=g1, power=cls.france, score=5)
        GamePlayer.objects.create(player=cls.p7, game=g1, power=cls.england, score=6)
        GamePlayer.objects.create(player=cls.p8, game=g1, power=cls.austria, score=7)
        g2 = Game.objects.create(name='T4R1G2',
                                 started_at=cls.r41.start,
                                 is_finished=True,
                                 the_round=cls.r41,
                                 the_set=GameSet.objects.get(name='Avalon Hill'))
        GamePlayer.objects.create(player=cls.p3, game=g2, power=cls.turkey, score=1)
        GamePlayer.objects.create(player=cls.p4, game=g2, power=cls.russia, score=2)
        GamePlayer.objects.create(player=cls.p5, game=g2, power=cls.italy, score=3)
        GamePlayer.objects.create(player=cls.p6, game=g2, power=cls.germany, score=4)
        GamePlayer.objects.create(player=cls.p7, game=g2, power=cls.france, score=5)
        GamePlayer.objects.create(player=cls.p8, game=g2, power=cls.england, score=6)
        GamePlayer.objects.create(player=cls.p9, game=g2, power=cls.austria, score=7)
        cls.r41.set_is_finished()

    def test_detail(self):
        response = self.client.get(reverse('round_detail',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_detail_non_existant_round(self):
        response = self.client.get(reverse('round_detail',
                                           args=(self.t1.pk, 2)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_board_call_csv(self):
        response = self.client.get(reverse('board_call_csv',
                                           args=(self.t4.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_board_call_csv_no_powers(self):
        r = self.t4.round_numbered(1)
        g = r.game_set.first()
        powers = {}
        for gp in g.gameplayer_set.all():
            powers[gp] = gp.power
            gp.power = None
            gp.save(update_fields=['power'])
        response = self.client.get(reverse('board_call_csv',
                                           args=(self.t4.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Clean up
        for gp, power in powers.items():
            gp.power = power
            gp.save(update_fields=['power'])

    def test_game_cycle_no_games(self):
        response = self.client.get(reverse('round_sc_graphs',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_game_cycle_one_game(self):
        response = self.client.get(reverse('round_sc_graphs',
                                           args=(self.t3.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Should redirect to itself
        self.assertContains(response, 'sc_graphs/T3R1G1/')

    def test_game_cycle_two_games(self):
        response = self.client.get(reverse('round_sc_graphs',
                                           args=(self.t4.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Should redirect to game 2
        self.assertContains(response, 'sc_graphs/T4R1G2/')
        response = self.client.get(reverse('round_sc_graphs_from_game',
                                           args=(self.t4.pk, 1, 'T4R1G2')),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Should redirect back to game 1
        self.assertContains(response, 'sc_graphs/T4R1G1/')

    def test_game_cycle_invalid_game(self):
        response = self.client.get(reverse('round_sc_graphs_from_game',
                                           args=(self.t4.pk, 1, 'T4R1G3')),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_roll_call_not_logged_in(self):
        response = self.client.get(reverse('round_roll_call',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)

    def test_roll_call_one_round(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('round_roll_call',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_roll_call_post_current_round_no_seeding(self):
        """roll_call() POST for t1, which only has a single Round"""
        self.assertEqual(self.t1.current_round().number(), 1)
        self.assertIs(False, self.t1.seed_games)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # These are the existing 13 RoundPlayers, plus one new one and one blank
        data = urlencode({'form-TOTAL_FORMS': '15',
                          'form-INITIAL_FORMS': '13',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-MIN_NUM_FORMS': '0',
                          'form-0-player': str(self.p1.pk),
                          'form-1-player': str(self.p2.pk),
                          'form-1-present': 'ok',
                          'form-2-player': str(self.p3.pk),
                          'form-2-present': 'ok',
                          'form-3-player': str(self.p4.pk),
                          'form-4-player': str(self.p5.pk),
                          'form-5-player': str(self.p6.pk),
                          'form-6-player': str(self.p7.pk),
                          'form-7-player': str(self.p8.pk),
                          'form-8-player': str(self.p9.pk),
                          'form-9-player': str(self.p10.pk),
                          'form-10-player': str(self.p11.pk),
                          'form-11-player': str(self.p12.pk),
                          'form-12-player': str(self.p13.pk),
                          'form-13-player': str(self.p14.pk),
                          'form-13-present': 'ok',
                          'form-14-player': ''})
        response = self.client.post(reverse('round_roll_call', args=(self.t1.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the create games page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('create_games', args=(self.t1.pk, 1)))
        # Check that TournamentPlayers and RoundPlayers were created and deleted correctly
        tp_qs = TournamentPlayer.objects.filter(player=self.p14)
        self.assertTrue(tp_qs.exists())
        self.assertEqual(self.r11.roundplayer_set.count(), 3)
        for rp in self.r11.roundplayer_set.all():
            self.assertIn(rp.player, [self.p2, self.p3, self.p14])
        # Clean up
        tp_qs.delete()
        self.r11.roundplayer_set.filter(player=self.p14).delete()
        self.rp11 = RoundPlayer.objects.create(player=self.p1, the_round=self.r11)
        self.rp14 = RoundPlayer.objects.create(player=self.p4, the_round=self.r11)
        self.rp15 = RoundPlayer.objects.create(player=self.p5, the_round=self.r11)
        self.rp16 = RoundPlayer.objects.create(player=self.p6, the_round=self.r11)
        self.rp17 = RoundPlayer.objects.create(player=self.p7, the_round=self.r11)
        self.rp18 = RoundPlayer.objects.create(player=self.p8, the_round=self.r11)
        self.rp19 = RoundPlayer.objects.create(player=self.p9, the_round=self.r11)
        self.rp110 = RoundPlayer.objects.create(player=self.p10, the_round=self.r11)
        self.rp111 = RoundPlayer.objects.create(player=self.p11, the_round=self.r11)
        self.rp112 = RoundPlayer.objects.create(player=self.p12, the_round=self.r11, game_count=0)
        self.rp113 = RoundPlayer.objects.create(player=self.p13, the_round=self.r11, game_count=2)

    def test_roll_call_post_current_round_with_seeding(self):
        """roll_call POST for current round of a tournament with seeding"""
        self.assertEqual(self.t3.current_round().number(), 2)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # TODO Why doesn't this work?
        #data = urlencode({'form-TOTAL_FORMS': '10',
        data = urlencode({'form-TOTAL_FORMS': '8',
                          'form-INITIAL_FORMS': '8',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-MIN_NUM_FORMS': '0',
                          'form-0-player': str(self.p1.pk),
                          'form-0-present': 'ok',
                          'form-1-player': str(self.p3.pk),
                          'form-1-present': 'ok',
                          'form-2-player': str(self.p4.pk),
                          'form-2-present': 'ok',
                          'form-3-player': str(self.p5.pk),
                          'form-3-present': 'ok',
                          'form-4-player': str(self.p6.pk),
                          'form-4-present': 'ok',
                          'form-5-player': str(self.p7.pk),
                          'form-5-present': 'ok',
                          'form-6-player': str(self.p8.pk),
                          'form-6-present': 'ok',
                          'form-7-player': str(self.p9.pk),
                          'form-7-present': 'ok',
                          'form-8-player': '',
                          'form-8-present': '',
                          'form-9-player': '',
                          'form-9-present': ''})
        response = self.client.post(reverse('round_roll_call', args=(self.t3.pk, 2)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the get seven page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('get_seven', args=(self.t3.pk, 2)))
        # No clean up needed because we left the same 8 players playing

    def test_roll_call_post_current_round_with_pools(self):
        """roll_call POST for current round of a tournament with pools"""
        r = self.t3.current_round()
        self.assertEqual(r.number(), 2)
        pool1 = Pool.objects.create(the_round=r,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=r,
                                    name='Variable')
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # TODO Why doesn't this work?
        #data = urlencode({'form-TOTAL_FORMS': '10',
        data = urlencode({'form-TOTAL_FORMS': '8',
                          'form-INITIAL_FORMS': '8',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-MIN_NUM_FORMS': '0',
                          'form-0-player': str(self.p1.pk),
                          'form-0-present': 'ok',
                          'form-1-player': str(self.p3.pk),
                          'form-1-present': 'ok',
                          'form-2-player': str(self.p4.pk),
                          'form-2-present': 'ok',
                          'form-3-player': str(self.p5.pk),
                          'form-3-present': 'ok',
                          'form-4-player': str(self.p6.pk),
                          'form-4-present': 'ok',
                          'form-5-player': str(self.p7.pk),
                          'form-5-present': 'ok',
                          'form-6-player': str(self.p8.pk),
                          'form-6-present': 'ok',
                          'form-7-player': str(self.p9.pk),
                          'form-7-present': 'ok',
                          'form-8-player': '',
                          'form-8-present': '',
                          'form-9-player': '',
                          'form-9-present': ''})
        response = self.client.post(reverse('round_roll_call', args=(self.t3.pk, 2)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the populate pools page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('populate_pools', args=(self.t3.pk, 2)))
        # No clean up needed because we left the same 8 players playing

    def test_roll_call_post_old_round(self):
        """POST of roll_call() for a Round that is finished"""
        self.assertIs(True, self.t3.round_numbered(1).is_finished)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # TODO Why doesn't this work?
        #data = urlencode({'form-TOTAL_FORMS': '9',
        # This just confirms the actual players.
        # Note that one who didn't play is flagged as "not present"
        data = urlencode({'form-TOTAL_FORMS': '8',
                          'form-INITIAL_FORMS': '7',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-MIN_NUM_FORMS': '0',
                          'form-0-player': str(self.p1.pk),
                          'form-0-present': 'ok',
                          'form-1-player': str(self.p3.pk),
                          'form-1-present': 'ok',
                          'form-2-player': str(self.p4.pk),
                          'form-2-present': 'ok',
                          'form-3-player': str(self.p5.pk),
                          'form-3-present': 'ok',
                          'form-4-player': str(self.p6.pk),
                          'form-4-present': 'ok',
                          'form-5-player': str(self.p7.pk),
                          'form-5-present': 'ok',
                          'form-6-player': str(self.p8.pk),
                          'form-6-present': 'ok',
                          'form-7-player': str(self.p2.pk),
                          'form-7-present': '',
                          'form-8-player': '',
                          'form-8-present': ''})
        url = reverse('round_roll_call', args=(self.t3.pk, 1))
        response = self.client.post(url,
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # Should still redirect to the get seven page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('get_seven', args=(self.t3.pk, 1)))
        # No clean up needed because we left the same 7 players playing

    def test_roll_call_post_old_round_refuse_delete(self):
        """POST of roll_call() for a Round that is finished, trying to delete a player who played a game"""
        r = self.t3.round_numbered(1)
        self.assertIs(True, r.is_finished)
        self.assertTrue(GamePlayer.objects.filter(game__the_round=r, player=self.p3).exists())
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # TODO Why doesn't this work?
        #data = urlencode({'form-TOTAL_FORMS': '9',
        data = urlencode({'form-TOTAL_FORMS': '7',
                          'form-INITIAL_FORMS': '7',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-MIN_NUM_FORMS': '0',
                          'form-0-player': str(self.p1.pk),
                          'form-0-present': 'ok',
                          'form-1-player': str(self.p3.pk),
                          'form-1-present': '',
                          'form-2-player': str(self.p4.pk),
                          'form-2-present': 'ok',
                          'form-3-player': str(self.p5.pk),
                          'form-3-present': 'ok',
                          'form-4-player': str(self.p6.pk),
                          'form-4-present': 'ok',
                          'form-5-player': str(self.p7.pk),
                          'form-5-present': 'ok',
                          'form-6-player': str(self.p8.pk),
                          'form-6-present': 'ok',
                          'form-7-player': str(self.p9.pk),
                          'form-7-present': 'ok',
                          'form-8-player': '',
                          'form-8-present': ''})
        response = self.client.post(reverse('round_roll_call', args=(self.t3.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertContains(response, ' did play this round')
        self.assertTrue(GamePlayer.objects.filter(game__the_round=r, player=self.p3).exists())
        # Clean up
        GamePlayer.objects.filter(game__the_round=r, player=self.p9).delete()

    def test_roll_call_post_add_duplicate_player(self):
        """POST of roll_call() where we add a TournamentPlayer who's already playing"""
        self.assertIs(True, self.t3.round_numbered(1).is_finished)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # TODO Why doesn't this work?
        #data = urlencode({'form-TOTAL_FORMS': '9',
        data = urlencode({'form-TOTAL_FORMS': '8',
                          'form-INITIAL_FORMS': '7',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-MIN_NUM_FORMS': '0',
                          'form-0-player': str(self.p1.pk),
                          'form-0-present': 'ok',
                          'form-1-player': str(self.p3.pk),
                          'form-1-present': 'ok',
                          'form-2-player': str(self.p4.pk),
                          'form-2-present': 'ok',
                          'form-3-player': str(self.p5.pk),
                          'form-3-present': 'ok',
                          'form-4-player': str(self.p6.pk),
                          'form-4-present': 'ok',
                          'form-5-player': str(self.p7.pk),
                          'form-5-present': 'ok',
                          'form-6-player': str(self.p8.pk),
                          'form-6-present': 'ok',
                          'form-7-player': str(self.p3.pk),
                          'form-7-present': 'ok',
                          'form-8-player': '',
                          'form-8-present': ''})
        url = reverse('round_roll_call', args=(self.t3.pk, 1))
        response = self.client.post(url,
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # There should be a validation error for the last player
        self.assertContains(response, 'appears more than once')
        # Should re-load the same page
        self.assertEqual(response.context['post_url'], url)
        # No clean up needed because there was an error

    def test_get_seven_not_logged_in(self):
        response = self.client.get(reverse('get_seven',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)

    def test_get_seven(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('get_seven',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_get_seven_too_few_players(self):
        """Nothing we can do if have fewer than seven players"""
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('get_seven',
                                           args=(self.t2.pk, 2)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tournament_players', args=(self.t2.pk,)))

    def test_get_seven_good_number(self):
        """No action needed if we have an exact multiple of seven players"""
        self.assertEqual(self.t2.round_numbered(3).roundplayer_set.count(), 7)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('get_seven',
                                           args=(self.t2.pk, 3)),
                                   secure=True)
        # We should still get the "get seven" page
        self.assertEqual(response.status_code, 200)

    def test_get_seven_sitters(self):
        """get_seven where we specify people sitting out"""
        # Remember the game_counts
        initial_values = {}
        for rp in self.r11.roundplayer_set.all():
            initial_values[rp] = rp.game_count
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = urlencode({'sitter_0': str(self.rp12.pk),
                          'sitter_1': str(self.rp13.pk),
                          'sitter_2': str(self.rp14.pk),
                          'sitter_3': str(self.rp15.pk),
                          'sitter_4': str(self.rp16.pk),
                          'sitter_5': str(self.rp17.pk)})
        response = self.client.post(reverse('get_seven', args=(self.t1.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('seed_games', args=(self.t1.pk, 1)))
        # Check that the game_counts have been updated accordingly
        self.rp11.refresh_from_db()
        self.assertEqual(self.rp11.game_count, 1)
        self.rp12.refresh_from_db()
        self.assertEqual(self.rp12.game_count, 0)
        self.rp13.refresh_from_db()
        self.assertEqual(self.rp13.game_count, 0)
        self.rp14.refresh_from_db()
        self.assertEqual(self.rp14.game_count, 0)
        self.rp15.refresh_from_db()
        self.assertEqual(self.rp15.game_count, 0)
        self.rp16.refresh_from_db()
        self.assertEqual(self.rp16.game_count, 0)
        self.rp17.refresh_from_db()
        self.assertEqual(self.rp17.game_count, 0)
        self.rp18.refresh_from_db()
        self.assertEqual(self.rp18.game_count, 1)
        self.rp19.refresh_from_db()
        self.assertEqual(self.rp19.game_count, 1)
        self.rp110.refresh_from_db()
        self.assertEqual(self.rp110.game_count, 1)
        self.rp111.refresh_from_db()
        self.assertEqual(self.rp111.game_count, 1)
        self.rp112.refresh_from_db()
        self.assertEqual(self.rp112.game_count, 1)
        self.rp113.refresh_from_db()
        self.assertEqual(self.rp113.game_count, 1)
        # Clean up
        for rp in self.r11.roundplayer_set.all():
            rp.game_count = initial_values[rp]
            rp.save(update_fields=['game_count'])

    def test_get_seven_doublers(self):
        """get_seven where we specify people playing two games"""
        # Remember the game_counts
        initial_values = {}
        for rp in self.r11.roundplayer_set.all():
            initial_values[rp] = rp.game_count
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = urlencode({'double_0': str(self.rp12.pk)})
        response = self.client.post(reverse('get_seven', args=(self.t1.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('seed_games', args=(self.t1.pk, 1)))
        # Check that the game_counts have been updated accordingly
        self.rp11.refresh_from_db()
        self.assertEqual(self.rp11.game_count, 1)
        self.rp12.refresh_from_db()
        self.assertEqual(self.rp12.game_count, 2)
        self.rp13.refresh_from_db()
        self.assertEqual(self.rp13.game_count, 1)
        self.rp14.refresh_from_db()
        self.assertEqual(self.rp14.game_count, 1)
        self.rp15.refresh_from_db()
        self.assertEqual(self.rp15.game_count, 1)
        self.rp16.refresh_from_db()
        self.assertEqual(self.rp16.game_count, 1)
        self.rp17.refresh_from_db()
        self.assertEqual(self.rp17.game_count, 1)
        self.rp18.refresh_from_db()
        self.assertEqual(self.rp18.game_count, 1)
        self.rp19.refresh_from_db()
        self.assertEqual(self.rp19.game_count, 1)
        self.rp110.refresh_from_db()
        self.assertEqual(self.rp110.game_count, 1)
        self.rp111.refresh_from_db()
        self.assertEqual(self.rp111.game_count, 1)
        self.rp112.refresh_from_db()
        self.assertEqual(self.rp112.game_count, 1)
        self.rp113.refresh_from_db()
        self.assertEqual(self.rp113.game_count, 1)
        # Clean up
        for rp in self.r11.roundplayer_set.all():
            rp.game_count = initial_values[rp]
            rp.save(update_fields=['game_count'])

    def test_get_seven_standbys(self):
        """Check that we can fill a game with standby players"""
        self.assertEqual(RoundPlayer.objects.filter(the_round=self.r11, standby=True).count(), 0)
        # Set it up so we have 5 players and 8 standbys
        self.rp11.standby = True
        self.rp11.save(update_fields=['standby'])
        self.rp12.standby = True
        self.rp12.save(update_fields=['standby'])
        self.rp14.standby = True
        self.rp14.save(update_fields=['standby'])
        self.rp15.standby = True
        self.rp15.save(update_fields=['standby'])
        self.rp18.standby = True
        self.rp18.save(update_fields=['standby'])
        self.rp110.standby = True
        self.rp110.save(update_fields=['standby'])
        self.rp111.standby = True
        self.rp111.save(update_fields=['standby'])
        self.rp112.standby = True
        self.rp112.save(update_fields=['standby'])
        # Remember the game_counts
        initial_values = {}
        for rp in self.r11.roundplayer_set.all():
            initial_values[rp] = rp.game_count
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = urlencode({'standby_0': str(self.rp12.pk),
                          'standby_1': str(self.rp18.pk),
                          })
        response = self.client.post(reverse('get_seven', args=(self.t1.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('seed_games', args=(self.t1.pk, 1)))
        # Check that the game_counts have been updated accordingly
        self.rp11.refresh_from_db()
        self.assertEqual(self.rp11.game_count, 0)
        self.rp12.refresh_from_db()
        self.assertEqual(self.rp12.game_count, 1)
        self.rp13.refresh_from_db()
        self.assertEqual(self.rp13.game_count, 1)
        self.rp14.refresh_from_db()
        self.assertEqual(self.rp14.game_count, 0)
        self.rp15.refresh_from_db()
        self.assertEqual(self.rp15.game_count, 0)
        self.rp16.refresh_from_db()
        self.assertEqual(self.rp16.game_count, 1)
        self.rp17.refresh_from_db()
        self.assertEqual(self.rp17.game_count, 1)
        self.rp18.refresh_from_db()
        self.assertEqual(self.rp18.game_count, 1)
        self.rp19.refresh_from_db()
        self.assertEqual(self.rp19.game_count, 1)
        self.rp110.refresh_from_db()
        self.assertEqual(self.rp110.game_count, 0)
        self.rp111.refresh_from_db()
        self.assertEqual(self.rp111.game_count, 0)
        self.rp112.refresh_from_db()
        self.assertEqual(self.rp112.game_count, 0)
        self.rp113.refresh_from_db()
        self.assertEqual(self.rp113.game_count, 1)
        # Clean up
        for rp in self.r11.roundplayer_set.all():
            rp.game_count = initial_values[rp]
            rp.standby = False
            rp.save(update_fields=['standby'])

    def test_get_seven_with_pools_fixed_pool_right(self):
        """get_seven for a round with pools"""
        # Remember the game_counts
        initial_values = {}
        for rp in self.r11.roundplayer_set.all():
            initial_values[rp] = rp.game_count
        pool1 = Pool.objects.create(the_round=self.r11,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r11,
                                    name='Variable')
        # Assign players to pools
        # Correct number in the fixed pool
        for rp in [self.rp11, self.rp12, self.rp13, self.rp14, self.rp15, self.rp16, self.rp17]:
            rp.pool = pool1
            rp.save()
        # Remainder in the variable pool - too few for a game
        for rp in [self.rp18, self.rp19, self.rp110, self.rp111, self.rp112, self.rp113]:
            rp.pool = pool2
            rp.save()
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = urlencode({'double_0': str(self.rp12.pk)})
        response = self.client.post(reverse('get_seven', args=(self.t1.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tournament_players', args=(self.t1.pk,)))
        # Clean up
        for rp in self.r11.roundplayer_set.all():
            rp.pool = None
            rp.game_count = initial_values[rp]
            rp.save(update_fields=['game_count'])
        self.r11.pool_set.all().delete()

    def test_get_seven_with_pools_fixed_pool_wrong(self):
        """get_seven for a round with pools"""
        # Remember the game_counts
        initial_values = {}
        for rp in self.r11.roundplayer_set.all():
            initial_values[rp] = rp.game_count
        pool1 = Pool.objects.create(the_round=self.r11,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r11,
                                    name='Variable')
        # Assign players to pools
        # Too few in the fixed pool
        for rp in [self.rp11, self.rp12, self.rp13, self.rp14, self.rp15, self.rp16]:
            rp.pool = pool1
            rp.save()
        # Remainder in the variable pool
        for rp in [self.rp17, self.rp18, self.rp19, self.rp110, self.rp111, self.rp112, self.rp113]:
            rp.pool = pool2
            rp.save()
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = urlencode({'double_0': str(self.rp12.pk)})
        response = self.client.post(reverse('get_seven', args=(self.t1.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('populate_pools', args=(self.t1.pk, 1)))
        # Clean up
        for rp in self.r11.roundplayer_set.all():
            rp.pool = None
            rp.game_count = initial_values[rp]
            rp.save(update_fields=['game_count'])
        self.r11.pool_set.all().delete()

    def test_populate_pools_not_logged_in(self):
        response = self.client.get(reverse('populate_pools',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)

    def test_populate_pools_no_pools(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('populate_pools',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_populate_pools(self):
        pool1 = Pool.objects.create(the_round=self.r11,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r11,
                                    name='Variable')
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('populate_pools',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Cleanup
        self.r11.pool_set.all().delete()

    def test_populate_too_few_pools(self):
        pool1 = Pool.objects.create(the_round=self.r11,
                                    name='Variable')
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        with self.assertRaises(Pool.DoesNotExist):
            response = self.client.get(reverse('populate_pools',
                                               args=(self.t1.pk, 1)),
                                       secure=True)
        # Cleanup
        self.r11.pool_set.all().delete()

    def test_populate_too_many_pools(self):
        pool1 = Pool.objects.create(the_round=self.r11,
                                    name='Fixed1',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r11,
                                    name='Fixed2',
                                    board_count=1)
        pool3 = Pool.objects.create(the_round=self.r11,
                                    name='Variable')
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        with self.assertRaises(Pool.MultipleObjectsReturned):
            response = self.client.get(reverse('populate_pools',
                                               args=(self.t1.pk, 1)),
                                       secure=True)
        # Cleanup
        self.r11.pool_set.all().delete()

    def test_populate_pools_post(self):
        rp13_game_count = self.rp13.game_count
        self.rp13.game_count = 0
        self.rp13.save()
        # Seven players for the fixed pool
        fixed_players = [self.rp12, self.rp13, self.rp16, self.rp17, self.rp19, self.rp110, self.rp113]
        pool1 = Pool.objects.create(the_round=self.r11,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r11,
                                    name='Variable')
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = {}
        for n, rp in enumerate(fixed_players, start=1):
            data[f'player_{n}'] = str(rp.pk)
        response = self.client.post(reverse('populate_pools', args=(self.t1.pk, 1)),
                                    urlencode(data),
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('get_seven', args=(self.t1.pk, 1)))
        # RoundPlayers should all be assigned to a pool
        # RoundPlayers in the fixed pool should be set to playing one game
        # (they are skipped in the get_seven form)
        for rp in self.r11.roundplayer_set.all():
            if rp in fixed_players:
                self.assertEqual(rp.pool, pool1)
                self.assertEqual(rp.game_count, 1)
            else:
                self.assertEqual(rp.pool, pool2)
        # Cleanup
        self.rp13.game_count = rp13_game_count
        self.rp13.save()
        for rp in self.r11.roundplayer_set.all():
            rp.pool = None
            rp.save()
        self.r11.pool_set.all().delete()

    def test_populate_pools_post_missing_player(self):
        # Seven players for the fixed pool
        fixed_players = [self.rp12, self.rp13, self.rp16, self.rp17, self.rp19, self.rp110, self.rp113]
        pool1 = Pool.objects.create(the_round=self.r11,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r11,
                                    name='Variable')
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = {}
        for n, rp in enumerate(fixed_players, start=1):
            data[f'player_{n}'] = str(rp.pk)
        # Remove one player
        del data['player_4']
        response = self.client.post(reverse('populate_pools', args=(self.t1.pk, 1)),
                                    urlencode(data),
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # All 7 players should be required
        self.assertContains(response, 'This field is required.')
        # No RoundPlayers should be assigned to a pool
        for rp in self.r11.roundplayer_set.all():
            self.assertEqual(rp.pool, None)
        # Cleanup
        self.r11.pool_set.all().delete()

    def test_populate_pools_post_duplicate_player(self):
        # Seven players for the fixed pool
        fixed_players = [self.rp12, self.rp13, self.rp16, self.rp12, self.rp19, self.rp110, self.rp113]
        pool1 = Pool.objects.create(the_round=self.r11,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r11,
                                    name='Variable')
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = {}
        for n, rp in enumerate(fixed_players, start=1):
            data[f'player_{n}'] = str(rp.pk)
        response = self.client.post(reverse('populate_pools', args=(self.t1.pk, 1)),
                                    urlencode(data),
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # Duplicate should be reported as an error
        self.assertContains(response, 'Player Bobby Bandersnatch appears more than once')
        # No RoundPlayers should be assigned to a pool
        for rp in self.r11.roundplayer_set.all():
            self.assertEqual(rp.pool, None)
        # Cleanup
        self.r11.pool_set.all().delete()

    def test_seed_games_not_logged_in(self):
        response = self.client.get(reverse('seed_games',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)

    def test_seed_games_odd_number(self):
        """if we dont have a mutiple of 7 players, this view should redirect to fix that"""
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('get_seven', args=(self.t1.pk, 1)))

    def test_seed_games_preferences_good_number(self):
        """Simple case with exactly seven players with PREFERENCES power assignment"""
        self.assertEqual(self.t2.round_numbered(3).roundplayer_set.count(), 7)
        self.assertEqual(self.t2.round_numbered(3).game_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games',
                                           args=(self.t2.pk, 3)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # A single Game should have been created
        g_qs = self.t2.round_numbered(3).game_set
        self.assertEqual(g_qs.count(), 1)
        # with seven GamePlayers
        g = g_qs.get()
        self.assertEqual(g.gameplayer_set.count(), 7)
        # Clean up
        g.delete()

    def test_seed_games_manual_good_number(self):
        """Simple case with exactly seven players with MANUAL power assignment"""
        self.assertEqual(self.t2.round_numbered(3).roundplayer_set.count(), 7)
        self.assertEqual(self.t2.round_numbered(3).game_set.count(), 0)
        self.assertEqual(self.t2.power_assignment, PowerAssignMethods.PREFERENCES)
        self.t2.power_assignment = PowerAssignMethods.MANUAL
        self.t2.save(update_fields=['power_assignment'])
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games',
                                           args=(self.t2.pk, 3)),
                                   secure=True)
        # Check that the powers are not selected in the form (this also checks for status 200)
        self.assertContains(response, 'option value="" selected')
        # A single Game should have been created
        g_qs = self.t2.round_numbered(3).game_set
        self.assertEqual(g_qs.count(), 1)
        # with seven GamePlayers
        g = g_qs.get()
        self.assertEqual(g.gameplayer_set.count(), 7)
        # And no powers assigned
        for gp in g.gameplayer_set.all():
            self.assertIsNone(gp.power)
        # Clean up
        g.delete()
        self.t2.power_assignment = PowerAssignMethods.PREFERENCES
        self.t2.save(update_fields=['power_assignment'])

    def test_seed_games_auto_good_number_with_sitters(self):
        """Eight players, one sitting out, AUTO power assignment"""
        self.assertEqual(self.r32.game_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games',
                                           args=(self.t3.pk, 2)),
                                   secure=True)
        # Check that the powers are selected in the form (this also checks for status 200)
        self.assertNotContains(response, 'option value="" selected')
        # A single Game should have been created
        g_qs = self.t3.round_numbered(2).game_set
        self.assertEqual(g_qs.count(), 1)
        # with seven GamePlayers
        g = g_qs.get()
        self.assertEqual(g.gameplayer_set.count(), 7)
        # and powers assigned
        for gp in g.gameplayer_set.all():
            self.assertIsNotNone(gp.power)
        # Clean up
        g.delete()

    def test_seed_games_auto_good_number_with_doublers(self):
        """13 players, one playing two games, AUTO power assignment"""
        self.assertEqual(self.r11.game_set.count(), 0)
        # Tweak initial data for this test
        self.rp112.game_count = 1
        self.rp112.save(update_fields=['game_count'])
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        # Check that the powers are selected in the form (this also checks for status 200)
        self.assertNotContains(response, 'option value="" selected')
        # Two Games should have been created
        g_qs = self.t1.round_numbered(1).game_set
        self.assertEqual(g_qs.count(), 2)
        # with seven GamePlayers
        for g in g_qs.all():
            self.assertEqual(g.gameplayer_set.count(), 7)
            # and powers assigned
            for gp in g.gameplayer_set.all():
                self.assertIsNotNone(gp.power)
        # Clean up
        g_qs.all().delete()
        self.rp112.game_count = 0
        self.rp112.save(update_fields=['game_count'])

    def test_seed_games_with_teams(self):
        """14 players, AUTO power assignment"""
        self.assertEqual(self.r11.game_set.count(), 0)
        tp = TournamentPlayer.objects.create(player=self.p14,
                                             tournament=self.t1)
        rp = RoundPlayer.objects.create(player=self.p14,
                                        the_round=self.r11)
        self.assertEqual(self.rp112.game_count, 0)
        self.rp112.game_count = 1
        self.rp112.save(update_fields=['game_count'])
        self.assertEqual(self.rp113.game_count, 2)
        self.rp113.game_count = 1
        self.rp113.save(update_fields=['game_count'])
        # Create two teams
        self.t1.team_size = 2
        self.t1.save(update_fields=['team_size'])
        self.r11.is_team_round = True
        self.r11.save(update_fields=['is_team_round'])
        tm1 = Team.objects.create(tournament=self.t1,
                                  name="Test team 1")
        tm1.players.add(self.p2)
        tm1.players.add(self.p4)
        tm2 = Team.objects.create(tournament=self.t1,
                                  name="Test team 2")
        tm2.players.add(self.p3)
        tm2.players.add(self.p14)
        # Tweak initial data for this test
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        # Check that the powers are selected in the form (this also checks for status 200)
        self.assertNotContains(response, 'option value="" selected')
        # Two Games should have been created
        g_qs = self.t1.round_numbered(1).game_set
        self.assertEqual(g_qs.count(), 2)
        # with seven GamePlayers
        for g in g_qs.all():
            self.assertEqual(g.gameplayer_set.count(), 7)
            # and powers assigned
            for gp in g.gameplayer_set.all():
                self.assertIsNotNone(gp.power)
        # Team members should not be playing each other
        for tm in [tm1, tm2]:
            games = set()
            gps = tm.gameplayers()
            for gp in gps:
                games.add(gp.game)
            self.assertEqual(len(games), len(gps))
        # Clean up
        tm1.delete()
        tm2.delete()
        g_qs.all().delete()
        rp.delete()
        self.rp112.game_count = 0
        self.rp112.save(update_fields=['game_count'])
        self.rp113.game_count = 2
        self.rp113.save(update_fields=['game_count'])
        tp.delete()
        self.r11.is_team_round = False
        self.r11.save(update_fields=['is_team_round'])
        self.t1.team_size = None
        self.t1.save(update_fields=['team_size'])

    def test_seed_games_with_pools(self):
        self.assertEqual(self.t1.power_assignment, PowerAssignMethods.AUTO)
        self.t1.power_assignment = PowerAssignMethods.MANUAL
        self.t1.save()
        r = self.t1.round_numbered(1)
        self.assertFalse(r.game_set.exists())
        tp = TournamentPlayer.objects.create(player=self.p14,
                                             tournament=self.t1)
        new_rp = RoundPlayer.objects.create(player=self.p14,
                                            the_round=self.r11)
        self.assertEqual(self.rp112.game_count, 0)
        self.rp112.game_count = 1
        self.rp112.save(update_fields=['game_count'])
        self.assertEqual(self.rp113.game_count, 2)
        self.rp113.game_count = 1
        self.rp113.save(update_fields=['game_count'])
        pool1 = Pool.objects.create(the_round=r,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=r,
                                    name='Variable')
        for rp in [self.rp11, self.rp13, self.rp15, self.rp17, self.rp19, self.rp111, self.rp113]:
            rp.pool = pool1
            rp.save()
        for rp in [self.rp12, self.rp14, self.rp16, self.rp18, self.rp110, self.rp112, new_rp]:
            rp.pool = pool2
            rp.save()
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        # Form should be for one game in each of the two pools
        self.assertContains(response, 'R1GA')
        self.assertContains(response, 'R1GB')
        # Cleanup
        new_rp.delete()
        tp.delete()
        for rp in r.roundplayer_set.all():
            rp.pool = None
            rp.save()
        r.game_set.all().delete()
        r.pool_set.all().delete()
        self.rp112.game_count = 0
        self.rp112.save(update_fields=['game_count'])
        self.rp113.game_count = 2
        self.rp113.save(update_fields=['game_count'])
        self.t1.power_assignment = PowerAssignMethods.AUTO
        self.t1.save()

    def test_seed_games_and_powers_with_pools(self):
        self.assertEqual(self.t1.power_assignment, PowerAssignMethods.AUTO)
        r = self.t1.round_numbered(1)
        self.assertFalse(r.game_set.exists())
        tp = TournamentPlayer.objects.create(player=self.p14,
                                             tournament=self.t1)
        new_rp = RoundPlayer.objects.create(player=self.p14,
                                            the_round=self.r11)
        self.assertEqual(self.rp112.game_count, 0)
        self.rp112.game_count = 1
        self.rp112.save(update_fields=['game_count'])
        self.assertEqual(self.rp113.game_count, 2)
        self.rp113.game_count = 1
        self.rp113.save(update_fields=['game_count'])
        pool1 = Pool.objects.create(the_round=r,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=r,
                                    name='Variable')
        for rp in [self.rp11, self.rp13, self.rp15, self.rp17, self.rp19, self.rp111, self.rp113]:
            rp.pool = pool1
            rp.save()
        for rp in [self.rp12, self.rp14, self.rp16, self.rp18, self.rp110, self.rp112, new_rp]:
            rp.pool = pool2
            rp.save()
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('seed_games',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        # Form should be for one game in each of the two pools
        self.assertContains(response, 'R1GA')
        self.assertContains(response, 'R1GB')
        # Cleanup
        new_rp.delete()
        tp.delete()
        for rp in r.roundplayer_set.all():
            rp.pool = None
            rp.save()
        r.game_set.all().delete()
        r.pool_set.all().delete()
        self.rp112.game_count = 0
        self.rp112.save(update_fields=['game_count'])
        self.rp113.game_count = 2
        self.rp113.save(update_fields=['game_count'])

    def test_seed_games_post_no_change(self):
        """Just accept the generated seeding"""
        # Eight players, one sitting out, AUTO power assignment
        self.assertEqual(self.r32.game_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # We need the Game to already exist
        g = Game.objects.create(name='T3R2G1',
                                started_at=self.r32.start,
                                is_finished=True,
                                the_round=self.r32,
                                the_set=GameSet.objects.get(name='Avalon Hill'))
        gp1 = GamePlayer.objects.create(player=self.p1, game=g, power=self.turkey)
        gp2 = GamePlayer.objects.create(player=self.p3, game=g, power=self.russia)
        gp3 = GamePlayer.objects.create(player=self.p4, game=g, power=self.italy)
        gp4 = GamePlayer.objects.create(player=self.p5, game=g, power=self.germany)
        gp5 = GamePlayer.objects.create(player=self.p6, game=g, power=self.france)
        gp6 = GamePlayer.objects.create(player=self.p7, game=g, power=self.england)
        gp7 = GamePlayer.objects.create(player=self.p9, game=g, power=self.austria)
        data = {'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '1',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-name': g.name,
                'form-0-the_set': str(g.the_set.pk)}
        for gp in g.gameplayer_set.all():
            data[f'form-0-{gp.pk}'] = str(gp.power.pk)
        data = urlencode(data)
        response = self.client.post(reverse('seed_games', args=(self.t3.pk, 2)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('board_call', args=(self.t3.pk, 2)))
        # TODO Initial game, round, and tournament scores should have been calculated
        for gp in g.gameplayer_set.all():
            self.assertNotEqual(gp.score, 0.0)
        # TODO Check that board call email was sent out
        # Clean up
        g.delete()

    def test_seed_games_post_change_players(self):
        """Change the power assignment"""
        # Eight players, one sitting out, AUTO power assignment
        self.assertEqual(self.r32.game_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # We need the Game to already exist
        g = Game.objects.create(name='T3R2G1',
                                started_at=self.r32.start,
                                is_finished=True,
                                the_round=self.r32,
                                the_set=GameSet.objects.get(name='Avalon Hill'))
        gp1 = GamePlayer.objects.create(player=self.p1, game=g, power=self.turkey)
        gp2 = GamePlayer.objects.create(player=self.p3, game=g, power=self.russia)
        gp3 = GamePlayer.objects.create(player=self.p4, game=g, power=self.italy)
        gp4 = GamePlayer.objects.create(player=self.p5, game=g, power=self.germany)
        gp5 = GamePlayer.objects.create(player=self.p6, game=g, power=self.france)
        gp6 = GamePlayer.objects.create(player=self.p7, game=g, power=self.england)
        gp7 = GamePlayer.objects.create(player=self.p9, game=g, power=self.austria)
        powers = {gp1: self.austria,
                  gp2: self.turkey,
                  gp3: self.england,
                  gp4: self.russia,
                  gp5: self.france,
                  gp6: self.italy,
                  gp7: self.germany}
        data = {'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '1',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-name': g.name,
                'form-0-the_set': str(g.the_set.pk)}
        for gp, p in powers.items():
            data[f'form-0-{gp.pk}'] = str(p.pk)
        data = urlencode(data)
        response = self.client.post(reverse('seed_games', args=(self.t3.pk, 2)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('board_call', args=(self.t3.pk, 2)))
        # And power assignments for the 7 GamePlayers
        for gp, p in powers.items():
            gp.refresh_from_db()
            self.assertEqual(gp.power, p)
        # TODO Check that board call email was sent out
        # Clean up
        g.delete()

    def test_seed_games_post_no_player_change(self):
        """Change something other than the players"""
        # Eight players, one sitting out, AUTO power assignment
        self.assertEqual(self.r32.game_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # We need the Game to already exist
        g = Game.objects.create(name='T3R2G1',
                                started_at=self.r32.start,
                                is_finished=True,
                                the_round=self.r32,
                                the_set=GameSet.objects.get(name='Avalon Hill'))
        gp1 = GamePlayer.objects.create(player=self.p1, game=g, power=self.turkey)
        gp2 = GamePlayer.objects.create(player=self.p3, game=g, power=self.russia)
        gp3 = GamePlayer.objects.create(player=self.p4, game=g, power=self.italy)
        gp4 = GamePlayer.objects.create(player=self.p5, game=g, power=self.germany)
        gp5 = GamePlayer.objects.create(player=self.p6, game=g, power=self.france)
        gp6 = GamePlayer.objects.create(player=self.p7, game=g, power=self.england)
        gp7 = GamePlayer.objects.create(player=self.p9, game=g, power=self.austria)
        data = {'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '1',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-name': 'NewName',
                'form-0-the_set': str(self.gibsons.pk)}
        for gp in g.gameplayer_set.all():
            data[f'form-0-{gp.pk}'] = str(gp.power.pk)
        data = urlencode(data)
        response = self.client.post(reverse('seed_games', args=(self.t3.pk, 2)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('board_call', args=(self.t3.pk, 2)))
        # Check Game name and Set
        g.refresh_from_db()
        self.assertEqual(g.name, 'NewName')
        self.assertEqual(g.the_set, self.gibsons)
        # TODO Check that board call email was sent out
        # Clean up
        g.delete()

    def test_seed_games_post_invalid_game_name(self):
        """Eight players, one sitting out, AUTO power assignment"""
        self.assertEqual(self.r32.game_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # We need the Game to already exist
        g = Game.objects.create(name='T3R2G1',
                                started_at=self.r32.start,
                                is_finished=True,
                                the_round=self.r32,
                                the_set=GameSet.objects.get(name='Avalon Hill'))
        gp1 = GamePlayer.objects.create(player=self.p1, game=g, power=self.turkey)
        gp2 = GamePlayer.objects.create(player=self.p3, game=g, power=self.russia)
        gp3 = GamePlayer.objects.create(player=self.p4, game=g, power=self.italy)
        gp4 = GamePlayer.objects.create(player=self.p5, game=g, power=self.germany)
        gp5 = GamePlayer.objects.create(player=self.p6, game=g, power=self.france)
        gp6 = GamePlayer.objects.create(player=self.p7, game=g, power=self.england)
        gp7 = GamePlayer.objects.create(player=self.p9, game=g, power=self.austria)
        powers = {gp1: self.austria,
                  gp2: self.turkey,
                  gp3: self.england,
                  gp4: self.russia,
                  gp5: self.france,
                  gp6: self.italy,
                  gp7: self.germany}
        data = {'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '1',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-name': 'S P A C E',
                'form-0-the_set': str(self.gibsons.pk)}
        for gp, p in powers.items():
            data[f'form-0-{gp.pk}'] = str(p.pk)
        data = urlencode(data)
        response = self.client.post(reverse('seed_games', args=(self.t3.pk, 2)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        # Check error(s)
        self.assertEqual(len(response.context['formset'].errors[0]['name']), 1)
        self.assertIn('Game names cannot contain ',
                      response.context['formset'].errors[0]['name'][0])
        # Clean up
        g.delete()

    def test_seed_games_post_invalid_power(self):
        """Eight players, one sitting out, AUTO power assignment"""
        self.assertEqual(self.r32.game_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # We need the Game to already exist
        g = Game.objects.create(name='T3R2G1',
                                started_at=self.r32.start,
                                is_finished=True,
                                the_round=self.r32,
                                the_set=GameSet.objects.get(name='Avalon Hill'))
        gp1 = GamePlayer.objects.create(player=self.p1, game=g, power=self.turkey)
        gp2 = GamePlayer.objects.create(player=self.p3, game=g, power=self.russia)
        gp3 = GamePlayer.objects.create(player=self.p4, game=g, power=self.italy)
        gp4 = GamePlayer.objects.create(player=self.p5, game=g, power=self.germany)
        gp5 = GamePlayer.objects.create(player=self.p6, game=g, power=self.france)
        gp6 = GamePlayer.objects.create(player=self.p7, game=g, power=self.england)
        gp7 = GamePlayer.objects.create(player=self.p9, game=g, power=self.austria)
        powers = {gp1: self.austria,
                  gp2: self.turkey,
                  gp3: self.england,
                  gp4: self.russia,
                  gp5: self.france,
                  gp6: self.italy,
                  gp7: self.germany}
        data = {'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '1',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-name': 'NewName',
                'form-0-the_set': str(self.gibsons.pk)}
        for gp, p in powers.items():
            data[f'form-0-{gp.pk}'] = str(p.pk)
        data[f'form-0-{gp5.pk}'] = '99'
        data = urlencode(data)
        response = self.client.post(reverse('seed_games', args=(self.t3.pk, 2)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        # Check error(s)
        self.assertIn('Select a valid choice. That choice is not one of the available choices.',
                      response.context['formset'].errors[0][str(gp5.pk)])
        # Clean up
        g.delete()

    def test_seed_games_post_duplicate_power(self):
        """Eight players, one sitting out, AUTO power assignment"""
        self.assertEqual(self.r32.game_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        # We need the Game to already exist
        g = Game.objects.create(name='T3R2G1',
                                started_at=self.r32.start,
                                is_finished=True,
                                the_round=self.r32,
                                the_set=GameSet.objects.get(name='Avalon Hill'))
        gp1 = GamePlayer.objects.create(player=self.p1, game=g, power=self.turkey)
        gp2 = GamePlayer.objects.create(player=self.p3, game=g, power=self.russia)
        gp3 = GamePlayer.objects.create(player=self.p4, game=g, power=self.italy)
        gp4 = GamePlayer.objects.create(player=self.p5, game=g, power=self.germany)
        gp5 = GamePlayer.objects.create(player=self.p6, game=g, power=self.france)
        gp6 = GamePlayer.objects.create(player=self.p7, game=g, power=self.england)
        gp7 = GamePlayer.objects.create(player=self.p9, game=g, power=self.austria)
        powers = {gp1: self.austria,
                  gp2: self.turkey,
                  gp3: self.england,
                  gp4: self.russia,
                  gp5: self.italy,
                  gp6: self.italy,
                  gp7: self.germany}
        data = {'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '1',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-name': 'NewName',
                'form-0-the_set': str(self.gibsons.pk)}
        for gp, p in powers.items():
            data[f'form-0-{gp.pk}'] = str(p.pk)
        data = urlencode(data)
        response = self.client.post(reverse('seed_games', args=(self.t3.pk, 2)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        # Check error(s)
        self.assertIn('Power Italy appears more than once',
                      response.context['formset'].errors[0]['__all__'])
        # Clean up
        g.delete()

    def test_create_games_not_logged_in(self):
        response = self.client.get(reverse('create_games',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)

    def test_create_games(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('create_games',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_create_games_no_players(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('create_games',
                                           args=(self.t2.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_create_games_when_games_exist(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('create_games',
                                           args=(self.t3.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_create_games_invalid_pool(self):
        r = self.t3.round_numbered(1)
        pool1 = Pool.objects.create(the_round=r,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=r,
                                    name='Variable')
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('create_games_in_pool',
                                           args=(self.t3.pk, 1, 'invalid-pool-slug')),
                                   secure=True)
        self.assertEqual(response.status_code, 404)
        # Cleanup
        r.pool_set.all().delete()

    def test_create_games_in_pool(self):
        r = self.t4.round_numbered(1)
        pool1 = Pool.objects.create(the_round=r,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=r,
                                    name='Variable')
        self.assertEqual(r.game_set.count(), 2)
        # Last game in pool2, rest in pool1
        g1 = r.game_set.first()
        g1.pool = pool2
        g1.save()
        g2 = r.game_set.last()
        g2.pool = pool1
        g2.save()
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('create_games_in_pool',
                                           args=(self.t4.pk, 1, pool1.slug)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # g2 should be in the form, g1 should not
        self.assertNotContains(response, g1.name)
        self.assertContains(response, g2.name)
        # Cleanup
        for g in r.game_set.all():
            g.pool = None
            g.save()
        r.pool_set.all().delete()

    def test_create_games_when_games_exist_powers_unassigned(self):
        r = self.t3.round_numbered(1)
        g = r.game_set.first()
        # Unassign powers to GamePlayers
        powers = {}
        for gp in g.gameplayer_set.all():
            powers[gp] = gp.power
            gp.power = None
            gp.save(update_fields=['power'])
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('create_games',
                                           args=(self.t3.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Clean-up
        for gp in g.gameplayer_set.all():
            gp.power = powers[gp]
            gp.save(update_fields=['power'])

    def test_create_games_post(self):
        """Simple case - no pre-existing Games. Create one"""
        self.assertEqual(self.r11.game_set.count(), 0)
        powers = {self.austria : self.rp11,
                  self.turkey : self.rp12,
                  self.england : self.rp13,
                  self.russia : self.rp15,
                  self.italy : self.rp16,
                  self.france : self.rp17,
                  self.germany : self.rp19}
        URL = 'http://example.com/test.html'
        NOTE = 'New Game notes'
        data = {'form-TOTAL_FORMS': '2',
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-game_id': '',
                'form-0-name': 'NewName',
                'form-0-external_url': URL,
                'form-0-notes': NOTE,
                'form-0-the_set': str(self.gibsons.pk),
                'form-1-game_id': '',
                'form-1-name': '',
                'form-1-external_url': '',
                'form-1-notes': '',
                'form-1-the_set': ''}
        for p, rp in powers.items():
            data[f'form-0-{p.name}'] = str(rp.pk)
            # Include a blank form in the formset
            data[f'form-1-{p.name}'] = ''
        data = urlencode(data)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.post(reverse('create_games', args=(self.t1.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should re-direct to the board call page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('board_call', args=(self.t1.pk, 1)))
        # The one Game should now exist
        self.assertEqual(self.r11.game_set.count(), 1)
        g = self.r11.game_set.get()
        self.assertEqual(g.name, 'NewName')
        self.assertEqual(g.the_set, self.gibsons)
        self.assertEqual(g.external_url, URL)
        self.assertEqual(g.notes, NOTE)
        self.assertEqual(g.gameplayer_set.count(), 7)
        for p, rp in powers.items():
            self.assertEqual(g.gameplayer_set.filter(power=p, player=rp.player).count(), 1)
        # TODO Verify that email is sent
        # Clean up
        self.r11.game_set.all().delete()

    def test_create_games_post_modify_players(self):
        """Change players or power assignments"""
        self.assertEqual(self.r11.game_set.count(), 0)
        powers = {self.austria : self.rp11,
                  self.turkey : self.rp12,
                  self.england : self.rp13,
                  self.russia : self.rp15,
                  self.italy : self.rp16,
                  self.france : self.rp17,
                  self.germany : self.rp19}
        g = Game.objects.create(the_round=self.r11,
                                name='Existing',
                                the_set=self.gibsons,
                                external_url='http://example.com/old.html')
        for p, rp in powers.items():
            # Swap England and Russia
            if p == self.england:
                GamePlayer.objects.create(game=g,
                                          power=self.russia,
                                          player=rp.player)
            elif p == self.russia:
                GamePlayer.objects.create(game=g,
                                          power=self.england,
                                          player=rp.player)
            else:
                GamePlayer.objects.create(game=g,
                                          power=p,
                                          player=rp.player)
        data = {'form-TOTAL_FORMS': '2',
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-game_id': str(g.id),
                'form-0-name': g.name,
                'form-0-external_url': g.external_url,
                'form-0-notes': g.notes,
                'form-0-the_set': str(g.the_set.pk),
                # Include a blank form in the formset
                'form-1-game_id': '',
                'form-1-name': '',
                'form-1-external_url': '',
                'form-1-notes': '',
                'form-1-the_set': ''}
        for p, rp in powers.items():
            data[f'form-0-{p.name}'] = str(rp.pk)
            data[f'form-1-{p.name}'] = ''
        data = urlencode(data)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.post(reverse('create_games', args=(self.t1.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should re-direct to the board call page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('board_call', args=(self.t1.pk, 1)))
        # The one Game should still exist
        self.assertEqual(self.r11.game_set.count(), 1)
        g = self.r11.game_set.get()
        self.assertEqual(g.gameplayer_set.count(), 7)
        for p, rp in powers.items():
            self.assertEqual(g.gameplayer_set.filter(power=p, player=rp.player).count(), 1)
        # TODO Verify that email is sent
        # Clean up
        self.r11.game_set.all().delete()

    def test_create_games_post_modify_non_players(self):
        """Change attributes other than players and power assignments"""
        self.assertEqual(self.r11.game_set.count(), 0)
        powers = {self.austria : self.rp11,
                  self.turkey : self.rp12,
                  self.england : self.rp13,
                  self.russia : self.rp15,
                  self.italy : self.rp16,
                  self.france : self.rp17,
                  self.germany : self.rp19}
        g = Game.objects.create(the_round=self.r11,
                                name='Existing',
                                the_set=self.gibsons,
                                external_url='http://example.com/old.html')
        for p, rp in powers.items():
            GamePlayer.objects.create(game=g,
                                      power=p,
                                      player=rp.player)
        URL = 'http://example.com/new.html'
        NOTE = 'Some note'
        data = {'form-TOTAL_FORMS': '2',
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-game_id': str(g.id),
                'form-0-name': 'NewName',
                'form-0-external_url': URL,
                'form-0-notes': NOTE,
                'form-0-the_set': str(self.ah.pk),
                'form-1-game_id': '',
                'form-1-name': '',
                'form-1-external_url': '',
                'form-1-notes': '',
                'form-1-the_set': ''}
        for p, rp in powers.items():
            data[f'form-0-{p.name}'] = str(rp.pk)
            # Include a blank form in the formset
            data[f'form-1-{p.name}'] = ''
        data = urlencode(data)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.post(reverse('create_games', args=(self.t1.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should re-direct to the board call page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('board_call', args=(self.t1.pk, 1)))
        # The one Game should still exist
        self.assertEqual(self.r11.game_set.count(), 1)
        g = self.r11.game_set.get()
        self.assertEqual(g.name, 'NewName')
        self.assertEqual(g.the_set, self.ah)
        self.assertEqual(g.external_url, URL)
        self.assertEqual(g.notes, NOTE)
        self.assertEqual(g.gameplayer_set.count(), 7)
        for p, rp in powers.items():
            self.assertEqual(g.gameplayer_set.filter(power=p, player=rp.player).count(), 1)
        # TODO Verify that email is NOT sent
        # Clean up
        self.r11.game_set.all().delete()

    def test_create_games_modify_two_games(self):
        """Check that multiple games can be changed in different ways"""
        self.assertEqual(self.r11.game_set.count(), 0)
        powers = {self.austria : self.rp11,
                  self.turkey : self.rp12,
                  self.england : self.rp13,
                  self.russia : self.rp15,
                  self.italy : self.rp16,
                  self.france : self.rp17,
                  self.germany : self.rp19}
        g1 = Game.objects.create(the_round=self.r11,
                                 name='Existing1',
                                 the_set=self.gibsons,
                                 external_url='http://example.com/old.html')
        g2 = Game.objects.create(the_round=self.r11,
                                 name='Existing2',
                                 the_set=self.gibsons,
                                 external_url='http://example.com/old.html')
        for p, rp in powers.items():
            GamePlayer.objects.create(game=g1,
                                      power=p,
                                      player=rp.player)
            # Swap England and Russia in g2
            if p == self.england:
                GamePlayer.objects.create(game=g2,
                                          power=self.russia,
                                          player=rp.player)
            elif p == self.russia:
                GamePlayer.objects.create(game=g2,
                                          power=self.england,
                                          player=rp.player)
            else:
                GamePlayer.objects.create(game=g2,
                                          power=p,
                                          player=rp.player)
        data = {'form-TOTAL_FORMS': '2',
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-game_id': str(g1.id),
                'form-0-name': g1.name,
                # Change a non-player field in g1, too
                'form-0-external_url': '',
                'form-0-notes': g1.notes,
                'form-0-the_set': str(g1.the_set.pk),
                'form-1-game_id': str(g2.id),
                'form-1-name': g2.name,
                'form-1-external_url': g2.external_url,
                'form-1-notes': g2.notes,
                'form-1-the_set': str(g2.the_set.pk)}
        for p, rp in powers.items():
            data[f'form-0-{p.name}'] = str(rp.pk)
            data[f'form-1-{p.name}'] = str(rp.pk)
        data = urlencode(data)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.post(reverse('create_games', args=(self.t1.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should re-direct to the board call page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('board_call', args=(self.t1.pk, 1)))
        # The two Games should still exist
        self.assertEqual(self.r11.game_set.count(), 2)
        for g in self.r11.game_set.all():
            # GamePlayers should be set as expected
            self.assertEqual(g.gameplayer_set.count(), 7)
            for p, rp in powers.items():
                self.assertEqual(g.gameplayer_set.filter(power=p, player=rp.player).count(), 1)
        # TODO Verify that email is sent
        # Clean up
        self.r11.game_set.all().delete()

    def test_create_games_post_duplicate_name(self):
        """Duplicate a Game name in another Round of the same Tournament"""
        self.assertEqual(self.r21.game_set.count(), 0)
        self.assertEqual(self.r23.game_set.count(), 0)
        powers = {self.austria : self.rp21,
                  self.turkey : self.rp23,
                  self.england : self.rp24,
                  self.russia : self.rp25,
                  self.italy : self.rp26,
                  self.france : self.rp27,
                  self.germany : self.rp28}
        # Create a Game in round 1
        Game.objects.create(the_round=self.r21,
                            name="Duplicate",
                            the_set=self.gibsons)
        data = {'form-TOTAL_FORMS': '2',
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-game_id': '',
                'form-0-name': 'Duplicate',
                'form-0-external_url': 'http://example.com/game.html',
                'form-0-notes': '',
                'form-0-the_set': str(self.ah.pk),
                'form-1-game_id': '',
                'form-1-name': '',
                'form-1-external_url': '',
                'form-1-notes': '',
                'form-1-the_set': ''}
        for p, rp in powers.items():
            data[f'form-0-{p.name}'] = str(rp.pk)
            # Include a blank form in the formset
            data[f'form-1-{p.name}'] = ''
        data = urlencode(data)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.post(reverse('create_games', args=(self.t2.pk, 3)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # We should get an error due to the duplicate name
        self.assertContains(response, 'must be unique')
        # Clean up
        self.r21.game_set.all().delete()
        self.r23.game_set.all().delete()

    def test_game_scores_not_logged_in(self):
        response = self.client.get(reverse('game_scores',
                                           args=(self.t1.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)

    def test_game_scores(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('game_scores',
                                           args=(self.t3.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_game_scores_post(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        r = self.t4.round_numbered(1)
        g1 = r.game_set.first()
        g2 = r.game_set.last()
        data = {'form-TOTAL_FORMS': '2',
                'form-INITIAL_FORMS': '2',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0'}
        data['form-0-name'] = g1.name
        expected_scores = {}
        for gp in g1.gameplayer_set.all():
            # Leave game 1 scores unchanged
            data[f'form-0-{gp.power.name}'] = str(gp.score)
            expected_scores[gp] = gp.score
        data['form-1-name'] = g2.name
        for gp in g2.gameplayer_set.all():
            # Modify game 2 scores
            data[f'form-1-{gp.power.name}'] = str(gp.player.pk)
            expected_scores[gp] = gp.player.pk
        data = urlencode(data)
        response = self.client.post(reverse('game_scores', args=(self.t4.pk, 1)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # Should redirect to the round index page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('round_index', args=(self.t4.pk,)))
        # Game scores should be saved
        for g in r.game_set.all():
            for gp in g.gameplayer_set.all():
                with self.subTest(player=gp.player, game=g.name):
                    self.assertEqual(gp.score, expected_scores[gp])
        # Round scores should be recalculated
        for rp in r.roundplayer_set.all():
            with self.subTest(player=rp.player):
                self.assertEqual(rp.score, rp.player.pk)
        # Tournament scores should be recalculated
        for tp in self.t4.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                # p2 doesn't play at all
                if tp.player == self.p2:
                    self.assertEqual(tp.score, 0.0)
                else:
                    self.assertEqual(tp.score, tp.player.pk)

    def test_game_index(self):
        response = self.client.get(reverse('game_index',
                                           args=(self.t4.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_board_call(self):
        response = self.client.get(reverse('board_call',
                                           args=(self.t4.pk, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
