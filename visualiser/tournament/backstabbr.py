# Copyright 2018, 2020 Chris Brand
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
Scrape the interesting parts of a Diplomacy game on Backstabbr.com.
"""

import re
import requests
from urllib.parse import urljoin, urlparse, urlunparse
from ast import literal_eval
from bs4 import BeautifulSoup

from tournament.diplomacy.values.diplomacy_values import WINNING_SCS

BACKSTABBR_NETLOC = 'www.backstabbr.com'

# Names used for the Great Powers on Backstabbr
POWERS = ['Austria',
          'England',
          'France',
          'Germany',
          'Italy',
          'Russia',
          'Turkey']

# Names used for the Supply Centres on Backstabbr
DOTS = ['Ank',
        'Bel',
        'Ber',
        'Bre',
        'Bud',
        'Bul',
        'Con',
        'Den',
        'Edi',
        'Gre',
        'Hol',
        'Kie',
        'Lvp',
        'Lon',
        'Mar',
        'Mos',
        'Mun',
        'Nap',
        'Nwy',
        'Par',
        'Por',
        'Rom',
        'Rum',
        'Ser',
        'Sev',
        'Smy',
        'Spa',
        'StP',
        'Swe',
        'Tri',
        'Tun',
        'Ven',
        'Vie',
        'War']

# Names used for the seasons on Backstabbr
SPRING = 'spring'
FALL = 'fall'
WINTER = 'winter'

# Unit types on Backstabbr
UNITS = ['A', 'F']

# Javascript regexes
DOTS = re.compile('var territories = (.*);')
ORDERS = re.compile('var orders = (.*);')
UNITS = re.compile('var unitsByPlayer = (.*);')


class InvalidGameUrl(Exception):
    """Expected a Backstabbr game URL."""
    pass


class Game():

    """
    A single game on Backstabbr
    """

    def __init__(self, url):
        """
        url is a link to the game on backstabbr.
        """
        self.url = url
        self.parsed_url = urlparse(url)
        if self.parsed_url.netloc != BACKSTABBR_NETLOC:
            raise InvalidGameUrl(self.url)
        self.regular_game = ('game/' in self.parsed_url.path)
        self.sandbox_game = ('sandbox/' in self.parsed_url.path)
        if not self.regular_game and not self.sandbox_game:
            raise InvalidGameUrl(self.url)
        try:
            self.number = self._extract_game_number()
        except ValueError as e:
            raise InvalidGameUrl(self.url) from e
        # Default all the other instance variables
        self.name = 'Unknown'
        self.gm = 'Unknown'
        self.season = SPRING
        self.year = 1901
        self.result = 'Unknown'
        self.soloer = None
        self.ongoing = True
        self.players = {}
        self.soloing_power = None
        self.sc_counts = {}
        for p in POWERS:
            self.sc_counts[p] = 0
            # (player, player profile URL) tuple
            self.players[p] = ('Unknown', '')
        self.sc_ownership = {}
        self.position = {}
        self.orders = {}
        # Now parse the current state of the game
        self._parse_page()
        self._calculate_result()

    def _extract_game_number(self):
        """Extracts the backstabbr game id as an int from the URL"""
        url = self.parsed_url.path
        # strip any trailing '/'
        if url[-1] == '/':
            url = url[:-1]
        # game number should be everything after the last '/'
        return int(url.split('/')[-1])

    def _calculate_result(self):
        """
        Set self.result and self.soloer from self.sc_counts, self.players, and self.ongoing.
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

    def _url_to_soup(self, url):
        """
        Open the specified URL, turn the web page into soup.
        """
        page = requests.get(url,
                            allow_redirects=False,
                            timeout=1.5)
        if page.status_code != requests.codes.ok:
            raise InvalidGameUrl(url)
        return BeautifulSoup(page.text)

    def _parse_page(self):
        """
        Read the game page on backstabbr and extract the interesting details.
        """
        soup = self._url_to_soup(self.url)
        self._parse_invariants_from_soup(soup)
        # These will be the final or current values
        self.sc_counts, self.soloing_power, self.sc_ownership, self.position, self.orders = self._parse_turn_from_soup(soup)

    def turn_details(self, season, year):
        """
        Read the state of the game for the specified turn.
        Year should be an int that is a valid game year.
        Season should be 'spring', 'fall', or 'winter'.
        Returns a (sc_counts, soloing_power, sc_ownership, position, orders) 5-tuple
        sc_counts is a dict, indexed by power, of ints (number of SCs owned)
        soloing_power is a power, or None
        sc_ownership is a dict, indexed by SC, of power (owner of the SC)
        position is a dict, indexed by power, of dicts, indexed by province, of units.
           Where the province is coastal, unit is replaced by a dict indexed by 'coast' and 'type'
        orders is a dict, indexed by power, of dicts, indexed by province, of order dicts.
           The order dict may contain 'from', 'to', 'result', 'result_reason', 'type', 'to', and probably others.
        """
        url = urljoin(self.url + '/', '%d/%s' % (year, season))
        return self._parse_turn_page(url)

    def _parse_turn_page(self, url):
        """
        Read the game page on backstabbr and extract the interesting details.
        Returns a (sc_counts, soloing_power, sc_ownership, position, orders) 5-tuple
        """
        soup = self._url_to_soup(url)
        return self._parse_turn_from_soup(soup)

    def _parse_invariants_from_soup(self, soup):
        """
        Read the fixed properties of the game from the soup.
        Sets self.name, self.season, self.year, self.players, self.gm, and self.ongoing
        """
        # Extract the game name
        m = soup.find('meta', property="og:title", content=True)
        if m:
            self.name = m["content"].partition('(')[0].strip()
        else:
            title = soup.find('title')
            self.name = title.string.partition('Game:')[2].partition('|  Backstabbr')[0].strip()
        # Season and year
        for div in soup.find_all('div'):
            if div.has_attr('class') and 'modal-body' in div['class']:
                if div.a:
                    # This gives us the "current season" i.e. the next season to be played
                    season_year = div.a.string.split()
                    self.season = season_year[0]
                    self.year = int(season_year[1])
        # Players
        for h4 in soup.find_all('h4'):
            if 'Players' in h4.string:
                t = h4.find_next('table')
                for td in t.find_all('td'):
                    if td.div:
                        power = td.div.text.strip()
                    elif td.a:
                        self.players[power] = (td.a.string.strip(),
                                               urlunparse(('https',
                                                           BACKSTABBR_NETLOC,
                                                           td.a.get('href'),
                                                           '', '', '')))
        # GM
        for h4 in soup.find_all('h4'):
            if 'Gamemaster' in h4.string:
                for s in h4.next_siblings:
                    if s.name == 'h6':
                        try:
                            self.gm = s.a.string.strip()
                        except AttributeError:
                            pass
                        self.ongoing = False

    def _parse_turn_from_soup(self, soup):
        """
        Read the per-turn properties of the game from the soup.
        Returns a (sc_counts, soloing_power, sc_ownership, position, orders) 5-tuple
        """
        sc_counts = {}
        for p in POWERS:
            sc_counts[p] = 0
        soloing_power = None
        sc_ownership = {}
        position = {}
        orders = {}
        # Centre counts
        for span in soup.find_all('span'):
            if span.div:
                power, count = span.text.strip().split()
                dots = int(count)
                sc_counts[power] = dots
                if dots >= WINNING_SCS:
                    soloing_power = power
        # SC ownership, unit locations, and orders
        for scr in soup.find_all('script'):
            if scr.string is not None:
                match = DOTS.search(scr.string)
                if match:
                    sc_ownership = literal_eval(match.group(1))
                match = UNITS.search(scr.string)
                if match:
                    position = literal_eval(match.group(1))
                match = ORDERS.search(scr.string)
                if match:
                    # Retreat-off-the-board orders contain "null", which breaks literal_eval()
                    str = match.group(1).replace(': null,', ': None,')
                    try:
                        orders = literal_eval(str)
                    except ValueError:
                        print(match.group(1))
        return (sc_counts, soloing_power, sc_ownership, position, orders)
