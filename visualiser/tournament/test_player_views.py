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

from tournament.players import Player

class TournamentViewTests(TestCase):

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
        response = self.client.get(reverse('player_index'))
        self.assertEqual(response.status_code, 200)

    def test_detail_invalid_player(self):
        response = self.client.get(reverse('player_detail', args=(self.INVALID_P_PK,)))
        self.assertEqual(response.status_code, 404)

    def test_detail(self):
        # Don't have to be logged in to see a player
        response = self.client.get(reverse('player_detail', args=(self.p1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_detail_refresh_wdd(self):
        # Test the "Refresh From WDD" button
        self.client.login(username=self.USERNAME, password=self.PWORD)
        player_url = reverse('player_detail', args=(self.p1.pk,))
        response = self.client.post(player_url,
                                    urlencode({}),
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect back to the same URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, player_url)

    # TODO test upload_players(), including fields with trailing spaces
