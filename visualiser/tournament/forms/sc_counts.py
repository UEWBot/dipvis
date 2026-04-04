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
Forms for SupplyCentre counts in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.formsets import BaseFormSet
from django.utils.translation import gettext as _

from tournament.diplomacy import FIRST_YEAR, TOTAL_SCS, GreatPower


class SCCountForm(forms.Form):
    """Form for a Supply Centre count"""
    # Allow for an initial game-start SC count
    year = forms.IntegerField(min_value=FIRST_YEAR-1,
                              widget=forms.TextInput(attrs={'size': '4'}))

    def __init__(self, *args, **kwargs):
        """Dynamically creates one count field per Great Power"""
        super().__init__(*args, **kwargs)

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            # Support just providing counts for some powers (e.g. eliminations)
            # We don't want the default capitalisation
            self.fields[c] = forms.IntegerField(label=_(c),
                                                min_value=0,
                                                max_value=TOTAL_SCS,
                                                required=False,
                                                widget=forms.TextInput(attrs={'size': '2',
                                                                              'maxlength': '2'}))

    def clean(self):
        """Checks that the total SC count is reasonable"""
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        total_scs = 0
        got_full_set = True
        for power in GreatPower.objects.all():
            c = power.name
            dots = cleaned_data.get(c)
            if dots is None:
                # This power is either missing or didn't validate
                got_full_set = False
            else:
                total_scs += dots
        if total_scs > TOTAL_SCS:
            raise forms.ValidationError(_("Total SC count for %(year)d is %(dots)d, more than %(max)d")
                                        % {'year': year,
                                           'dots': total_scs,
                                           'max': TOTAL_SCS})
        if got_full_set:
            # Add a pseudo-field with the number of neutrals, for convenience
            cleaned_data['neutral'] = TOTAL_SCS - total_scs

        return cleaned_data


class BaseSCCountFormset(BaseFormSet):
    """Form to specify SC counts for a Game"""
    def clean(self):
        """
        Checks that no year appears more than once, and that neutrals don't increase
        """
        if any(self.errors):
            return
        years = set()
        neutrals = {}
        for form in self.forms:
            try:
                year = form.cleaned_data['year']
            except KeyError:
                # Blank form
                continue
            if year in years:
                raise forms.ValidationError(_('Year %(year)s appears more than once')
                                            % {'year': year})
            years.add(year)
            # Remember the number of neutrals left
            try:
                neutrals[year] = form.cleaned_data['neutral']
            except KeyError:
                # Don't check years with partial data
                pass
        # Now check that the number of neutrals only goes down
        prev_neutrals = TOTAL_SCS
        for year in sorted(neutrals.keys()):
            if neutrals[year] > prev_neutrals:
                raise forms.ValidationError(_('Neutrals increases from %(before)d to %(after)d in %(year)d')
                                            % {'before': prev_neutrals,
                                               'after': neutrals[year],
                                               'year': year})
            prev_neutrals = neutrals[year]
