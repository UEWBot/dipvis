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
Forms for payment in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.formsets import BaseFormSet


class PaidForm(forms.Form):
    """Form that just provides a checkbox to indicate that a TournamentPlayer has paid"""
    paid = forms.BooleanField(required=False,
                              initial=False)

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tp = kwargs.pop('tp')
        super().__init__(*args, **kwargs)
        self.fields['paid'].label = str(self.tp.player)


class BasePaidFormset(BaseFormSet):
    """Form to specify which TournamentPlayers have paid"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        self.tps = self.tournament.tournamentplayer_set.all()
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            initial = []
            for tp in self.tps:
                initial.append({'paid': tp.paid})
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['tp'] = self.tps[index]
        return super()._construct_form(index, **kwargs)
