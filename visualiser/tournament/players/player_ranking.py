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

# This file contains code related to Diplomacy players themselves.
# This is predominantly the Player class, but also the various classes
# used to cache background information about players' Diplomacy
# tournament history.

"""
This module provides classes to describe Diplomacy players.

Most of the code is dedicated to storing background information
about a player and retrieving it as needed.
"""

from urllib.parse import urlencode, urlunparse

from django.db import models
from django.utils.translation import gettext as _

from tournament.wdd import WDD_BASE_RANKING_PATH, WDD_NETLOC
from tournament.wdr import WDR_BASE_URL

from .player import Player
from .wdd_player import WDDPlayer


class PlayerRanking(models.Model):
    """
    WDD Ranking of a player.

    Used to import background information.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    system = models.CharField(max_length=50)
    score = models.FloatField(blank=True, null=True)
    international_rank = models.CharField(max_length=20)
    national_rank = models.CharField(max_length=20)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'system'],
                                    name='unique_player_system'),
        ]

    def __str__(self):
        s = _('%(player)s is ranked %(ranking)s internationally in the %(system)s') % {'player': self.player,
                                                                                       'ranking': self.international_rank,
                                                                                       'system': self.system}
        return s

    def wdd_url(self):
        """WDD URL where this ranking can be seen"""
        try:
            wdd = WDDPlayer.objects.get(player=self.player)
        except (WDDPlayer.DoesNotExist, WDDPlayer.MultipleObjectsReturned):
            return ''
        if self.system == 'World Performance Evaluation':
            wdd_system_id = 2
        elif self.system == 'Dip Pouch Tournament Rating':
            wdd_system_id = 3
        elif self.system == 'SDR Marathon':
            wdd_system_id = 16
        else:
            return ''
        query = {'id_ranking': wdd_system_id,
                 'id_player': wdd.wdd_player_id}
        url = urlunparse(('https',
                          WDD_NETLOC,
                          f'{WDD_BASE_RANKING_PATH}ranking_player.php',
                          '',
                          urlencode(query),
                          ''))
        return url

    def wdr_url(self):
        """WDR URL where this ranking can be seen"""
        if self.system == 'WPE7':
            return f'{WDR_BASE_URL}rankings/wpe7'
        return ''

    def national_str(self):
        """Returns a string describing the national_rank"""
        s = _('%(player)s is ranked %(ranking)s in their country in the %(system)s') % {'player': self.player,
                                                                                        'ranking': self.national_rank,
                                                                                        'system': self.system}
        return s
