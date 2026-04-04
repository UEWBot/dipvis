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
Forms for handicaps in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.formsets import BaseFormSet


class HandicapForm(forms.Form):
    """Form to set one TournamentPlayer's handicap"""
    handicap = forms.FloatField()

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tp = kwargs.pop('tp')
        # Overridable default initial value, like ModelForm
        if 'initial' not in kwargs.keys():
            kwargs['initial'] = {'handicap': self.tp.handicap}
        super().__init__(*args, **kwargs)
        # Set the label to the player's name
        self.fields['handicap'].label = str(self.tp.player)


class BaseHandicapsFormset(BaseFormSet):
    """Formset for setting handicaps for TournamentPlayers"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        # Get the list of TournamentPlayers
        self.tps = list(self.tournament.tournamentplayer_set.all())
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            # And construct initial data from it
            # __init__() uses len(initial) to decide how many forms to create
            initial = []
            for tp in self.tps:
                initial.append({'handicap': tp.handicap})
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['tp'] = self.tps[index]
        return super()._construct_form(index, **kwargs)
