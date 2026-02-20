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
Database or World Diplomacy Reference for everything else.
"""

import requests
from bs4 import BeautifulSoup

from django.conf import settings

from tournament.diplomacy.values.diplomacy_values import WINNING_SCS
from tournament.wdd import (WDD_BASE_RANKING_URL, WDD_BASE_RESULTS_URL,
                            wdd_img_to_country)
from tournament.wdr import WDR_BASE_URL


MAP = {'Name of the tournament': 'Tournament',
      }


class WikipediaNotAccessible(Exception):
    """Wikipedia cannot currently be accessed."""
    pass


class InvalidWDDId(Exception):
    """The WDD id provided for the player is unused on the WDD."""
    pass


class WDDNotAccessible(Exception):
    """The WDD website cannot currently be accessed."""
    pass


class UnableToSplitName(Exception):
    """The name retrieved from the WDD is a single word."""
    pass


class InvalidWDRId(Exception):
    """The WDR id provided for the player is unused on the WDR."""
    pass


class WDRNotAccessible(Exception):
    """The WDR website cannot currently be accessed."""
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


class WDDBackground():
    """
    Get background on a player from the World Diplomacy Database.
    """

    # timeout in seconds for read requests to WDD
    TIMEOUT = 4.0

    def __init__(self, wdd_id):
        self.wdd_id = wdd_id

    def _wdd_name(self):
        """
        Returns the name of the player, as read from the WDD

        Can raise WDDNotAccessible or InvalidWDDId
        """
        url = WDD_BASE_RESULTS_URL + 'player_fiche.php'
        try:
            page = requests.get(url,
                                params={'id_player': self.wdd_id},
                                headers={'User-Agent': settings.USER_AGENT,
                                         'Accept-Encoding': 'gzip'},
                                allow_redirects=False,
                                timeout=self.TIMEOUT)
        except requests.exceptions.Timeout as e:
            raise WDDNotAccessible from e
        if page.status_code != requests.codes.ok:
            raise InvalidWDDId(self.wdd_id, url, page.status_code)
        if not len(page.text):
            raise WDDNotAccessible("Got a response with no content")
        soup = BeautifulSoup(page.text, "html.parser")
        return soup.title.string[6:]

    def wdd_firstname_lastname(self):
        """
        Returns a 2-tuple containing the name of the player, as read from the WDD

        Can raise WDDNotAccessible, InvalidWDDId, or UnableToSplitName
        """
        # TODO Should be able to avoid manually splitting if we read the right part of the WDD
        name = self._wdd_name()
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

    def nationalities(self):
        """
        Returns a list of country 2- or 3-letter codes.

        WDD doesn't currently support multiple citizenships,
        but does have players without nationalities,
        so the list will currently always be empty or have a single entry.
        """
        url = WDD_BASE_RESULTS_URL + 'player_fiche.php'
        try:
            page = requests.get(url,
                                params={'id_player': self.wdd_id},
                                headers={'User-Agent': settings.USER_AGENT,
                                         'Accept-Encoding': 'gzip'},
                                allow_redirects=False,
                                timeout=self.TIMEOUT)
        except requests.exceptions.Timeout as e:
            raise WDDNotAccessible from e
        if page.status_code != requests.codes.ok:
            raise InvalidWDDId(self.wdd_id, url, page.status_code)
        soup = BeautifulSoup(page.text, "html.parser")
        table = soup.find('table', bgcolor='black')
        if not table:
            return []
        td = table.tr.th.table.tr.td
        if td.img:
            return [wdd_img_to_country(td.img['src'])]
        return []

    def location(self):
        """
        Returns a country 2- or 3-letter code or empty string if unknown.

        Currently always returns an empty string.
        """
        # TODO WDD shows location on the player index/search page, but I don't see it elsewhere
        return ''

    def finishes(self):
        """
        Returns a list of tournament placings.

        Each entry is a dict.
        Keys are Position, Date, Country, Tournament, WDD URL, and Type.
        Can raise InvalidWDDId
        """
        # Individual Prize List
        url = WDD_BASE_RESULTS_URL + 'player_fiche.php'
        try:
            page = requests.get(url,
                                params={'id_player': self.wdd_id},
                                headers={'User-Agent': settings.USER_AGENT,
                                         'Accept-Encoding': 'gzip'},
                                allow_redirects=False,
                                timeout=self.TIMEOUT)
        except requests.exceptions.Timeout as e:
            raise WDDNotAccessible from e
        if page.status_code != requests.codes.ok:
            raise InvalidWDDId(self.wdd_id, url, page.status_code)
        soup = BeautifulSoup(page.text, "html.parser")
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
                            result[key] = wdd_img_to_country(td.img['src'])
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
        url = WDD_BASE_RESULTS_URL + 'player_fiche5.php'
        try:
            page = requests.get(url,
                                params={'id_player': self.wdd_id},
                                headers={'User-Agent': settings.USER_AGENT,
                                         'Accept-Encoding': 'gzip'},
                                allow_redirects=False,
                                timeout=self.TIMEOUT)
        except requests.exceptions.Timeout as e:
            raise WDDNotAccessible from e
        if page.status_code != requests.codes.ok:
            raise InvalidWDDId(self.wdd_id, url, page.status_code)
        soup = BeautifulSoup(page.text, "html.parser")
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
                        result[key] = wdd_img_to_country(td.img['src'])
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
        url = WDD_BASE_RESULTS_URL + 'player_fiche9.php'
        try:
            page = requests.get(url,
                                params={'id_player': self.wdd_id},
                                headers={'User-Agent': settings.USER_AGENT,
                                         'Accept-Encoding': 'gzip'},
                                allow_redirects=False,
                                timeout=self.TIMEOUT)
        except requests.exceptions.Timeout as e:
            raise WDDNotAccessible from e
        if page.status_code != requests.codes.ok:
            raise InvalidWDDId(self.wdd_id, url, page.status_code)
        soup = BeautifulSoup(page.text, "html.parser")
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
                                if n >= WINNING_SCS:
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
                        result[key] = wdd_img_to_country(td.img['src'])
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
        url = WDD_BASE_RESULTS_URL + 'player_fiche3.php'
        try:
            page = requests.get(url,
                                params={'id_player': self.wdd_id},
                                headers={'User-Agent': settings.USER_AGENT,
                                         'Accept-Encoding': 'gzip'},
                                allow_redirects=False,
                                timeout=self.TIMEOUT)
        except requests.exceptions.Timeout as e:
            raise WDDNotAccessible from e
        if page.status_code != requests.codes.ok:
            raise InvalidWDDId(self.wdd_id, url, page.status_code)
        soup = BeautifulSoup(page.text, "html.parser")
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
                            result[key] = wdd_img_to_country(td.img['src'])
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
        url = WDD_BASE_RESULTS_URL + 'player_fiche4.php'
        try:
            page = requests.get(url,
                                params={'id_player': self.wdd_id},
                                headers={'User-Agent': settings.USER_AGENT,
                                         'Accept-Encoding': 'gzip'},
                                allow_redirects=False,
                                timeout=self.TIMEOUT)
        except requests.exceptions.Timeout as e:
            raise WDDNotAccessible from e
        if page.status_code != requests.codes.ok:
            raise InvalidWDDId(self.wdd_id, url, page.status_code)
        soup = BeautifulSoup(page.text, "html.parser")
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

    def wpe_scores(self):
        """Parse a World Performance Evaluation page on the World Diplomacy Database"""
        # TODO This is quite similar to finishes(), above
        url = WDD_BASE_RANKING_URL + 'ranking_player.php'
        try:
            page = requests.get(url,
                                params={'id_ranking': 2,
                                        'id_player': self.wdd_id},
                                headers={'User-Agent': settings.USER_AGENT,
                                         'Accept-Encoding': 'gzip'},
                                allow_redirects=False,
                                timeout=self.TIMEOUT)
        except requests.exceptions.Timeout as e:
            raise WDDNotAccessible from e
        if page.status_code != requests.codes.ok:
            # Unranked players don't get a WDD page at all
            return {}
        soup = BeautifulSoup(page.text, "html.parser")
        # Find the table we need to parse
        tr = None
        for th in soup.find_all('th'):
            if th.string and 'Name of the tournament' in th.string:
                tr = th.parent
        if not tr:
            return {}
        columns = []
        for th in tr.find_all('th'):
            col = MAP.get(th.string, str(th.string))
            columns.append(col)
        results = []
        for row in tr.next_siblings:
            result = {}
            for key, td in zip(columns, row.find_all('td')):
                if len(td.contents):
                    if td.string:
                        result[key] = str(td.string)
                    else:
                        result[key] = wdd_img_to_country(td.img['src'])
                if key == 'Tournament':
                    result['WDD WPE URL'] = WDD_BASE_RANKING_URL + td.a['href']
            results.append(result)
        return results


class WDRBackground():
    """
    Get background on a player from the World Diplomacy Reference.
    """

    # timeout in seconds for read requests to WDR
    # Some players have a long history
    TIMEOUT = 10.0

    def __init__(self, wdr_id):
        self.wdr_id = wdr_id
        # Use the WDR API to read the player's info and cache it locally
        self._read_wdr()

    def _read_wdr(self):
        """ Read the player's info from the WDR API """
        url = f'{WDR_BASE_URL}api/v1/players/{self.wdr_id}'
        try:
            page = requests.get(url,
                                headers={'User-Agent': settings.USER_AGENT,
                                         'Accept': 'application/json',
                                         'Accept-Encoding': 'gzip'},
                                timeout=self.TIMEOUT)
        except requests.exceptions.Timeout as e:
            raise WDRNotAccessible from e
        if page.status_code != requests.codes.ok:
            raise InvalidWDRId(self.wdr_id, url, page.status_code)
        self.data = page.json()

    def wdd_id(self):
        """ Returns the WDD id for the player """
        return self.data['player_wdd_id']

    def firstname_lastname(self):
        """
        Returns a 2-tuple containing the name of the player, as read from the WDR
        """
        return (self.data['player_first_name'], self.data['player_last_name'])

    def nationality(self):
        """
        Returns the nationality of the player

        2-letter ISO code
        """
        return self.data['player_nationality']

    def location(self):
        """
        Returns the location of the player

        2-letter ISO code
        """
        return self.data['player_location']

    def tournaments(self):
        """
        Returns the tournament results for the player

        list of dicts. Dict keys are:
            "tournament_id"
            "tournament_wdd_id"
            "tournament_name"
            "tournament_start_date"
            "tournament_end_date"
            "tournament_kind" ("CUP", "WDC", "DIPCON", "EDC", ...)
            "tournament_player_rank"
        """
        return self.data['player_tournaments_played']

    def boards(self):
        """
        Returns the board results for the player

        list of dicts. Dict keys are:
            "board_round"
            "board_number"
            "board_is_top"
            "board_tournament"
            "board_power"
            "board_centers"
            "board_score"
            "board_rank"
            "board_year_of_elimination"
            "board_url"
            "board_variant"
        """
        return self.data['player_boards_played']

    def awards(self):
        """
        Returns the awards for the player

        list of dicts. Dict keys are:
            "award_tournament"
            "award_country"
        """
        return self.data['player_awards']

    def rankings(self):
        """
        Returns the rankings for the player

        Returns a dict, keyed by ranking name (e.g. "WPE7"), of dicts
        """
        return self.data['player_rankings']
