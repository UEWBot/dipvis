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

from tournament.diplomacy import WINNING_SCS
from tournament.wdr import WDR_BASE_URL


class InvalidWDRId(Exception):
    """The WDR id provided for the player is unused on the WDR."""
    pass


class WDRNotAccessible(Exception):
    """The WDR website cannot currently be accessed."""
    pass


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
