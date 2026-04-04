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
Forms for check-in in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.formsets import BaseFormSet


class SelfCheckInForm(forms.Form):
    """Form for one TournamentPlayer to selfcheck-in for a single Round"""
    playing = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tp = kwargs.pop('tp')
        self.round = kwargs.pop('round')
        super().__init__(*args, **kwargs)
        # Set the label appropriately
        label = _('Round %(number)d') % {'number': self.round.number()}
        if self.round.is_finished:
            label += _(' (Finished)')
        elif not self.round.enable_check_in:
            label += _(' (Self-check-in not yet allowed)')
        elif self.round.game_set.exists():
            label += _(' (Self-check-in closed)')
        self.fields['playing'].label = label
        # Set read-only if it's too late or if self-check-in isn't enabled
        readonly = (not self.round.enable_check_in) or self.round.game_set.exists()
        if readonly:
            self.fields['playing'].disabled = True


class BaseCheckInFormset(BaseFormSet):
    """Formset to provide self-check-in for every Round for a single TournamentPlayer"""
    def __init__(self, *args, **kwargs):
        # Remove our kwarg from the list
        self.tp = kwargs.pop('tp')
        # Get the list of Rounds
        self.rounds = list(self.tp.tournament.round_set.all())
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            initial = []
            for r in self.rounds:
                initial.append({'playing': r.roundplayer_set.filter(player=self.tp.player).exists()})
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['tp'] = self.tp
        kwargs['round'] = self.rounds[index]
        return super()._construct_form(index, **kwargs)
