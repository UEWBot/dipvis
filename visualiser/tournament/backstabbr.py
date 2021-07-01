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
import urllib.request
from ast import literal_eval
from bs4 import BeautifulSoup

BACKSTABBR_GAME_URL = 'https://www.backstabbr.com/game/'

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

class InvalidGameId(Exception):
    """The id provided for the game is unused on Backstabbr."""
    pass


class InvalidGameUrl(Exception):
    """Expected a Backstabbr game URL."""
    pass


def number_from_game_url(url):
    """Extracts the backstabbr game id as an int from a backstabbr URL"""
    if BACKSTABBR_GAME_URL not in url:
        raise InvalidGameUrl(url)
    if url[-1] == '/':
        url = url[:-1]
    return int(url.split('/')[-1])


class Game():

    """
    A single game on Backstabbr
    """

    def __init__(self, number):
        """
        number is the unique id for the game on backstabbr.
        """
        self.number = number
        self.gm = 'Unknown'
        self.ongoing = True
        self.soloing_power = None
        self.powers = {}
        self.sc_ownership = {}
        self.position = {}
        self.orders = {}
        for p in POWERS:
            self.powers[p] = (0, 'Unknown')
        self._parse_page()
        self._calculate_result()

    def _calculate_result(self):
        """
        Set self.result and self.soloer from self.powers and self.ongoing.
        """
        alive = 0
        self.soloer = None
        for count, player in self.powers.values():
            if count > 0:
                alive += 1
            if count > 17:
                self.soloer = player
        if self.soloer is not None:
            self.result = 'Solo'
        elif self.ongoing:
            self.result = '%d powers still alive' % alive
        else:
            self.result = '%d-way draw' % alive

    def _parse_page(self):
        """
        Read the game page on backstabbr and extract the interesting details.
        """
        self.url = '%s%d' % (BACKSTABBR_GAME_URL, self.number)
        page = urllib.request.urlopen(self.url)
        if page.geturl() != self.url:
            # We were redirected - implies invalid game number
            raise InvalidGameId(self.number)
        soup = BeautifulSoup(page.read())
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
        # Centre counts
        for span in soup.find_all('span'):
            if span.div:
                power, count = span.text.strip().split()
                t = self.powers[power]
                dots = int(count)
                self.powers[power] = (dots, t[1])
                if dots > 17:
                    self.soloing_power = power
        # Players
        for h4 in soup.find_all('h4'):
            if 'Players' in h4.string:
                t = h4.find_next('table')
                for td in t.find_all('td'):
                    if td.div:
                        power = td.div.text.strip()
                    elif td.a:
                        t = self.powers[power]
                        self.powers[power] = (t[0], td.a.string.strip())
        # GM
        for h4 in soup.find_all('h4'):
            if 'Gamemaster' in h4.string:
                for s in h4.next_siblings:
                    if s.name == 'h6':
                        try:
                            self.gm = s.a.string.strip()
                        except AttributeError:
                            self.gm = None
                        self.ongoing = False
        # SC ownership, unit locations, and orders
        for scr in soup.find_all('script'):
            if scr.string is not None:
                match = DOTS.search(scr.string)
                if match:
                    self.sc_ownership = literal_eval(match.group(1))
                match = UNITS.search(scr.string)
                if match:
                    self.position = literal_eval(match.group(1))
                match = ORDERS.search(scr.string)
                if match:
                    self.orders = literal_eval(match.group(1))
