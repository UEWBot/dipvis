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
Forms for round scoring in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.formsets import BaseFormSet

from tournament.models import TournamentPlayer
from tournament.players import Player

from .fields import TournamentPlayerChoiceField


class PlayerRoundScoreForm(forms.Form):
    """Form to enter round score(s) for a player"""
    tp = TournamentPlayerChoiceField(queryset=TournamentPlayer.objects.none(),
                                     widget=forms.HiddenInput())
    player = forms.CharField(max_length=Player._meta.get_field('first_name').max_length + Player._meta.get_field('last_name').max_length + 1,
                             disabled=True,
                             widget=forms.TextInput(attrs={'size': '20'}))

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        self.last_round_num = kwargs.pop('last_round_num')
        super().__init__(*args, **kwargs)

        self.fields['tp'].queryset = self.tournament.tournamentplayer_set.prefetch_related('player')

        # Create the right number of round fields, with the right ones read-only
        for i in range(1, 1 + self.last_round_num):
            name = f'round_{i}'
            # Create an additional field to show the game scores for that round
            game_scores_name = f'game_scores_{i}'
            self.fields[game_scores_name] = forms.CharField(max_length=10,
                                                            required=False,
                                                            disabled=True)
            self.fields[name] = forms.FloatField(required=False,
                                                 widget=forms.TextInput(attrs={'size': '10',
                                                                               'maxlength': '40'}))

        # Last field is for the overall tournament score
        self.fields['overall_score'] = forms.FloatField(required=False,
                                                        widget=forms.TextInput(attrs={'size': '10',
                                                                                      'maxlength': '20'}))


class BasePlayerRoundScoreFormset(BaseFormSet):
    """Form to enter round scores for all players"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        super().__init__(*args, **kwargs)
        # Cache value we'll pass to each form's constructor
        self.last_round_num = self.tournament.round_set.count()

    def _construct_form(self, index, **kwargs):
        # Pass the three special args down to the form itself
        kwargs['tournament'] = self.tournament
        kwargs['last_round_num'] = self.last_round_num
        return super()._construct_form(index, **kwargs)
