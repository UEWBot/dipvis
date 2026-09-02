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

from tournament.wdd import (WDD_BASE_RESULTS_PATH, WDD_NETLOC,
                            validate_wdd_tournament_id)
from tournament.wdr import WDR_BASE_URL, validate_wdr_tournament_id

from .event_kinds import EventKinds
from .player import Player
from .rank_str import rank_str
from .wdd_player import WDDPlayer


class PlayerEventRanking(models.Model):
    """
    An event ranking for a player.

    Used to import background information from external sites.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    event_name = models.CharField(max_length=100)
    rank = models.PositiveSmallIntegerField(blank=True, null=True)
    date = models.DateField()
    event_kind = models.CharField(max_length=1,
                                  choices=EventKinds.choices,
                                  default=EventKinds.TOURNAMENT,
                                  help_text=_(u'Kind of event (tournament, league, circuit)'))
    tournament_kind = models.CharField(max_length=20,
                                       blank=True,
                                       null=True,
                                       help_text=_(u'Type of tournament on WDR/WDD'))
    wdd_tournament_id = models.PositiveIntegerField(validators=[validate_wdd_tournament_id],
                                                    verbose_name=_(u'WDD tournament id'),
                                                    blank=True,
                                                    null=True)
    wdr_tournament_id = models.PositiveIntegerField(validators=[validate_wdr_tournament_id],
                                                    verbose_name=_(u'WDR tournament id'),
                                                    blank=True,
                                                    null=True)
    wpe_score = models.FloatField(blank=True,
                                  null=True,
                                  help_text=_('World Performance Evaluation score'))
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'event_name', 'date'],
                                    name='unique_player_event_name_date'),
        ]

    def __str__(self):
        if self.rank is None:
            s = _(u'%(player)s was unranked at %(event_name)s') % {'player': self.player,
                                                                   'event_name': self.event_name}
        else:
            s = _(u'%(player)s came %(rank)s at %(event_name)s') % {'player': self.player,
                                                                        'rank': rank_str(self.rank),
                                                                        'event_name': self.event_name}
        if self.event_name[-4:] != str(self.date.year):
            s += _(u' in %(year)d') % {'year': self.date.year}
        return s

    def wdd_url(self):
        """WDD URL where this ranking can be seen"""
        if not self.wdd_tournament_id:
            return ''
        try:
            wdd = WDDPlayer.objects.get(player=self.player)
        except (WDDPlayer.DoesNotExist, WDDPlayer.MultipleObjectsReturned):
            return ''
        if self.event_kind == EventKinds.CIRCUIT:
            query = {'id_circuit': self.wdd_tournament_id,
                     'id_player': wdd.wdd_player_id}
            url = urlunparse(('https',
                              WDD_NETLOC,
                              f'{WDD_BASE_RESULTS_PATH}circuit_player.php',
                              '',
                              urlencode(query),
                              ''))
        else:
            query = {'id_tournament': self.wdd_tournament_id,
                     'id_player': wdd.wdd_player_id}
            url = urlunparse(('https',
                              WDD_NETLOC,
                              f'{WDD_BASE_RESULTS_PATH}tournament_player.php',
                              '',
                              urlencode(query),
                              ''))
        return url

    def wdr_url(self):
        """WDR URL where this ranking can be seen"""
        if not self.wdr_tournament_id:
            return ''
        return f'{WDR_BASE_URL}tournaments/{self.wdr_tournament_id}'
