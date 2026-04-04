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
Forms for the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.utils.translation import gettext as _

from tournament.diplomacy import FIRST_YEAR, GreatPower


class DeathYearForm(forms.Form):
    """Form for elimination year of each power"""

    # One shared label, because we expect the form to be displayed in a table
    label = forms.CharField(initial=_('Eliminated (optional):'),
                            disabled=True)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one year field per Great Power"""
        super().__init__(*args, **kwargs)

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            self.fields[c] = forms.IntegerField(min_value=FIRST_YEAR,
                                                required=False,
                                                widget=forms.TextInput(attrs={'size': '4',
                                                                              'maxlength': '4'}))
