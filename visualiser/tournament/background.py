# Diplomacy Tournament Visualiser
# Copyright (C) 2014 Chris Brand
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

from bs4 import BeautifulSoup
import urllib2

WDD_BASE_URL = 'http://world-diplomacy-database.com/php/results/'

class Background():
    """
    Get background on a player from online sources.
    """

    def __init__(self, wdd_id):
        self.wdd_id = wdd_id
        name = self.wdd_name()
        parts = name.split()
        self.first_name = parts[0].title()
        self.last_name = parts[1].title()

    def wdd_name(self):
        """
        Player name from the WDD
        """
        url = WDD_BASE_URL + 'player_fiche.php?id_player=%d' % self.wdd_id
        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page.read())
        return soup.title.string[6:]

    def name(self):
        """
        Returns the name of the player.
        """
        return self.first_name + ' ' + self.last_name

    def finishes(self):
        """
        Returns a list of tournament placings.
        Each entry is a dict.
        Keys are Position, Date, Country, Name of the tournament, and Type.
        """
        # Individual Prize List
        url = WDD_BASE_URL + 'player_fiche.php?id_player=%d' % self.wdd_id
        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page.read())
        table = soup.find('table', width='65%')
        if not table:
            return []
        # Check that we have the "Tournament" rather than "Circuit" table
        header = table.find('th')
        if not 'ournament' in header.string:
            # No such table
            return []
        row = header.find_parent()
        # Move to the column headers row
        row = row.find_next_sibling()
        columns = []
        for th in row.find_all('th'):
            columns.append(th.string)
        results = []
        while True:
            row = row.find_next_sibling()
            if not row:
                break
            th = row.find('th')
            if th:
                # New position
                position = int(th.string[0])
            else:
                # New result at that position
                result = {'Position': position}
                for key,td in zip(columns, row.find_all('td')):
                    # Countries are encoded as flag images
                    if td.string:
                        result[key] = td.string
                    else:
                        result[key] = td.img['src']
                results.append(result)
        return results

    def stats(self):
        """
        Returns statistics by country for the player.
        Returns a dict, keyed by country name (or 'Total') of dicts.
        Inner dict is keyed by column name.
        """
        # Board Statistics for tournaments only
        url = WDD_BASE_URL + 'player_fiche16.php?event=1&id_player=%d' % self.wdd_id
        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page.read())
        # Script is in the footer
        script = soup.find('script')
        footer = script.find_parent()
        table = footer.find_previous_sibling()
        if not table:
            return []
        row = table.tr
        columns = []
        for th in row.find_all('th'):
            columns.append(th.string)
        results = {}
        while True:
            row = row.find_next_sibling()
            if not row:
                break
            result = {}
            for key,td in zip(columns, row.find_all('td')):
                if key == 'Country':
                    country = td.string
                    results[country] = []
                else:
                    result[key] = td.string
            results[country].append(result)
        return results
