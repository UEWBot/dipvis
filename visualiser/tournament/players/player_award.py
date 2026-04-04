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
from django.db.models import Q
from django.utils.translation import gettext as _

from tournament.diplomacy import TOTAL_SCS, GreatPower
from tournament.wdd import (WDD_BASE_RESULTS_PATH, WDD_NETLOC,
                            validate_wdd_tournament_id)
from tournament.wdr import WDR_BASE_URL, validate_wdr_tournament_id

from .player import Player


class PlayerAward(models.Model):
    """
    An award won by a player.

    Used to import background information.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    tournament = models.CharField(max_length=100)
    date = models.DateField()
    name = models.CharField(max_length=50)
    power = models.ForeignKey(GreatPower,
                              related_name='+',
                              on_delete=models.CASCADE,
                              blank=True,
                              null=True)
    score = models.FloatField(blank=True, null=True)
    final_sc_count = models.PositiveSmallIntegerField(blank=True, null=True)
    wdd_tournament_id = models.PositiveIntegerField(validators=[validate_wdd_tournament_id],
                                                    verbose_name=_(u'WDD tournament id'),
                                                    blank=True,
                                                    null=True)
    wdr_tournament_id = models.PositiveIntegerField(validators=[validate_wdr_tournament_id],
                                                    verbose_name=_(u'WDR tournament id'),
                                                    blank=True,
                                                    null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(final_sc_count__lte=TOTAL_SCS) | Q(final_sc_count__isnull=True),
                                   name='%(class)s_final_sc_count_valid'),
            models.UniqueConstraint(fields=['player', 'tournament', 'date', 'name'],
                                    name='unique_player_tournament_date_name'),
        ]

    def __str__(self):
        return _('%(player)s won %(award)s at %(tourney)s') % {'player': self.player,
                                                               'award': self.name,
                                                               'tourney': self.tournament}

    def wdd_url(self):
        """WDD URL where this award can be seen"""
        if not self.wdd_tournament_id:
            return ''
        if self.power is None:
            path = 'tournament_award.php'
        else:
            path = 'tournament_best_countries.php'
        query = {'id_tournament': self.wdd_tournament_id}
        url = urlunparse(('https',
                          WDD_NETLOC,
                          f'{WDD_BASE_RESULTS_PATH}{path}',
                          '',
                          urlencode(query),
                          ''))
        return url

    def wdr_url(self):
        """WDR URL where this ranking can be seen"""
        if not self.wdr_tournament_id:
            return ''
        return f'{WDR_BASE_URL}tournaments/{self.wdr_tournament_id}'
