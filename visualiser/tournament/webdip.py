# Copyright 2022 Chris Brand
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

"""
Scrape the interesting parts of a Diplomacy game on WebDiplomacy.net.
"""

import urllib.request
from urllib.parse import urlparse, parse_qs, urlunparse
from bs4 import BeautifulSoup

from tournament.diplomacy.values.diplomacy_values import WINNING_SCS

WEBDIPLOMACY_NETLOC = 'webdiplomacy.net'

# Names used for Great Powers on WebDiplomacy
POWERS = ['Austria',
          'England',
          'France',
          'Germany',
          'Italy',
          'Russia',
          'Turkey']

# Names used for the seasons on WebDiplomacy
SPRING = 'Spring'
FALL = 'Autumn'


class InvalidGameUrl(Exception):
    """Expected a WebDiplomacy game URL."""
    pass

class UnsupportedVariant(Exception):
    """Only the standard map is supported."""
    pass


class Game():
    """
    A single game on WebDiplomacy
    """

    def __init__(self, url):
        """
        url is a link to a game on WebDiplomacy
        """
        self.url = url
        self.parsed_url = urlparse(url)
        if self.parsed_url.netloc != WEBDIPLOMACY_NETLOC:
            raise InvalidGameUrl(self.url)
        try:
            self.id = self._extract_game_id()
        except KeyError as e:
            raise InvalidGameUrl(self.url) from e
        self.ongoing = True
        self.players = {}
        self.soloing_power = None
        self.sc_counts = {}
        for p in POWERS:
            self.sc_counts[p] = 0
            # (payer, player profile URL) tuple
            self.players[p] = ('Unknown', '')
        self._parse_page()
        self._calculate_result()

    def _extract_game_id(self):
        """Extracts the game id as an int from the URL"""
        query = self.parsed_url.query
        qs = parse_qs(query)
        num = qs['gameID'][0]
        # Webdip strips off any characters after the number part
        if not num.isdigit():
            tmp =[]
            for c in num:
                if c.isdigit():
                    tmp.append(c)
                else:
                    break
            num = ''.join(tmp)
        return int(num)

    def _url_to_soup(self, url):
        """
        Open the specified URL, turn the web page into soup.
        """
        #page = urllib.request.urlopen(url)
        req = urllib.request.Request(url, headers={'User-Agent': "Magic Browser"})
        page = urllib.request.urlopen( req )
        if page.url != url:
            # We were redirected - implies invalid game URL
            raise InvalidGameUrl(url)
        return BeautifulSoup(page.read())

    def _parse_page(self):
        """
        Read the game page on WebDiplomacy and extract the interesting details
        """
        soup = self._url_to_soup(self.url)
        self._parse_invariants_from_soup(soup)

    def _calculate_result(self):
        """
        Set self.result and self.soloer from self.sc_counts, self.players, and self.ongoing
        """
        self.soloer = None
        if self.soloing_power is not None:
            self.soloer = self.players[self.soloing_power][0]
        alive = len([count for count in self.sc_counts.values() if count > 0])
        if self.soloer is not None:
            self.result = 'Solo'
        elif self.ongoing:
            self.result = '%d powers still alive' % alive
        else:
            self.result = '%d-way draw' % alive

    def _parse_invariants_from_soup(self, soup):
        """
        Read the fixed properties of the game from the soup.
        Sets self.name, self.ongoing, self.season, self.year,
        self.players, self.sc_counts (for uneliminated powers), and self.soloing_power
        """
        # First check the variant
        span = soup.find('span', {'class': 'gamePotType'})
        if not span:
            raise InvalidGameUrl(self.url)
        variant = span.a.string
        if variant != "Classic":
            raise UnsupportedVariant(variant)
        span = soup.find('span', {'class': 'gameName'})
        self.name = span.string
        span = soup.find('span', {'class': 'gameTimeRemainingNextPhase'})
        self.ongoing = not (span.string == 'Finished:')
        span = soup.find('span', {'class': 'gameDate'})
        date = span.string.split(', ')
        self.season = date[0]
        self.year = int(date[1])
        span = soup.find('span', {'class': 'gamePhase'})
        # Parse the players from the bottom of the page
        for td in soup.find_all('td', {'class': 'memberLeftSide'}):
            span = td.find('span', {'class': 'memberCountryName'})
            if not span:
                # This player abandoned the game - ignore them
                continue
            power = span.span.string
            if power[0] == '-':
                power = power.split(' ')[1]
            td2 = td.next_sibling.next_sibling
            # Get the player link
            span = td2.find('span', {'class': 'memberName'})
            a = span.a
            # and the SC count (not present for eliminated powers)
            span = td2.find('span', {'class': 'memberSCCount'})
            if span:
                dots = int(span.em.string)
            else:
                dots = 0
            # And store all the extracted information
            self.players[power] = (a.string, urlunparse(('https',
                                                         WEBDIPLOMACY_NETLOC,
                                                         a.get('href'),
                                                         '', '', '')))
            self.sc_counts[power] = dots
            if dots >= WINNING_SCS:
                self.soloing_power = power
