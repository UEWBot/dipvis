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

import datetime as dt
import requests
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from django.test import TestCase, tag

from .add_player_bg import (WIKIPEDIA_EVENT_KIND_MAP,
                            WIKIPEDIA_TOURNAMENT_KIND_MAP)
from . import WikipediaBackground
from .wikipedia_background import WikipediaCache, WikipediaNotAccessible, cache


class WikipediaBackgroundTests(TestCase):

    FIXTURE_PAGE = 'tournament/players/testdata/wikipedia_international_prize_list_of_diplomacy.html'

    ETAG = 'W/"1298445974/e23c2e85-8215-11f0-a785-1d77f87c9956/view/html"'
    REVISION = '1298445974'

    @classmethod
    def _fixture_soup(cls):
        with open(cls.FIXTURE_PAGE, encoding='utf-8') as f:
            return BeautifulSoup(f.read(), "html.parser")

    @classmethod
    def _mock_page(cls, text='<html><body><p>cached</p></body></html>', etag=ETAG):
        page = Mock()
        page.text = text
        page.headers = {} if etag is None else {'ETag': etag}
        return page

    @classmethod
    def _offline_cache(cls, page=None):
        """Build a populated WikipediaCache without reading wikipedia"""
        with patch('tournament.players.wikipedia_background.requests.get',
                   return_value=page if page else cls._mock_page()):
            return WikipediaCache()

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

    def test_wikipedia_cache_latest_revision(self):
        wiki_cache = self._offline_cache()
        page = Mock()
        page.json.return_value = {'items': [{'rev': '1298445999'}]}
        with patch('tournament.players.wikipedia_background.requests.get',
                   return_value=page):
            self.assertEqual('1298445999', wiki_cache._latest_revision())

    @patch('builtins.print')
    def test_wikipedia_cache_latest_revision_invalid_json(self, mock_print):
        wiki_cache = self._offline_cache()
        page = Mock()
        page.text = 'not json'
        page.json.side_effect = requests.exceptions.JSONDecodeError('Expecting value',
                                                                    'not json',
                                                                    0)
        with patch('tournament.players.wikipedia_background.requests.get',
                   return_value=page):
            self.assertEqual('', wiki_cache._latest_revision())
        mock_print.assert_any_call('JSONDecodeError:')
        mock_print.assert_any_call('not json')

    def test_wikipedia_cache_soup_read_recently(self):
        """A recently-read page should be returned without checking the revision"""
        wiki_cache = self._offline_cache()
        wiki_cache.last_read = dt.datetime.now()
        with patch.object(WikipediaCache, '_latest_revision') as mock_revision:
            self.assertIs(wiki_cache.the_soup, wiki_cache.soup())
        mock_revision.assert_not_called()

    def test_wikipedia_cache_soup_still_current(self):
        """An unchanged revision should be re-used rather than re-read"""
        wiki_cache = self._offline_cache()
        old_last_read = dt.datetime.now() - (2 * WikipediaCache.MIN_READ_INTERVAL)
        wiki_cache.last_read = old_last_read
        old_soup = wiki_cache.the_soup
        with patch.object(WikipediaCache, '_latest_revision', return_value=self.REVISION), \
             patch.object(WikipediaCache, '_read_page') as mock_read_page:
            self.assertIs(old_soup, wiki_cache.soup())
        mock_read_page.assert_not_called()
        self.assertGreater(wiki_cache.last_read, old_last_read)

    def test_wikipedia_cache_soup_out_of_date(self):
        """A changed revision should cause the page to be re-read"""
        wiki_cache = self._offline_cache()
        wiki_cache.last_read = dt.datetime.now() - (2 * WikipediaCache.MIN_READ_INTERVAL)
        new_page = self._mock_page(text='<html><body><p>updated</p></body></html>',
                                   etag='W/"1298445999/e23c2e85-8215-11f0-a785-1d77f87c9956/view/html"')
        with patch.object(WikipediaCache, '_latest_revision', return_value='1298445999'), \
             patch('tournament.players.wikipedia_background.requests.get',
                   return_value=new_page):
            soup = wiki_cache.soup()
        self.assertEqual('1298445999', wiki_cache.revision)
        self.assertIn('updated', soup.get_text())

    def test_wikipedia_cache_soup_unavailable(self):
        """soup() should raise if the page has never been read successfully"""
        with patch('tournament.players.wikipedia_background.requests.get',
                   side_effect=requests.exceptions.Timeout):
            wiki_cache = WikipediaCache()
        self.assertIsNone(wiki_cache.the_soup)
        with patch.object(WikipediaCache, '_latest_revision', return_value=''):
            self.assertRaises(WikipediaNotAccessible, wiki_cache.soup)

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

    def test_wikipedia_background_no_flags(self):
        """A span with no link should not add flags"""
        page = '''<h2>Test Event</h2>
                  <table>
                  <tr><th>Year</th><th>World Champion</th></tr>
                  <tr><td>2020</td><td>Some Player<span>unlinked</span></td></tr>
                  </table>'''
        bg = WikipediaBackground('Some Player')
        with patch('tournament.players.wikipedia_background.cache.soup',
                   return_value=BeautifulSoup(page, "html.parser")):
            titles = bg.titles()
        self.assertEqual(len(titles), 1)
        self.assertEqual(titles[0]['Tournament'], 'Test Event')
        self.assertEqual(titles[0]['Year'], 2020)
        self.assertEqual(titles[0]['World Champion'], 'Some Player')
        self.assertNotIn('World Champion Flags', titles[0])

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
        self.assertEqual(set(), events - set(WIKIPEDIA_TOURNAMENT_KIND_MAP))
