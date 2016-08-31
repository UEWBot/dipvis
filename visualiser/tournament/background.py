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
WIKIPEDIA_URL = 'https://en.wikipedia.org/wiki/International_prize_list_of_Diplomacy'

MAP = {'Name of the tournament': 'Tournament',
      }

class InvalidWDDId(Exception):
    pass

class WDDNotAccessible(Exception):
    pass

def img_to_country(img):
    """
    Convert a WDD flag image name to a country name.
    """
    path, sep, filename = img.rpartition('/')
    return filename[:-4]

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

    def _relevant(self, d):
        for val in d.itervalues():
            if val == self.name():
                return True
        return False

    def titles(self):
        """
        Returns a list of dicts.
        Keys are Tournament and position.
        """
        url = WIKIPEDIA_URL
        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page.read())
        # Find the first H2 with a span inside
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
                    tournament = unicode(span.string)
            elif tag.name == 'table':
                row = tag.tr
                columns = []
                for th in row.find_all('th'):
                    columns.append(unicode(th.string))
                while True:
                    row = row.find_next_sibling()
                    if not row:
                        break
                    result = {'Tournament': tournament}
                    for key,td in zip(columns, row.find_all('td')):
                        val = list(td.stripped_strings)
                        if len(val) > 0:
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

    def wdd_name(self):
        """
        Player name from the WDD
        """
        url = WDD_BASE_URL + 'player_fiche.php?id_player=%d' % self.wdd_id
        try:
            page = urllib2.urlopen(url)
        except urllib2.URLError:
            # Most likely, WDD is not available
            raise WDDNotAccessible
        if page.geturl() != url:
            # We were redirected - implies invalid WDD id
            raise InvalidWDDId
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
        Keys are Position, Date, Country, Tournament, and Type.
        """
        # Individual Prize List
        url = WDD_BASE_URL + 'player_fiche.php?id_player=%d' % self.wdd_id
        page = urllib2.urlopen(url)
        if page.geturl() != url:
            # We were redirected - implies invalid WDD id
            raise InvalidWDDId
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
            try:
                col = MAP[th.string]
            except KeyError:
                col = unicode(th.string)
            columns.append(col)
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
                for key, td in zip(columns, row.find_all('td')):
                    # Countries are encoded as flag images
                    if td.string:
                        result[key] = unicode(td.string)
                    else:
                        result[key] = img_to_country(td.img['src'])
                results.append(result)
        return results

    def stats(self):
        """
        Returns statistics by country for the player.
        Returns a dict, keyed by country name, of dicts.
        Inner dict is keyed by column name.
        """
        # Board Statistics for tournaments only
        url = WDD_BASE_URL + 'player_fiche16.php?event=1&id_player=%d' % self.wdd_id
        page = urllib2.urlopen(url)
        if page.geturl() != url:
            # We were redirected - implies invalid WDD id
            raise InvalidWDDId
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
            columns.append(unicode(th.string))
        results = {}
        while True:
            row = row.find_next_sibling()
            if not row:
                break
            result = {}
            for key,td in zip(columns, row.find_all('td')):
                if key == 'Country':
                    country = unicode(td.string)
                else:
                    val = td.string
                    # Massage the value
                    val = val.replace(' %', '%')
                    val = val.split()[0]
                    try:
                        val = int(val)
                    except ValueError:
                        try:
                            val = float(val)
                        except ValueError:
                            pass
                    result[key] = val
            results[country] = result
        del results['Total']
        return results

    def tournaments(self):
        """
        Returns a list of dicts, one per tournament competed in.
        Dict is keyed by column name, except for "Step of the following circuits", which
        is omitted, and an additional "WDD URL" giving the URL for the tournament in the WDD.
        The content of the "Rank" column is split into "Rank" and "Total Players".
        """
        # Tournaments competed in
        url = WDD_BASE_URL + 'player_fiche5.php?id_player=%d' % self.wdd_id
        page = urllib2.urlopen(url)
        if page.geturl() != url:
            # We were redirected - implies invalid WDD id
            raise InvalidWDDId
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
                        columns.append(unicode(th.string))
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
                for key,td in zip(columns, row.find_all('td')):
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
                        result[key] = unicode(td.string)
                    elif td.img:
                        result[key] = td.img['src']
                    # Add URLs to the results dict
                    if key == u'Name of the tournament':
                        result[u'WDD URL'] = WDD_BASE_URL + td.a['href']
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
        """
        # Tournament board listings
        url = WDD_BASE_URL + 'player_fiche9.php?id_player=%d' % self.wdd_id
        page = urllib2.urlopen(url)
        if page.geturl() != url:
            # We were redirected - implies invalid WDD id
            raise InvalidWDDId
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
                        # Note that there are two columsn called "Country"
                        # Fortunately the second is the one we want,
                        # So we don't worry about the second overwriting the first
                        columns.append(unicode(th.string))
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
                for key,td in zip(columns, row.find_all('td')):
                    if key == u'Rank':
                        # stripped_strings here could produce a number of different things:
                        # '3'
                        # '6', '2ex'
                        # '4', '2ex', '(D3)'
                        # '4 (L)'
                        # The Rank column actually encodes up to three separate pieces of info
                        for key,s in zip([u'Position', u'Position sharing', u'Game end'],
                                         td.stripped_strings):
                            if s.find('ex') != -1:
                                result[key] = int(s[:-2])
                            elif s[0] == '(':
                                result[key] = s[1:-1]
                            elif s.find('(') != -1:
                                s2 = s.split()
                                result[key] = s2[0]
                                result[u'Game end'] = s2[1][1:-1]
                            else:
                                result[key] = int(s)
                    elif key == 'SCs':
                        # The SCs column can contain year of elimination instead
                        if td.string.find('c.') != -1:
                            # It's a final centre count, or maybe just 'c.'
                            if td.string != 'c.':
                                n = int(td.string[:-2])
                                result[u'Final SCs'] = n
                                # Not all solos are flagged as such
                                if n > 17:
                                    result[u'Game end'] = u'W'
                        else:
                            # It's a year of elimination
                            result[u'Elimination year'] = unicode(td.string)
                            result[u'Final SCs'] = u'0'
                    elif td.string:
                        try:
                            result[key] = float(td.string)
                        except ValueError:
                            result[key] = unicode(td.string)
                    elif td.img:
                        result[key] = td.img['src']
                    # Add URLs to the results dict
                    if key == u'Name of the tournament':
                        result[u'WDD Tournament URL'] = WDD_BASE_URL + td.a['href']
                    elif key == u'Round / Board':
                        result[u'WDD Board URL'] = WDD_BASE_URL + td.a['href']
                results.append(result)
        return results

