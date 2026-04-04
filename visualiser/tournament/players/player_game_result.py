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

from tournament.diplomacy import (FIRST_YEAR, TOTAL_SCS, GreatPower,
                                  validate_max_supplycentres, validate_year)
from tournament.wdd import (WDD_BASE_RESULTS_PATH, WDD_NETLOC,
                            validate_wdd_tournament_id)
from tournament.wdr import WDR_BASE_URL, validate_wdr_tournament_id

from .game_results import GameResults
from .player import Player


class PlayerGameResult(models.Model):
    """
    One player's result for a tournament game.

    Used to import background information from external sites.
    """

    tournament_name = models.CharField(max_length=100)
    round_number = models.PositiveSmallIntegerField()
    game_number = models.PositiveSmallIntegerField()
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    power = models.ForeignKey(GreatPower, related_name='+', on_delete=models.CASCADE)
    date = models.DateField()
    position = models.PositiveSmallIntegerField()
    position_equals = models.PositiveSmallIntegerField(blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    final_sc_count = models.PositiveSmallIntegerField(blank=True,
                                                      null=True,
                                                      validators=[validate_max_supplycentres])
    result = models.CharField(max_length=2, choices=GameResults.choices, blank=True)
    year_eliminated = models.PositiveSmallIntegerField(blank=True,
                                                       null=True,
                                                       validators=[validate_year])
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
            models.CheckConstraint(check=Q(result__in=GameResults.values) | Q(result=''),
                                   name='%(class)s_result_valid'),
            models.CheckConstraint(check=Q(year_eliminated__gte=FIRST_YEAR) | Q(year_eliminated__isnull=True),
                                   name='%(class)s_year_eliminated_valid'),
            models.UniqueConstraint(fields=['tournament_name', 'round_number', 'game_number', 'player', 'power'],
                                    name='unique_names_player_power'),
        ]

    def __str__(self):
        return _(u'%(player)s played %(power)s in R %(r_num)d B %(g_num)d at %(tourney)s') % {'player': self.player,
                                                                                              'power': self.power,
                                                                                              'r_num': self.round_number,
                                                                                              'g_num': self.game_number,
                                                                                              'tourney': self.tournament_name}

    def for_same_game(self, pgr):
        """Returns True if the two PlayerGameResults are for the same game"""
        return ((self.tournament_name == pgr.tournament_name) and
                (self.round_number == pgr.round_number) and
                (self.game_number == pgr.game_number) and
                (self.date == pgr.date))

    def game_name(self):
        """Returns a string representing the round and board numbers"""
        return f'R {self.round_number} B {self.game_number}'

    def wdd_url(self):
        """WDD URL where this result can be seen"""
        if not self.wdd_tournament_id:
            return ''
        query = {'id_tournament': self.wdd_tournament_id,
                 'id_round': self.round_number,
                 'id_board': self.game_number}
        url = urlunparse(('https',
                          WDD_NETLOC,
                          f'{WDD_BASE_RESULTS_PATH}tournament_board.php',
                          '',
                          urlencode(query),
                          ''))
        return url

    def wdr_url(self):
        """WDR URL where this ranking can be seen"""
        if not self.wdr_tournament_id:
            return ''
        return f'{WDR_BASE_URL}tournaments/{self.wdr_tournament_id}/boards'
