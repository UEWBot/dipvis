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
from django.forms.formsets import BaseFormSet

from tournament.models import Award, TournamentPlayer

from .fields import TournamentPlayerMultipleChoiceField


class AwardForm(forms.Form):
    """Form to give one Award to TournamentPlayers"""
    award = forms.ModelChoiceField(queryset=Award.objects.all(),
                                   widget=forms.HiddenInput())
    players = TournamentPlayerMultipleChoiceField(queryset=TournamentPlayer.objects.none(),
                                                  required=False)

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        tournament = kwargs.pop('tournament')
        award_name = kwargs.pop('award_name')
        super().__init__(*args, **kwargs)
        # TODO we could create this queryset just once, in the formset
        self.fields['players'].queryset = tournament.tournamentplayer_set.filter(unranked=False)
        # Set the label to the award's name
        self.fields['players'].label = award_name


class BaseAwardsFormset(BaseFormSet):
    """Formset for giving Awards to TournamentPlayers"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        # Get the list of Awards
        self.awards = list(self.tournament.awards.all())
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            # And construct initial data from it
            # __init__() uses len(initial) to decide how many forms to create
            initial = []
            for award in self.awards:
                tps = [tp.id for tp in award.tournamentplayer_set.filter(tournament=self.tournament).order_by()]
                initial.append({'award': award.id, 'players': tps})
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special kwargs down to the form itself
        kwargs['tournament'] = self.tournament
        kwargs['award_name'] = str(self.awards[index])
        return super()._construct_form(index, **kwargs)
