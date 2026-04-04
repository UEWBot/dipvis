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
Forms for teams in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.formsets import BaseFormSet
from django.utils.translation import gettext as _

from tournament.models import Team
from tournament.players import Player

from .fields import PlayerChoiceField


class TeamForm(forms.Form):
    """Form to create/edit one Team"""
    name = forms.CharField(max_length=Team.MAX_NAME_LENGTH,
                           strip=True,
                           required=True)

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        self.team = kwargs.pop('team', None)
        # Create an appropriate number of player fields
        queryset = Player.objects.filter(tournamentplayer__in=self.tournament.tournamentplayer_set.order_by()).distinct()
        # Overridable default initial value, like ModelForm
        # TODO This is dead code if we only ever use the formset
        if 'initial' not in kwargs.keys():
            if self.team:
                initial = {'name': self.team.name}
                for i, p in enumerate(self.team.players.all()):
                    initial[f'player_{i}'] = p
                kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        for n in range(self.tournament.team_size):
            # We allow Teams with as few as one player
            self.fields[f'player_{n}'] = PlayerChoiceField(queryset=queryset,
                                                           required=(n == 0))

    def clean(self):
        """
        Checks that the Team is reasonable

        Checks for the same player appearing multiple times
        """
        cleaned_data = super().clean()
        players = []
        for n in range(self.tournament.team_size):
            try:
                players.append(cleaned_data[f'player_{n}'])
            except KeyError:
                # If there are already errors, cleaned_data may not include all fields
                continue
        for p in players:
            if p and (players.count(p) > 1):
                raise forms.ValidationError(_('Player %(player)s appears more than once')
                                            % {'player': p})
        return cleaned_data


class BaseTeamsFormset(BaseFormSet):
    """Formset for editing Teams"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        # Get the list of Teams
        self.teams = list(self.tournament.team_set.all())
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            # And construct initial data from it
            # __init__() uses len(initial) to decide how many forms to create
            initial = []
            for tm in self.teams:
                d = {'name': tm.name}
                for i, p in enumerate(tm.players.all()):
                    d[f'player_{i}'] = p
                initial.append(d)
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special args down to the form itself
        kwargs['tournament'] = self.tournament
        # TODO is the if statement needed?
        if index < len(self.teams):
            kwargs['team'] = self.teams[index]
        return super()._construct_form(index, **kwargs)

    def clean(self):
        """
        Check for problems with the list of teams

        Checks for players in multiple teams
        """
        if any(self.errors):
            # One or more forms is invalid anyway
            return
        # Any duplicates within the page ?
        players = []
        for form in self.forms:
            for n in range(self.tournament.team_size):
                players.append(form.cleaned_data[f'player_{n}'])
        for p in players:
            if p and (players.count(p) > 1):
                raise forms.ValidationError(_('Player %(player)s appears in multiple teams')
                                            % {'player': p})
