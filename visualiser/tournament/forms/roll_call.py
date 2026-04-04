# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2026 Chris Brand
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

"""
Forms for roll call in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.formsets import BaseFormSet
from django.utils.translation import gettext as _

from tournament.players import Player

from .fields import PlayerChoiceField


class PlayerRoundForm(forms.Form):
    """Form to specify whether a player is available to play a specific round"""

    # We want all Players to be available to be chosen,
    # as this provides an easy way to add TournamentPlayers
    player = PlayerChoiceField(queryset=Player.objects.all())
    present = forms.BooleanField(required=False,
                                 initial=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'center-checkbox'}))
    standby = forms.BooleanField(required=False,
                                 initial=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'center-checkbox'}))
    sandboxer = forms.BooleanField(required=False,
                                   initial=False,
                                   widget=forms.CheckboxInput(attrs={'class': 'center-checkbox'}))
    rounds_played = forms.IntegerField(required=False,
                                       disabled=True,
                                       widget=forms.TextInput(attrs={'class': 'readonly-look'}),
                                       min_value=0)

    def clean(self):
        """Checks that standby players and sandboxers are present"""
        cleaned_data = super().clean()
        if (cleaned_data['standby'] or cleaned_data['sandboxer']) and not cleaned_data['present']:
            raise forms.ValidationError(_('Standbys/sandboxers should be flagged as present'))
        return cleaned_data


class BasePlayerRoundFormset(BaseFormSet):
    """Form to specify which players are playing in a round"""

    def clean(self):
        """Checks that no player appears more than once"""
        if any(self.errors):
            return
        players = set()
        for form in self.forms:
            player = form.cleaned_data.get('player')
            if not player:
                continue
            if player in players:
                raise forms.ValidationError(_('Player %(player)s appears more than once')
                                            % {'player': player})
            players.add(player)

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        super().__init__(*args, **kwargs)
