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

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _

from tournament.wdd import WDD_BASE_RESULTS_URL, validate_wdd_player_id

from .player import Player
from .wdd_background import InvalidWDDId, WDDBackground, WDDNotAccessible


class WDDPlayerIdField(models.PositiveIntegerField):
    """A field that represents the unique id for a player in the WDD"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_val = None

    def pre_save(self, model_instance, add):
        # Clear cached WDD Name if WDD id has changed
        model_instance._wdd_firstname = ''
        model_instance._wdd_lastname = ''
        val = super().pre_save(model_instance, add)
        if (val != self._old_val) and not add:
            # Background data is presumably wrong
            model_instance._clear_background()
            self._old_val = val
        return val


class WDDPlayer(models.Model):
    """
    A Single Diplomacy player on the World Diplomacy Database

    A separate model because some players have multiple entries on the WDD
    """
    wdd_player_id = WDDPlayerIdField(unique=True,
                                     validators=[validate_wdd_player_id],
                                     verbose_name=_(u'WDD player id'))
    _wdd_firstname = models.CharField(max_length=40, blank=True)
    _wdd_lastname = models.CharField(max_length=40, blank=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'WDD player'

    def __str__(self):
        return f'{self.player} {self.wdd_player_id}'

    def delete(self, *args, **kwargs):
        # Nuke any background that may have been from this WDDPlayer
        self.player._clear_background()
        return super().delete(*args, **kwargs)

    def _clear_background(self):
        self.player._clear_background()

    def wdd_url(self):
        """URL for this player in the World Diplomacy Database."""
        return f'{WDD_BASE_RESULTS_URL}player_fiche.php?id_player={self.wdd_player_id}'

    def wdd_firstname_lastname(self):
        """
        Name for this player as a 2-tuple, as in the WDD.

        If the name in the WDD cannot be determined, returns ('', '').
        """
        # Read from the WDD if we haven't cached it
        if not self._wdd_firstname and not self._wdd_lastname:
            bg = WDDBackground(self.wdd_player_id)
            try:
                self._wdd_firstname, self._wdd_lastname = bg.wdd_firstname_lastname()
                self.save(update_fields=['_wdd_firstname', '_wdd_lastname'])
            except WDDNotAccessible:
                print(f'Unable to read name from WDD for id {self.wdd_player_id}')
                # Nothing we can do
                pass
            except InvalidWDDId as e:
                # This can only happen if we couldn't get to the WDD when wdd_player_id was validated
                raise ValidationError(_(u'WDD Id %(wdd_id)d is invalid'),
                                      params={'wdd_id': self.wdd_player_id}) from e
        return (self._wdd_firstname, self._wdd_lastname)
