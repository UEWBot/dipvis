# Diplomacy Tournament Visualiser
# Copyright (C) 2025 Chris Brand
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

from urllib.parse import urlencode, urlunparse

from django.test import TestCase
from django.urls import reverse

from tournament.backstabbr import BACKSTABBR_NETLOC

INVALID_GAME_NUMBER = 1
SOLO_GAME_NUMBER = 5128998112198656
SANDBOX_1_GAME_NUMBER = 5766492401172480
SANDBOX_2_GAME_NUMBER = 5412944885972992
SANDBOX_3_GAME_NUMBER = 5101432468275200

class BackstabbrViewTests(TestCase):
    def test_graph_page_game(self):
        response = self.client.get(reverse('game_sc_graph',
                                           args=(SOLO_GAME_NUMBER, )),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_graph_page_sandbox(self):
        response = self.client.get(reverse('sandbox_sc_graph',
                                           args=(SANDBOX_1_GAME_NUMBER, )),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_graph_game(self):
        response = self.client.get(reverse('graph',
                                           args=('game', SOLO_GAME_NUMBER, )),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_graph_sandbox_1(self):
        response = self.client.get(reverse('graph',
                                           args=('sandbox', SANDBOX_1_GAME_NUMBER, )),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_graph_sandbox_2(self):
        response = self.client.get(reverse('graph',
                                           args=('sandbox', SANDBOX_2_GAME_NUMBER, )),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_graph_sandbox_3(self):
        response = self.client.get(reverse('graph',
                                           args=('sandbox', SANDBOX_3_GAME_NUMBER, )),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_graph_invalid_game_number(self):
        response = self.client.get(reverse('graph',
                                           args=('game', INVALID_GAME_NUMBER, )),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_url_form(self):
        response = self.client.get(reverse('enter_url'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_url_form_post_game(self):
        path = f'game/{SOLO_GAME_NUMBER}'
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        data = urlencode({'url': url})
        response = self.client.post(reverse('enter_url'),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the graph page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('game_sc_graph', args=(SOLO_GAME_NUMBER, )))

    def test_url_form_post_sandbox(self):
        path = f'sandbox/{SANDBOX_1_GAME_NUMBER}'
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        data = urlencode({'url': url})
        response = self.client.post(reverse('enter_url'),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the graph page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('sandbox_sc_graph', args=(SANDBOX_1_GAME_NUMBER, )))

    def test_url_form_post_invalid_game_url(self):
        """Backstabbr game URL, but for a game that isn't readable"""
        path = f'game/{INVALID_GAME_NUMBER}'
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        data = urlencode({'url': url})
        response = self.client.post(reverse('enter_url'),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the graph page
        # because we don't want to actually read backstabbr at this point
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('game_sc_graph', args=(INVALID_GAME_NUMBER, )))

    def test_url_form_post_invalid_url(self):
        """Not a backstabbr game URL"""
        path = 'member/jHm3Y12XTZGeoRd2kl_cWw'
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        data = urlencode({'url': url})
        response = self.client.post(reverse('enter_url'),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # Page should load
        self.assertEqual(response.status_code, 200)
        # and contain a single error on the URL field
        self.assertEqual(len(response.context['form'].errors['url']), 1)
        self.assertIn('Not a valid backstabbr game URL',
                      response.context['form'].errors['url'][0])
