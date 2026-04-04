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
Forms for seeder bias in the Diplomacy Tournament Visualiser.
"""

from django import forms

from tournament.models import SeederBias, TournamentPlayer

from .fields import TournamentPlayerChoiceField


class SeederBiasForm(forms.ModelForm):
    """Form to create/update a SeederBias object"""
    player1 = TournamentPlayerChoiceField(queryset=TournamentPlayer.objects.none())
    player2 = TournamentPlayerChoiceField(queryset=TournamentPlayer.objects.none())

    class Meta:
        model = SeederBias
        fields = ['player1', 'player2']

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        super().__init__(*args, **kwargs)
        self.fields['player1'].queryset = self.tournament.tournamentplayer_set.prefetch_related('player')
        self.fields['player2'].queryset = self.tournament.tournamentplayer_set.prefetch_related('player')
