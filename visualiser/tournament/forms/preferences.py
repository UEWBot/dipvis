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
Forms for preferences in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.formsets import BaseFormSet

from tournament.diplomacy import validate_preference_string
from tournament.models import TournamentPlayer


class PrefsForm(forms.ModelForm):
    """Form for one TournamentPlayer's Preferences"""
    prefs = forms.CharField(max_length=7,
                            strip=True,
                            required=False,
                            validators=[validate_preference_string])

    class Meta:
        model = TournamentPlayer
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Overridable default initial value, like ModelForm
        if 'prefs' not in self.initial:
            self.initial['prefs'] = self.instance.prefs_string()
        # Set the label to the player's name
        self.fields['prefs'].label = str(self.instance.player)

    def save(self, commit=True):
        tp = super().save(commit=commit)
        tp.create_preferences_from_string(self.cleaned_data['prefs'])
        return tp


class BasePrefsFormset(BaseFormSet):
    """Form to specify Preferences for every TournamentPlayer"""
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
                initial.append({'prefs': tp.prefs_string()})
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['instance'] = self.tps[index]
        return super()._construct_form(index, **kwargs)
