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

import urllib.request
from bs4 import BeautifulSoup

BACKSTABBR_GAME_URL = 'http://www.backstabbr.com/game/'

def previous_season(year, season):
    """
    Returns the year and season before the one provided.
    year should be an int.
    season should be one of "spring", "fall", or "winter".
    """
    PREV = {'spring': 'winter',
            'fall': 'spring',
            'winter' : 'fall'}
    prev_season = PREV[season]
    if season == 'Spring':
        return year - 1, prev_season
    else:
        return year, prev_season

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
        self.powers['Austria'] = (0, 'Unknown')
        self.powers['England'] = (0, 'Unknown')
        self.powers['France'] = (0, 'Unknown')
        self.powers['Germany'] = (0, 'Unknown')
        self.powers['Italy'] = (0, 'Unknown')
        self.powers['Russia'] = (0, 'Unknown')
        self.powers['Turkey'] = (0, 'Unknown')
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
        soup = BeautifulSoup(page.read())
        # Extract the game name
        m = soup.find('meta', property="og:description", content=True)
        if m:
            self.name = m["content"]
        else:
            title = soup.find('title')
            self.name = title.string.partition('Game:')[2].partition('|  Backstabbr')[0].strip()
        # Season and year
        for div in soup.find_all('div'):
            if div.has_attr('class') and 'modal-body' in div['class']:
                if div.a:
                    # This gives us the "current season" i.e. the next season to be played
                    season_year = div.a.string.split()
                    self.last_year, self.last_season = previous_season(int(season_year[1]), season_year[0])
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

    def as_dict(self):
        """
        Return a dict containing all the details of the game.
        """
        retval = {}
        retval['name'] = self.name
        retval['id'] = self.number
        retval['url'] = self.url
        retval['ongoing'] = self.ongoing
        retval['result'] = self.result
        retval['soloer'] = self.soloer
        retval['soloing_power'] = self.soloing_power
        retval['last season'] = self.last_season
        retval['last year'] = self.last_year
        retval['gm'] = self.gm
        for k, v in self.powers.items():
            retval['%s centres' % k] =  v[0]
            retval['%s player' % k] =  v[1]
        return retval

def print_game(number):
    """
    Print the details of the Backstabbr game with the specified number.
    """
    g = Game(number)
    print(g.as_dict())
    print('Name: %s.' % g.name)
    print('Ongoing: %s.' % g.ongoing)
    print('Result: %s.' % g.result)
    print('Winner: %s.' % g.soloer)
    print('Winning Power: %s.' % g.soloing_power)
    print('Last turn completed: %s %d.' % (g.last_season, g.last_year))
    print('GM: %s.' % g.gm)
    for k, v in g.powers.items():
        print('Power: %s.' % k)
        print('  Centre Count: %s.' % v[0])
        print('  Player: %s.' % v[1])

if __name__ == "__main__":
    # Test with three known games
    print_game(5127188186136576)
    print_game(5128998112198656)
    print_game(5169348121985024)
    print_game(4728919006117888)
    print_game(5689559237263360)
