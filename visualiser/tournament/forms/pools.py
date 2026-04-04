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
Forms for pools in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.utils.translation import gettext as _

from tournament.diplomacy import GreatPower

from .fields import RoundPlayerChoiceField


class PoolForm(forms.Form):
    """Form to populate a Pool"""

    def __init__(self, *args, **kwargs):
        # Remove our kwarg from the list
        self.pool = kwargs.pop('pool')
        super().__init__(*args, **kwargs)
        # Create the right number of player fields
        r = self.pool.the_round
        queryset = r.roundplayer_set.order_by('player')
        for n in range(self.pool.board_count * GreatPower.objects.count()):
            self.fields[f'player_{n+1}'] = RoundPlayerChoiceField(queryset=queryset)

    def clean(self):
        """
        Checks for the same player appearing multiple times
        """
        cleaned_data = super().clean()
        r_players = []
        for n in range(self.pool.board_count * GreatPower.objects.count()):
            try:
                r_players.append(cleaned_data[f'player_{n+1}'])
            except KeyError:
                # If there are already errors, cleaned_data may not include all fields
                continue
        for rp in r_players:
            if rp and (r_players.count(rp) > 1):
                raise forms.ValidationError(_('Player %(player)s appears more than once')
                                            % {'player': rp.player})
        return cleaned_data
