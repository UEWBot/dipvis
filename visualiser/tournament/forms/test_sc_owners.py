# Diplomacy Tournament Visualiser
# Copyright (C) 2019-2026 Chris Brand
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
SC Ownership Forms Tests for the Diplomacy Tournament Visualiser.
"""
from django.forms.formsets import formset_factory
from django.test import TestCase

from tournament.diplomacy import GreatPower, SupplyCentre

from . import BaseSCOwnerFormset, SCOwnerForm


class SCOwnerFormTest(TestCase):
    fixtures = ['game_sets.json']

    def test_field_count(self):
        form = SCOwnerForm()
        self.assertEqual(len(form.fields), 1 + SupplyCentre.objects.count())

    def test_year(self):
        form = SCOwnerForm()
        attrs = form.fields['year'].widget.attrs
        self.assertEqual(attrs['size'], '4')

    def test_required(self):
        form = SCOwnerForm()
        for field in form.fields:
            with self.subTest(field=field):
                self.assertIs(False, form.fields[field].required)

    def test_year_1900(self):
        """1900 should be accepted"""
        form = SCOwnerForm(data={'year': 1900})
        self.assertIs(True, form.is_valid())

    def test_year_1899(self):
        """1899 should not be accepted"""
        form = SCOwnerForm(data={'year': 1899})
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'year', 'Ensure this value is greater than or equal to 1900.')

    def test_has_changed(self):
        initial = {'year': 1903}
        data = {'year': '1903'}
        for sc in SupplyCentre.objects.all():
            if sc.initial_owner:
                initial[sc.name] = sc.initial_owner
                data[sc.name] = str(sc.initial_owner_id)
        form = SCOwnerForm(data=data, initial=initial)
        self.assertIs(False, form.has_changed())


class BaseSCOwnerFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        cls.SCOwnerFormset = formset_factory(SCOwnerForm,
                                             formset=BaseSCOwnerFormset)
        # ManagementForm data
        cls.data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }
        cls.row_data = {}
        for sc in SupplyCentre.objects.all():
            cls.row_data[sc.name] = sc.initial_owner

    def test_success(self):
        """Everything is ok"""
        data = self.data.copy()
        for i in range(2):
            for key, val in self.row_data.items():
                if val:
                    data[f'form-{i}-{key}'] = val.pk
            data[f'form-{i}-year'] = 1902 + i
        data['form-0-Belgium'] = self.france.pk
        data['form-1-Belgium'] = self.germany.pk
        formset = self.SCOwnerFormset(data)
        self.assertIs(True, formset.is_valid())

    def test_leave_one_form_blank(self):
        """Everything is ok, one form left blank"""
        data = self.data.copy()
        for key, val in self.row_data.items():
            if val:
                data[f'form-0-{key}'] = val.pk
        data['form-0-year'] = 1904
        data['form-0-Belgium'] = self.france.pk
        formset = self.SCOwnerFormset(data)
        self.assertIs(True, formset.is_valid())

    def test_blank_one_form(self):
        """
        With initial data (game started)

        Everything is ok, one form blanked
        """
        data = self.data.copy()
        for key, val in self.row_data.items():
            if val:
                data[f'form-0-{key}'] = val.pk
        data['form-0-year'] = 1904
        data['form-0-Belgium'] = self.france.pk
        initial = []
        for year in range(1901, 1905):
            scs = {'year': year}
            for sc in SupplyCentre.objects.all():
                scs[str(sc)] = sc.initial_owner
            initial.append(scs)
        formset = self.SCOwnerFormset(data, initial=initial)
        self.assertIs(True, formset.is_valid())

    def test_form_error(self):
        """Error in one of the forms"""
        data = self.data.copy()
        for i in range(2):
            for key, val in self.row_data.items():
                if val:
                    data[f'form-{i}-{key}'] = val.pk
            # First year will be 1899, which is invalid
            data[f'form-{i}-year'] = 1899 + i
        data['form-0-Belgium'] = self.france.pk
        data['form-1-Belgium'] = self.germany.pk
        formset = self.SCOwnerFormset(data)
        self.assertIs(False, formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

    def test_duplicate_year(self):
        """Duplicate years"""
        data = self.data.copy()
        for i in range(2):
            for key, val in self.row_data.items():
                if val:
                    data[f'form-{i}-{key}'] = val.pk
            data[f'form-{i}-year'] = 1902
        data['form-0-Belgium'] = self.france.pk
        data['form-1-Belgium'] = self.germany.pk
        formset = self.SCOwnerFormset(data)
        self.assertIs(False, formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, None, None, 'Year 1902 appears more than once')

    def test_scs_become_neutral(self):
        """SC changes from owned to neutral"""
        data = self.data.copy()
        for i in range(2):
            for key, val in self.row_data.items():
                if val:
                    data[f'form-{i}-{key}'] = val.pk
            data[f'form-{i}-year'] = 1902 + i
        data['form-0-Belgium'] = self.france.pk
        formset = self.SCOwnerFormset(data)
        self.assertIs(False, formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, 1, 'Belgium', 'Supply Centres should never change from owned to neutral')
