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
from django.forms.models import BaseModelFormSet
from django.utils.translation import gettext as _

from tournament.models import Team
from tournament.players import Player

from .fields import PlayerChoiceField


class TeamForm(forms.ModelForm):
    """Form to create/edit one Team"""

    class Meta:
        model = Team
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament', None)
        super().__init__(*args, **kwargs)

        # Existing rows can infer tournament from instance.
        if self.tournament is None and self.instance.pk:
            self.tournament = self.instance.tournament
        if self.tournament is None:
            raise ValueError('TeamForm requires tournament or an existing Team instance')
        if not self.instance.pk:
            self.instance.tournament = self.tournament

        # Create an appropriate number of player fields
        queryset = Player.objects.filter(tournamentplayer__tournament=self.tournament,
                         tournamentplayer__unranked=False).distinct()
        for n in range(self.tournament.team_size):
            # We allow Teams with as few as one player
            self.fields[f'player_{n}'] = PlayerChoiceField(queryset=queryset,
                                                           required=(n == 0))

        # Populate dynamic player initial values for existing teams.
        if self.instance.pk:
            for i, p in enumerate(self.instance.players.all()):
                self.initial.setdefault(f'player_{i}', p.pk)

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
                raise forms.ValidationError(_('Player %(player)s appears more than once'),
                                            code='duplicate_player_in_team',
                                            params={'player': p})
        return cleaned_data


class BaseTeamsFormset(BaseModelFormSet):
    """Formset for editing Teams"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        if 'queryset' not in kwargs:
            kwargs['queryset'] = self.tournament.team_set.all()
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['tournament'] = self.tournament
        return super()._construct_form(index, **kwargs)

    def clean(self):
        """
        Check for problems with the list of teams

        Checks for duplicate team names and players in multiple teams.
        """
        if any(self.errors):
            # One or more forms is invalid anyway
            return
        names = []
        for form in self.forms:
            name = form.cleaned_data.get('name')
            if name:
                names.append(name)
        for name in names:
            if names.count(name) > 1:
                raise forms.ValidationError(_('Team %(team)s appears more than once'),
                                            code='duplicate_team_name',
                                            params={'team': name})
        # Any duplicates within the page ?
        players = []
        for form in self.forms:
            for n in range(self.tournament.team_size):
                players.append(form.cleaned_data[f'player_{n}'])
        for p in players:
            if p and (players.count(p) > 1):
                raise forms.ValidationError(_('Player %(player)s appears in multiple teams'),
                                            code='duplicate_player_across_teams',
                                            params={'player': p})
