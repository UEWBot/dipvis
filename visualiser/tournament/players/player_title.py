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

from django.db import models
from django.utils.translation import gettext as _

from .player import Player
from .player_tournament_ranking import PlayerTournamentRanking


class PlayerTitle(models.Model):
    """
    A title won by a player.

    Used to import background information from external sites.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    year = models.PositiveSmallIntegerField()
    updated = models.DateTimeField(auto_now=True)
    # Cross-reference to more information about the tournament where the title was won
    ranking = models.ForeignKey(PlayerTournamentRanking,
                                on_delete=models.SET_NULL,
                                blank=True,
                                null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'title', 'year'],
                                    name='unique_player_title_year'),
        ]

    def __str__(self):
        s = _(u'%(player)s won %(title)s in %(year)s') % {'player': self.player,
                                                          'title': self.title,
                                                          'year': self.year}
        return s
