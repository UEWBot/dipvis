# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2026 Chris Brand
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

import requests
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from django.test import TestCase, tag

from .add_player_bg import WIKIPEDIA_EVENT_KIND_MAP
from . import WikipediaBackground
from .wikipedia_background import WikipediaCache, WikipediaNotAccessible, cache


class WikipediaBackgroundTests(TestCase):

    FIXTURE_PAGE = 'tournament/players/testdata/wikipedia_international_prize_list_of_diplomacy.html'

    @classmethod
    def _fixture_soup(cls):
        with open(cls.FIXTURE_PAGE, encoding='utf-8') as f:
            return BeautifulSoup(f.read(), "html.parser")

    def test_wikipedia_cache_read_page_timeout(self):
        with patch('tournament.players.wikipedia_background.requests.get',
                   side_effect=requests.exceptions.Timeout):
            cache = WikipediaCache()
            self.assertIsNone(cache.the_soup)

    def test_wikipedia_cache_latest_revision_timeout(self):
        page = Mock()
        page.text = '<html></html>'
        page.headers = {'ETag': 'W/"1298445974/e23c2e85-8215-11f0-a785-1d77f87c9956/view/html"'}
        with patch('tournament.players.wikipedia_background.requests.get', return_value=page):
            cache = WikipediaCache()
        with patch('tournament.players.wikipedia_background.requests.get',
                   side_effect=requests.exceptions.Timeout):
            self.assertEqual('', cache._latest_revision())

    def test_wikipedia_cache_missing_etag_keeps_existing_cache(self):
        good_page = Mock()
        good_page.text = '<html><body><p>good-content</p></body></html>'
        good_page.headers = {'ETag': 'W/"1298445974/e23c2e85-8215-11f0-a785-1d77f87c9956/view/html"'}
        with patch('tournament.players.wikipedia_background.requests.get', return_value=good_page):
            cache = WikipediaCache()

        old_soup = cache.the_soup
        old_revision = cache.revision
        old_last_read = cache.last_read

        bad_page = Mock()
        bad_page.text = '<html><body><p>rate-limited</p></body></html>'
        bad_page.headers = {}
        with patch('tournament.players.wikipedia_background.requests.get', return_value=bad_page):
            cache._read_page()

        self.assertIs(cache.the_soup, old_soup)
        self.assertEqual(old_revision, cache.revision)
        self.assertGreaterEqual(cache.last_read, old_last_read)

    @patch('builtins.print')
    def test_wikipedia_titles_when_page_unavailable(self, mock_print):
        bg = WikipediaBackground('Someone Unreachable')
        with patch('tournament.players.wikipedia_background.cache.soup',
                   side_effect=WikipediaNotAccessible):
            self.assertEqual([], bg.titles())
        mock_print.assert_called_with('Unable to read wikipedia')

    def test_wikipedia_background_titles(self):
        name = 'Cyrille Sevin'
        flags = ['France']
        bg = WikipediaBackground(name)
        with patch('tournament.players.wikipedia_background.cache.soup',
               return_value=self._fixture_soup()):
            titles = bg.titles()
        self.assertEqual(len(titles), 8)
        for t in titles:
            with self.subTest(title=t):
                if t['Year'] == 1997:
                    if t['Tournament'] == 'EuroDipCon':
                        self.assertEqual(t['European Champion'], name)
                        self.assertEqual(t['European Champion Flags'], flags)
                    else:
                        self.assertEqual(t['World Champion'], name)
                        self.assertEqual(t['World Champion Flags'], flags)
                elif t['Year'] == 2001:
                    self.assertEqual(t['World Champion'], name)
                    self.assertEqual(t['World Champion Flags'], flags)
                elif t['Year'] == 2004:
                    self.assertEqual(t['Third'], name)
                    self.assertEqual(t['Third Flags'], flags)
                elif t['Year'] == 2006:
                    self.assertEqual(t['Second'], name)
                    self.assertEqual(t['Second Flags'], flags)
                elif t['Year'] == 2008:
                    self.assertEqual(t['Second'], name)
                    self.assertEqual(t['Second Flags'], flags)
                elif t['Year'] == 2013:
                    self.assertEqual(t['World Champion'], name)
                    self.assertEqual(t['World Champion Flags'], flags)
                else:
                    # 2015
                    self.assertEqual(t['European Champion'], name)
                    self.assertEqual(t['European Champion Flags'], flags)

    def test_wikipedia_background_nationalities(self):
        """Check that multi-nationals get parsed correctly"""
        name = 'Antonio Ribeiro da Silva'
        flags = ['France', 'Portugal']
        bg = WikipediaBackground(name)
        with patch('tournament.players.wikipedia_background.cache.soup',
                   return_value=self._fixture_soup()):
            titles = bg.titles()
        self.assertEqual(len(titles), 1)
        for t in titles:
            with self.subTest(title=t):
                self.assertEqual(t['Second'], name)
                self.assertEqual(t['Second Flags'], flags)

    @tag('wikipedia_live')
    def test_wikipedia_background_titles_live(self):
        """Live integration check against current Wikipedia content."""
        bg = WikipediaBackground('Cyrille Sevin')
        titles = bg.titles()
        self.assertGreater(len(titles), 0)

    @tag('wikipedia_live')
    def test_wikipedia_event_kind_map_covers_live_events(self):
        """Live integration check that all current Wikipedia events are mapped."""
        soup = cache.soup()
        events = set()
        last_hdr = None
        for table in soup.find_all('table'):
            hdr = table.find_previous('h3')
            if (not hdr) or (hdr == last_hdr):
                hdr = table.find_previous('h2')
            last_hdr = hdr
            events.add(hdr.get_text())

        self.assertGreater(len(events), 0)
        self.assertEqual(set(), events - set(WIKIPEDIA_EVENT_KIND_MAP))
