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
Forms for Awards in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.models import BaseModelFormSet

from tournament.models import Award, TournamentPlayer

from .fields import TournamentPlayerMultipleChoiceField


class AwardForm(forms.ModelForm):
    """Form to give one Award to TournamentPlayers"""
    players = TournamentPlayerMultipleChoiceField(queryset=TournamentPlayer.objects.none(),
                                                  required=False)

    class Meta:
        model = Award
        fields = ()

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        players_queryset = kwargs.pop('players_queryset', None)
        super().__init__(*args, **kwargs)
        if players_queryset is None:
            players_queryset = self.tournament.tournamentplayer_set.filter(unranked=False)
        self.fields['players'].queryset = players_queryset
        # Set the label to the award name for this row.
        self.fields['players'].label = str(self.instance)
        # Populate initial player selection from current award recipients in this tournament.
        if self.instance.pk and ('players' not in self.initial):
            tps = [tp.id for tp in self.instance.tournamentplayer_set.filter(tournament=self.tournament).order_by()]
            self.initial['players'] = tps


class BaseAwardsFormset(BaseModelFormSet):
    """Formset for giving Awards to TournamentPlayers"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        # Pre-compute the players queryset once to share across all forms
        self._players_queryset = self.tournament.tournamentplayer_set.filter(unranked=False)
        if 'queryset' not in kwargs:
            kwargs['queryset'] = Award.objects.filter(tournamentaward__tournament=self.tournament)
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special kwargs down to the form itself
        kwargs['tournament'] = self.tournament
        kwargs['players_queryset'] = self._players_queryset
        return super()._construct_form(index, **kwargs)
