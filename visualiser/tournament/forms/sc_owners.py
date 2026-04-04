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
Forms for SupplyCentre ownership in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.formsets import BaseFormSet
from django.utils.translation import gettext as _

from tournament.diplomacy import FIRST_YEAR, GreatPower, SupplyCentre


class SCOwnerForm(forms.Form):
    """Form for Supply Centre ownership for one year"""
    # Allow for an initial game-start SC ownership
    year = forms.IntegerField(min_value=FIRST_YEAR-1,
                              required=False,
                              widget=forms.TextInput(attrs={'size': '4'}))

    def __init__(self, *args, **kwargs):
        """Dynamically creates one owner field per SupplyCentre"""
        super().__init__(*args, **kwargs)

        # Create the right country fields
        for sc in SupplyCentre.objects.all():
            self.fields[sc.name] = forms.ModelChoiceField(GreatPower.objects.all(),
                                                          required=False)


class BaseSCOwnerFormset(BaseFormSet):
    """Form to specify who owned which SupplyCentre when for a Game"""
    def clean(self):
        """
        Checks that no year appears more than once
        """
        if any(self.errors):
            return
        years = []
        for form in self.forms:
            year = form.cleaned_data.get('year')
            if not year:
                # Blank form
                continue
            if year in years:
                raise forms.ValidationError(_('Year %(year)s appears more than once')
                                            % {'year': year})
            years.append(year)
        years.sort()
        # Check that SCs never become neutral
        for sc in SupplyCentre.objects.all():
            # Find all the listed owners for this dot
            owners = {}
            for form in self.forms:
                year = form.cleaned_data.get('year')
                owner = form.cleaned_data.get(sc.name)
                owners[year] = (owner, form)
            # Check through them
            owned = False
            for key in years:
                owner, form = owners[key]
                if owner:
                    owned = True
                if owned and not owner:
                    form.add_error(sc.name,
                                   _('Supply Centres should never change from owned to neutral'))
