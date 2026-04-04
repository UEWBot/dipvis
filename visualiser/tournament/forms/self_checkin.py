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
Forms for self check-in in the Diplomacy Tournament Visualiser.
"""

from django import forms


class EnableCheckInForm(forms.Form):
    """Form to enable self-check-ins for roll call"""

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        round_num = kwargs.pop('round_num', None)
        super().__init__(*args, **kwargs)

        if round_num:
            first_round_num = last_round_num = this_round_num = round_num
        else:
            first_round_num = 1
            last_round_num = self.tournament.round_set.count()
            # current_round() could return None, if all rounds are over
            cr = self.tournament.current_round()
            if cr:
                this_round_num = cr.number()
            else:
                # Use a round number higher than all that exist
                this_round_num = last_round_num + 1

        # Create the right number of enable fields, with the right ones read-only
        for i in range(first_round_num, 1 + last_round_num):
            name = f'round_{i}'
            readonly = (i < this_round_num)
            self.fields[name] = forms.BooleanField(required=False, initial=False)
            if readonly:
                self.fields[name].disabled = True
