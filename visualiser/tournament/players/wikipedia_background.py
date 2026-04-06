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

# This file contains code to parse online sources of background information
# about Diplomacy players. Currently reads Wikipedia for titles and the World
# Diplomacy Database for lots of stuff.

"""
This module is dedicated to extracting background information about a player
from online sources.

Currently those sources are Wikipedia for titles and the World Diplomacy
Database or World Diplomacy Reference for everything else.
"""

import requests
from bs4 import BeautifulSoup

from django.conf import settings

from tournament.diplomacy import WINNING_SCS
from tournament.wdd import (WDD_BASE_RANKING_URL, WDD_BASE_RESULTS_URL,
                            wdd_img_to_country)
from tournament.wdr import WDR_BASE_URL


class WikipediaNotAccessible(Exception):
    """Wikipedia cannot currently be accessed."""
    pass


class WikipediaCache():
    """
    Cache of the International Prize List of Diplomacy wikipedia page
    """

    # Use the wikipedia REST API to retrieve the page
    TEMPLATE_URL = 'https://en.wikipedia.org/api/rest_v1/page/{}/International_prize_list_of_Diplomacy'
    PAGE_URL = TEMPLATE_URL.format('html')
    TITLE_URL = TEMPLATE_URL.format('title')

    # Timeout for retrieving wikipedia pages
    TIMEOUT = 1.5

    def __init__(self):
        self.the_soup = None
        self.revision = ''
        self._read_page()

    def _read_page(self):
        """Read the page. Store the soup in self.the_soup and the revision string in self.revision"""
        url = self.PAGE_URL
        try:
            page = requests.get(url,
                                headers={'User-Agent': settings.USER_AGENT,
                                         'Accept-Encoding': 'gzip'},
                                timeout=self.TIMEOUT)
        except requests.exceptions.Timeout:
            return
        self.the_soup = BeautifulSoup(page.text, "html.parser")
        try:
            etag = page.headers["ETag"]
        except KeyError as e:
            print(page.headers)
            self.revision = None
            raise e
        # ETag format is 'W/"1298445974/e23c2e85-8215-11f0-a785-1d77f87c9956/view/html"'
        # Store the revision
        s = etag.split('"')
        s = s[1].split('/')
        self.revision = s[0]

    def _latest_revision(self):
        """Return the latest revision of the page, as a string"""
        url = self.TITLE_URL
        try:
            page = requests.get(url,
                                headers={'User-Agent': settings.USER_AGENT,
                                         'Accept-Encoding': 'gzip'},
                                timeout=self.TIMEOUT)
        except requests.exceptions.Timeout:
            return ''
        json = page.json()
        return json['items'][0]['rev']

    def soup(self):
        """Get the soup of the wikipedia page"""
        # Check the current revision and re-read the page if the cache is out-of-date
        if self.revision != self._latest_revision():
            self._read_page()
        if self.the_soup is None:
            raise WikipediaNotAccessible
        return self.the_soup


# Singleton
cache = WikipediaCache()


class WikipediaBackground():
    """
    Get background on a player from wikipedia.
    """

    def __init__(self, name):
        self.name = name

    def _relevant(self, d):
        for val in d.values():
            # It's relevant if the player name matches
            if val == self.name:
                return True
        return False

    def titles(self):
        """
        Titles won by this player

        Returns a list of dicts.
        Keys are 'Tournament' and position.
        """
        try:
            soup = cache.soup()
        except WikipediaNotAccessible:
            print('Unable to read wikipedia')
            return []
        main = soup
        results = []
        last_hdr = None
        for table in main.find_all('table'):
            # Find the preceeding h3 or h2
            hdr = table.find_previous('h3')
            # We don't want to find the same header again
            if (not hdr) or (hdr == last_hdr):
                hdr = table.find_previous('h2')
            last_hdr = hdr
            tournament = hdr.get_text()
            # Parse the table itself
            row = table.tr
            columns = []
            for th in row.find_all('th'):
                columns.append(str(th.string.strip()))
            while True:
                row = row.find_next_sibling()
                if not row:
                    break
                result = {'Tournament': tournament}
                for key, td in zip(columns, row.find_all('td')):
                    val = list(td.stripped_strings)
                    if val:
                        val = val[0]
                        try:
                            val = int(val)
                        except ValueError:
                            pass
                        result[key] = val
                        for span in td.find_all('span', recursive=False):
                            if span.a:
                                nat = span.a['title']
                                result.setdefault(f'{key} Flags', []).append(nat)
                results.append(result)
        # Now results contains all the results
        # Filter out any that don't refer to the person we care about
        return [item for item in results if self._relevant(item)]
