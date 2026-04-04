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
Forms for draws in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.utils.translation import gettext as _

from tournament.diplomacy import FIRST_YEAR, GreatPower
from tournament.models import DrawSecrecy, Seasons


class DrawForm(forms.Form):
    """Form for a draw vote"""
    year = forms.IntegerField(min_value=FIRST_YEAR)
    season = forms.ChoiceField(choices=Seasons.choices)
    proposer = forms.ModelChoiceField(queryset=GreatPower.objects.all(),
                                      required=False,
                                      to_field_name='name')

    def __init__(self, *args, **kwargs):
        """Adds powers field if concession or DIAS"""
        # Remove our special kwargs from the list
        concession = kwargs.pop('concession')
        is_dias = kwargs.pop('dias')
        secrecy = kwargs.pop('secrecy')
        super().__init__(*args, **kwargs)

        if concession:
            self.fields['powers'] = forms.ModelChoiceField(queryset=GreatPower.objects.all(),
                                                           label=_('Concede to'),
                                                           to_field_name='name')
        elif not is_dias:
            self.fields['powers'] = forms.ModelMultipleChoiceField(queryset=GreatPower.objects.all(),
                                                                   to_field_name='name',
                                                                   widget=forms.SelectMultiple(attrs={'size': '7'}))
        if secrecy == DrawSecrecy.SECRET:
            self.fields['passed'] = forms.BooleanField(initial=False,
                                                       required=False)
        elif secrecy == DrawSecrecy.COUNTS:
            self.fields['votes_in_favour'] = forms.IntegerField(min_value=0,
                                                                max_value=GreatPower.objects.count())
        else:
            raise AssertionError(f'Unexpected draw secrecy value {secrecy}')
