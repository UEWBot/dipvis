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
from ast import literal_eval
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from tournament.diplomacy.values.diplomacy_values import WINNING_SCS

BACKSTABBR_NETLOCS = ['backstabbr.com', 'www.backstabbr.com']
BACKSTABBR_NETLOC = BACKSTABBR_NETLOCS[1]

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


class BackstabbrNotAccessible(Exception):
    """Unable to retrieve the game from Backstabbr."""
    pass


class InvalidGameUrl(Exception):
    """Expected a Backstabbr game URL."""
    pass


class NoSuchSeason(Exception):
    """The specified season isn't present in the game."""
    pass


def is_backstabbr_url(url):
    """Returns True if the specified URL points to the backstabbr domain"""
    parsed_url = urlparse(url)
    return parsed_url.netloc in BACKSTABBR_NETLOCS


class Game():

    """
    A single game on Backstabbr
    """

    TIMEOUT = 3.5

    def __init__(self, url, skip_read=False):
        """
        url is a link to the game on backstabbr.

        If skip_read is True, the URL will not be accessed, and not all
        attributes will be available/accurate. read_current_state() can
        be called later to populate these attributes.

        May raise BackstabbrNotAccessible, InvalidGameUrl.
        """
        self.url = url
        self.parsed_url = urlparse(url)
        if self.parsed_url.netloc not in BACKSTABBR_NETLOCS:
            raise InvalidGameUrl(self.url)
        self.regular_game = ('game/' in self.parsed_url.path)
        self.sandbox_game = ('sandbox/' in self.parsed_url.path)
        if not self.regular_game and not self.sandbox_game:
            raise InvalidGameUrl(self.url)
        self._trim_url_path()
        try:
            self.number = self._extract_game_number()
        except ValueError as e:
            raise InvalidGameUrl(self.url) from e
        # Default all the other instance variables
        self.name = 'Unknown'
        self.gm = 'Unknown'
        # The current turn, or final turn if the game has ended
        self.season = SPRING
        self.year = 1901
        # A string describing how the game ended
        self.result = 'Unknown'
        # This is the player who soloed (if any)
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
        if not skip_read:
            # Now parse the current state of the game
            self.read_current_state()

    def read_current_state(self):
        """
        Read the current state of the game

        Sets self.name, self.season, self.year, self.players, self.gm, self.ongoing,
        self.sc_counts, self.soloing_power, self.sc_ownership, self.position, self.orders,
        self.result, and self.soloer.

        Only needed if the Game was created with skip_read=True.

        May raise BackstabbrNotAccessible, InvalidGameUrl.
        """
        self._parse_page()
        self._calculate_result()

    def _trim_url_path(self):
        """
        Shorten the URL path to just the game itself

        This will remove any trailing slash, invite code, or season
        from both self.url and self.parsed_url.path

        May raise InvalidGameUrl.
        """
        # Expected format is [game|sandbox]/<optional name>/<number>
        # Anything after the <number> needs to be removed
        parts = self.parsed_url.path.split('/')
        if len(parts) > 3:
            if parts[2].isdecimal():
                new_path = '/'.join(parts[:3])
            elif parts[3].isdecimal():
                new_path = '/'.join(parts[:4])
            else:
                raise InvalidGameUrl(self.url)
            self.parsed_url = self.parsed_url._replace(path=new_path)
            self.url = urlunparse(self.parsed_url)

    def _extract_game_number(self):
        """Extracts the backstabbr game id as an int from the URL"""
        # game number should be everything after the last '/'
        return int(self.parsed_url.path.rsplit('/', 1)[-1])

    def _calculate_result(self):
        """
        Set self.result and self.soloer from self.soloing_power, self.sc_counts, self.players, and self.ongoing.
        """
        self.soloer = None
        if self.soloing_power is not None:
            self.soloer = self.players[self.soloing_power][0]
        alive = len([count for count in self.sc_counts.values() if count > 0])
        if self.soloer is not None:
            self.result = 'Solo'
        elif self.ongoing:
            self.result = f'{alive} powers still alive'
        else:
            self.result = f'{alive}-way draw'

    def _url_to_soup(self, url):
        """
        Open the specified URL, turn the web page into soup.

        May raise BackstabbrNotAccessible, InvalidGameUrl.
        """
        tries = 0
        # Backstabbr has occasional problems. A retry usually works
        while tries < 2:
            page = requests.get(url,
                                timeout=self.TIMEOUT)
            tries += 1
            if page.status_code == requests.codes.ok:
                return BeautifulSoup(page.text, "html.parser")
            elif page.status_code == requests.codes.not_found:
                raise InvalidGameUrl(url)
            elif page.status_code != requests.codes.internal_server_error:
                raise BackstabbrNotAccessible(f'{page.status_code} {url}')
        raise BackstabbrNotAccessible(f'{page.status_code} {url}')

    def _parse_page(self):
        """
        Read the game page on backstabbr and extract the interesting details.

        May raise BackstabbrNotAccessible, InvalidGameUrl.
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

        May raise NoSuchSeason, BackstabbrNotAccessible, InvalidGameUrl.
        """
        url = urljoin(self.url + '/', f'{year}/{season}')
        return self._parse_turn_page(url, season, year)

    def _parse_turn_page(self, url, season, year):
        """
        Read the game page on backstabbr and extract the interesting details.

        Returns a (sc_counts, soloing_power, sc_ownership, position, orders) 5-tuple

        May raise NoSuchSeason, BackstabbrNotAccessible, InvalidGameUrl.
        """
        soup = self._url_to_soup(url)
        s, y = self._season_and_year(soup)
        if (s != season) or (y != year):
            raise NoSuchSeason(season, year)
        return self._parse_turn_from_soup(soup)

    def _season_and_year(self, soup):
        """
        Read the season and year from the page

        Returns a (season, year) 2-tuple
        """
        a = soup.find('a', id='history_current_season')
        season_year = a.get_text().split()
        season = season_year[0]
        year = int(season_year[1])
        return season, year

    def _parse_invariants_from_soup(self, soup):
        """
        Read the fixed properties of the game from the soup.

        Sets self.name, self.season, self.year, self.players, self.gm, and self.ongoing
        """
        # Extract the game name and current season and year
        m = soup.find('meta', property="og:title", content=True)
        if m:
            title = m["content"].rpartition('(')
            self.name = title[0].strip()
            season_year = title[2][:-1].split()
            self.season = season_year[0].lower()
            self.year = int(season_year[1])
        else:
            title = soup.find('title')
            self.name = title.string.partition('Game:')[2].partition('|  Backstabbr')[0].strip()
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
