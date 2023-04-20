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

from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tournament.diplomacy.models.great_power import GreatPower
from tournament.players import Player, PlayerGameResult

class PlayerViewTests(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # A Player
        cls.p1 = Player.objects.create(first_name='Angela',
                                       last_name='Ampersand')

        # A pk that (hopefully) doesn't correspond to a player
        cls.INVALID_P_PK = 99999

        # A Superuser
        cls.USERNAME = 'superuser'
        cls.PWORD = 'L33tPw0rd'
        u = User.objects.create_user(username=cls.USERNAME,
                                     password=cls.PWORD,
                                     is_superuser=True)
        u.save()


    def test_index(self):
        response = self.client.get(reverse('player_index'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_detail_invalid_player(self):
        response = self.client.get(reverse('player_detail',
                                           args=(self.INVALID_P_PK,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_detail(self):
        # Don't have to be logged in to see a player
        response = self.client.get(reverse('player_detail',
                                           args=(self.p1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_detail_refresh_wdd(self):
        # Test the "Refresh From WDD" button
        self.client.login(username=self.USERNAME, password=self.PWORD)
        player_url = reverse('player_detail', args=(self.p1.pk,))
        response = self.client.post(player_url,
                                    urlencode({}),
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect back to the same URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, player_url)

    def test_versus_invalid_player1(self):
        response = self.client.get(reverse('player_versus',
                                           args=(self.INVALID_P_PK, self.p1.pk)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_versus_invalid_player2(self):
        response = self.client.get(reverse('player_versus',
                                           args=(self.p1.pk, self.INVALID_P_PK)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_versus_no_prev(self):
        p2 = Player.objects.create(first_name='Bernard',
                                   last_name='Belligerent')
        response = self.client.get(reverse('player_versus',
                                           args=(self.p1.pk, p2.pk)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        p2.delete()

    def test_versus_prev(self):
        england = GreatPower.objects.get(abbreviation='E')
        germany = GreatPower.objects.get(abbreviation='G')
        p2 = Player.objects.create(first_name='Bernard',
                                   last_name='Belligerent')
        # Add a shared game
        # One with lots of blanks
        pgr1 = PlayerGameResult.objects.create(tournament_name='Galaxy Championship',
                                               game_name='Top Boards',
                                               date=timezone.now(),
                                               player=self.p1,
                                               power=england,
                                               position=3)
        # One with lots of detail
        pgr2 = PlayerGameResult.objects.create(tournament_name=pgr1.tournament_name,
                                               game_name=pgr1.game_name,
                                               date=pgr1.date,
                                               player=p2,
                                               power=germany,
                                               position=6,
                                               position_equals=2,
                                               score=3.4,
                                               final_sc_count=1,
                                               result='D7')
        response = self.client.get(reverse('player_versus',
                                           args=(self.p1.pk, p2.pk)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        pgr1.delete()
        p2.delete()

    def test_wpe(self):
        # Test WPE page
        response = self.client.get(reverse('wep7',
                                           args=(self.p1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # TODO validate result

    # TODO test upload_players(), including fields with trailing spaces
