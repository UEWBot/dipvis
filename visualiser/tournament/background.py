# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016 Chris Brand
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
Database for everything else.
"""

import urllib.request
from bs4 import BeautifulSoup

WDD_BASE_RESULTS_URL = 'http://world-diplomacy-database.com/php/results/'
WDD_BASE_RANKING_URL = 'http://world-diplomacy-database.com/php/ranking/'
WIKIPEDIA_URL = 'https://en.wikipedia.org/wiki/International_prize_list_of_Diplomacy'

MAP = {'Name of the tournament': 'Tournament',
      }


class InvalidWDDId(Exception):
    """The WDD id provided for the player is unused on the WDD."""
    pass


class WDDNotAccessible(Exception):
    """The WWD website cannot currently be accessed."""
    pass


class UnableToSplitName(Exception):
    """The name retrieved from the WDD is a single word."""
    pass


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
        Returns a list of dicts.
        Keys are Tournament and position.
        """
        url = WIKIPEDIA_URL
        page = urllib.request.urlopen(url)
        soup = BeautifulSoup(page.read())
        # Find the first H2 with a span inside
        h2 = None
        for h2 in soup.find_all('h2'):
            span = h2.span
            if span:
                break
        results = []
        tag = h2
        while tag:
            if tag.name == 'h2' or tag.name == 'h3':
                span = tag.span
                if span:
                    tournament = str(span.string)
            elif tag.name == 'table':
                row = tag.tr
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
                    results.append(result)
            tag = tag.find_next_sibling()
        # Now results contains all the results
        # Filter out any that don't refer to the person we care about
        return [item for item in results if self._relevant(item)]


def img_to_country(img):
    """
    Convert a WDD flag image name to a country name.
    """
    filename = img.rpartition('/')[2]
    return filename[:-4]


class WDDBackground():
    """
    Get background on a player from the World Diplomacy Database.
    """

    def __init__(self, wdd_id):
        self.wdd_id = wdd_id

    def wdd_name(self):
        """
        Returns the name of the player, as read from the WDD
        Can raise WDDNotAccessible or InvalidWDDId
        """
        url = WDD_BASE_RESULTS_URL + 'player_fiche.php?id_player=%d' % self.wdd_id
        try:
            page = urllib.request.urlopen(url)
        except urllib.request.URLError as e:
            # Most likely, WDD is not available
            raise WDDNotAccessible from e
        if page.geturl() != url:
            # We were redirected - implies invalid WDD id
            raise InvalidWDDId(self.wdd_id)
        soup = BeautifulSoup(page.read())
        return soup.title.string[6:]

    def wdd_firstname_lastname(self):
        """
        Returns a 2-tuple containsin the name of the player, as read from the WDD
        Can raise WDDNotAccessible, InvalidWDDId, or UnableToSplitName
        """
        name = self.wdd_name()
        name_parts = name.split()
        if len(name_parts) < 2:
            raise UnableToSplitName
        first_name = name_parts.pop(0)
        last_name = name_parts.pop()
        while name_parts:
            word = name_parts.pop(0)
            if word.isupper() and not word.endswith('.') and not len(word) == 1:
                # This is likely part of the last name
                last_name = ' '.join([word] + name_parts + [last_name])
                name_parts = []
            else:
                # Likely part of the first name
                first_name = first_name + ' ' + word
        return (first_name, last_name)

    def finishes(self):
        """
        Returns a list of tournament placings.
        Each entry is a dict.
        Keys are Position, Date, Country, Tournament, WDD URL, and Type.
        Can raise InvalidWDDId
        """
        # Individual Prize List
        url = WDD_BASE_RESULTS_URL + 'player_fiche.php?id_player=%d' % self.wdd_id
        page = urllib.request.urlopen(url)
        if page.geturl() != url:
            # We were redirected - implies invalid WDD id
            raise InvalidWDDId(self.wdd_id)
        soup = BeautifulSoup(page.read())
        table = soup.find('table', width='65%')
        if not table:
            return []
        # Check that we have the "Tournament" rather than "Circuit" table
        header = table.find('th')
        if 'ournament' not in header.string:
            # No such table
            return []
        row = header.find_parent()
        # Move to the column headers row
        row = row.find_next_sibling()
        columns = []
        for th in row.find_all('th'):
            col = MAP.get(th.string, str(th.string))
            columns.append(col)
        results = []
        for row in row.next_siblings:
            th = row.find('th')
            if th:
                # New position
                position = int(th.string[0])
            else:
                # New result at that position
                result = {'Position': position}
                for key, td in zip(columns, row.find_all('td')):
                    if len(td.contents):
                        # Countries are encoded as flag images
                        if td.string:
                            result[key] = str(td.string)
                        else:
                            result[key] = img_to_country(td.img['src'])
                    # Add URLs to the results dict
                    if key == u'Tournament':
                        result[u'WDD URL'] = WDD_BASE_RESULTS_URL + td.a['href']
                results.append(result)
        return results

    def tournaments(self):
        """
        Returns a list of dicts, one per tournament competed in.
        Dict is keyed by column name, except for "Step of the following circuits", which
        is omitted, and an additional "WDD URL" giving the URL for the tournament in the WDD.
        The content of the "Rank" column is split into "Rank" and "Total Players".
        Can raise InvalidWDDId
        """
        # Tournaments competed in
        url = WDD_BASE_RESULTS_URL + 'player_fiche5.php?id_player=%d' % self.wdd_id
        page = urllib.request.urlopen(url)
        if page.geturl() != url:
            # We were redirected - implies invalid WDD id
            raise InvalidWDDId(self.wdd_id)
        soup = BeautifulSoup(page.read())
        results = []
        # This page really confuses BeautifulSoup. Have to just find all th and td tags
        for row in soup.find_all('tr'):
            # Header row contains header cells
            th = row.th
            if th:
                # First column is "Date"
                if th.string == u'Date':
                    # This is the row to parse
                    columns = []
                    for th in row.find_all('th'):
                        columns.append(str(th.string))
                    # Beautiful Soup actually truncates the row,
                    # but it only misses team stuff that we don't care about
                    continue
            # All the data rows in the table we're interested in have class="row_even" or "row_odd"
            try:
                c = row.attrs[u'class']
            except KeyError:
                continue
            if c[0].startswith('row_'):
                result = {}
                for key, td in zip(columns, row.find_all('td')):
                    if key == u'Rank':
                        # Split the two separate pieces of info
                        try:
                            rank, total = td.string.split(u' / ')
                            result['Rank'] = int(rank)
                        except ValueError:
                            # WDD include TDs (who played ?) but doesn't rank them
                            pass
                        try:
                            result['Total players'] = int(total[:-8])
                        except ValueError:
                            # Sometimes WDD doesn't have total players for a tournament
                            pass
                    elif td.string:
                        result[key] = str(td.string)
                    elif td.img:
                        result[key] = img_to_country(td.img['src'])
                    # Add URLs to the results dict
                    if key == u'Name of the tournament':
                        result[u'WDD URL'] = WDD_BASE_RESULTS_URL + td.a['href']
                    # Don't populate "Step of the following circuits"
                results.append(result)
        return results

    def boards(self):
        """
        Returns a list of boards played.
        Each board is a dict, keyed by column name. The "Rank" column is replaced by three
        keys - "Position", "Position sharing" (number of people sharing the position),
        and "Game end" ("L", "W", or "Dn"). The "SCs" column is replaced by "Final SCs"
        and/or "Elimination year".
        Two additional keys are added - "WDD Tournament URL" and "WDD Board URL", giving
        the URLs for the tournament and the board in the WDD.
        Can raise InvalidWDDId
        """
        # Tournament board listings
        url = WDD_BASE_RESULTS_URL + 'player_fiche9.php?id_player=%d' % self.wdd_id
        page = urllib.request.urlopen(url)
        if page.geturl() != url:
            # We were redirected - implies invalid WDD id
            raise InvalidWDDId(self.wdd_id)
        soup = BeautifulSoup(page.read())
        results = []
        # This page really confuses BeautifulSoup. Have to just find all th and td tags
        for row in soup.find_all('tr'):
            # Header row contains header cells
            th = row.th
            if th:
                # First column is "Date"
                if th.string == u'Date':
                    # This is the row to parse
                    columns = []
                    for th in row.find_all('th'):
                        # Note that there are two columns called "Country"
                        # Fortunately the second is the one we want,
                        # So we don't worry about the second overwriting the first
                        columns.append(str(th.string))
                    # Beautiful Soup even truncates this row
                    columns += [u'Rank', u'SCs', u'Score']
                    continue
            # All the data rows in the table we're interested in have class="row_even" or "row_odd"
            try:
                c = row.attrs[u'class']
            except KeyError:
                continue
            if c[0].startswith('row_'):
                result = {}
                for key, td in zip(columns, row.find_all('td')):
                    if key == u'Rank':
                        # stripped_strings here could produce a number of different things:
                        # '3'
                        # '6', '2ex'
                        # '4', '2ex', '(D3)'
                        # '4 (L)'
                        # 'n.c.'
                        # The Rank column actually encodes up to three separate pieces of info
                        for key, s in zip([u'Position', u'Position sharing', u'Game end'],
                                          td.stripped_strings):
                            if 'ex' in s:
                                result[key] = int(s[:-2])
                            elif s[0] == '(':
                                result[key] = s[1:-1]
                            elif '(' in s:
                                s2 = s.split()
                                result[key] = s2[0]
                                result[u'Game end'] = s2[1][1:-1]
                            elif s == 'n.c.':
                                # This seems to indicate that the result for the game is not recorded
                                break
                            else:
                                result[key] = int(s)
                    elif key == 'SCs':
                        # The SCs column can contain year of elimination instead
                        if 'c.' in td.string:
                            # It's a final centre count, or maybe just 'c.'
                            if td.string != 'c.':
                                n = int(td.string[:-2])
                                result[u'Final SCs'] = n
                                # Not all solos are flagged as such
                                if n > 17:
                                    result[u'Game end'] = u'W'
                        else:
                            # It's a year of elimination
                            result[u'Elimination year'] = str(td.string)
                            result[u'Final SCs'] = u'0'
                    elif td.string:
                        try:
                            result[key] = float(td.string)
                        except ValueError:
                            result[key] = str(td.string)
                    elif td.img:
                        result[key] = img_to_country(td.img['src'])
                    # Add URLs to the results dict
                    if key == u'Name of the tournament':
                        result[u'WDD Tournament URL'] = WDD_BASE_RESULTS_URL + td.a['href']
                    elif key == u'Round / Board':
                        result[u'WDD Board URL'] = WDD_BASE_RESULTS_URL + td.a['href']
                results.append(result)
        return results

    def awards(self):
        """
        Returns a dict, keyed by power name or 'Awards' of arrays of dicts.
        Keys for the inner dict are always 'Date', 'Country', 'Tournament', WDD URL, and 'Type'
        plus either 'SCs' and 'Score' (for best country awards) or 'Name' (for other awards)
        Can raise InvalidWDDId
        """
        url = WDD_BASE_RESULTS_URL + 'player_fiche3.php?id_player=%d' % self.wdd_id
        page = urllib.request.urlopen(url)
        if page.geturl() != url:
            # We were redirected - implies invalid WDD id
            raise InvalidWDDId(self.wdd_id)
        soup = BeautifulSoup(page.read())
        results = {}
        for table in soup.find_all('table', width='65%'):
            for th in table.find_all('th'):
                if th.string == 'List of won awards':
                    awards_table = True
                elif th.string.startswith('Best '):
                    awards_table = False
                    the_power = th.string.split()[-1]
                else:
                    # Skip the unexpected table
                    continue
                row = th.find_parent()
                # Move to the column headers row
                row = row.find_next_sibling()
                columns = []
                for th in row.find_all('th'):
                    col = MAP.get(th.string, str(th.string))
                    columns.append(col)
                if awards_table:
                    results['Awards'] = []
                else:
                    results[the_power] = []
                for row in row.next_siblings:
                    result = {}
                    for key, td in zip(columns, row.find_all('td')):
                        # Countries are encoded as flag images
                        if td.string:
                            result[key] = str(td.string)
                        elif td.img:
                            result[key] = img_to_country(td.img['src'])
                        else:
                            # Sometimes multiple awards were won at one tournament,
                            # encoded as a nested table
                            # (Multiple best country awards will be in separate tables)
                            # Also sometimes fields like SCs or Score are empty
                            if td.find('tr'):
                                for t in td.find_all('td'):
                                    if t.string:
                                        new_res = dict(result)
                                        new_res[key] = str(t.string)
                                        results['Awards'].append(new_res)
                                # We added them all individually above
                                result = {}
                        # Add URLs to the results dict
                        if key == u'Tournament':
                            result[u'WDD URL'] = WDD_BASE_RESULTS_URL + td.a['href']
                    # Don't add empty dicts
                    if result == {}:
                        continue
                    if awards_table:
                        results['Awards'].append(result)
                    else:
                        results[the_power].append(result)
        return results

    def rankings(self):
        """
        Returns a list of dicts.
        Keys for the dict are 'Name', 'Score', 'International rank', and 'National rank'.
        Can raise InvalidWDDId
        """
        url = WDD_BASE_RESULTS_URL + 'player_fiche4.php?id_player=%d' % self.wdd_id
        page = urllib.request.urlopen(url)
        if page.geturl() != url:
            # We were redirected - implies invalid WDD id
            raise InvalidWDDId(self.wdd_id)
        soup = BeautifulSoup(page.read())
        results = []
        for table in soup.find_all('table', width='70%'):
            columns = []
            for th in table.find_all('th'):
                col = MAP.get(th.string, str(th.string))
                columns.append(col)
            row = th.find_parent()
            for row in row.next_siblings:
                result = {}
                for key, td in zip(columns, row.find_all('td')):
                    if td.string:
                        result[key] = str(td.string)
                # Discard any row for a particular year
                if '20' not in result['Name']:
                    results.append(result)
        return results
