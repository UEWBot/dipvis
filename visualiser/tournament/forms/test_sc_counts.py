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
SC Count Forms Tests for the Diplomacy Tournament Visualiser.
"""
from django.forms.formsets import formset_factory
from django.test import TestCase

from tournament.diplomacy import GreatPower

from . import BaseSCCountFormset, SCCountForm


class SCCountFormTest(TestCase):
    fixtures = ['game_sets.json']

    def test_year_field(self):
        form = SCCountForm()
        attrs = form.fields['year'].widget.attrs
        self.assertEqual(attrs['size'], '4')

    def test_power_fields(self):
        form = SCCountForm()
        for power in GreatPower.objects.all():
            with self.subTest(power=power):
                self.assertIs(False, form.fields[power.name].required)
                attrs = form.fields[power.name].widget.attrs
                self.assertEqual(attrs['size'], '2')
                self.assertEqual(attrs['size'], attrs['maxlength'])

    def test_success(self):
        """Everything is ok"""
        data = {'year': 1902,
                'Austria-Hungary': 5,
                'England': 6,
                'France': 6,
                'Germany': 2,
                'Italy': 5,
                'Russia': 4,
                'Turkey': 5,
               }
        form = SCCountForm(data=data)
        self.assertIs(True, form.is_valid())

    def test_year_1900(self):
        """1900 should be accepted"""
        data = {'year': 1900,
                'Austria-Hungary': 5,
                'England': 6,
                'France': 6,
                'Germany': 2,
                'Italy': 5,
                'Russia': 4,
                'Turkey': 5,
               }
        form = SCCountForm(data=data)
        self.assertIs(True, form.is_valid())

    def test_year_1899(self):
        """1899 should not be accepted"""
        data = {'year': 1899,
                'Austria-Hungary': 5,
                'England': 6,
                'France': 6,
                'Germany': 2,
                'Italy': 5,
                'Russia': 4,
                'Turkey': 5,
               }
        form = SCCountForm(data=data)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'year', 'Ensure this value is greater than or equal to 1900.')

    def test_negative_sc_count(self):
        """One power has lost more than all their dots"""
        data = {'year': 1905,
                'Austria-Hungary': 4,
                'England': 5,
                'France': -1,
                'Germany': 5,
                'Italy': 4,
                'Russia': 4,
                'Turkey': 4,
               }
        form = SCCountForm(data=data)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'France', 'Ensure this value is greater than or equal to 0.')

    def test_power_with_too_many_dots(self):
        """One power has more than all the dots"""
        data = {'year': 1920,
                'Austria-Hungary': 0,
                'England': 0,
                'France': 0,
                'Germany': 0,
                'Italy': 35,
                'Russia': 0,
                'Turkey': 0,
               }
        form = SCCountForm(data=data)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'Italy', 'Ensure this value is less than or equal to 34.')

    def test_too_many_dots_in_total(self):
        """More than 34 in total"""
        data = {'year': 1920,
                'Austria-Hungary': 5,
                'England': 5,
                'France': 5,
                'Germany': 5,
                'Italy': 5,
                'Russia': 5,
                'Turkey': 5,
               }
        form = SCCountForm(data=data)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        self.assertFormError(form, None, 'Total SC count for 1920 is 35, more than 34')

    def test_fake_neutral_field(self):
        """Ensure that the extra 'neutral' field gets added"""
        data = {'year': 1902,
                'Austria-Hungary': 5,
                'England': 6,
                'France': 6,
                'Germany': 2,
                'Italy': 5,
                'Russia': 4,
                'Turkey': 5,
               }
        form = SCCountForm(data=data)
        self.assertIs(True, form.is_valid())
        self.assertEqual(form.cleaned_data['neutral'], 1)

    def test_missing_powers(self):
        """Check handling of years with just an elimination"""
        data = {'year': 1902,
                'England': 0,
               }
        form = SCCountForm(data=data)
        self.assertIs(True, form.is_valid())
        # In this case, the neutrals count should not be generated
        self.assertNotIn('neutral', form.cleaned_data)

    def test_has_changed(self):
        data = {'year': '1903',
                'England': '5'}
        initial = {'year': 1903,
                   'England': 5}
        form = SCCountForm(data=data, initial=initial)
        self.assertIs(False, form.has_changed())


class BaseSCCountFormsetTest(TestCase):
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

        cls.SCCountFormset = formset_factory(SCCountForm,
                                             formset=BaseSCCountFormset)
        # ManagementForm data
        cls.data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }

    def test_success(self):
        """Everything is ok"""
        data = self.data.copy()
        for i in range(2):
            data[f'form-{i}-Austria-Hungary'] = 4 + i
            data[f'form-{i}-England'] = 4 + i
            data[f'form-{i}-France'] = 4 + i
            data[f'form-{i}-Germany'] = 4 + i
            data[f'form-{i}-Italy'] = 4 + i
            data[f'form-{i}-Russia'] = 3 + i
            data[f'form-{i}-Turkey'] = 4 + i
            data[f'form-{i}-year'] = 1902 + i
        formset = self.SCCountFormset(data)
        self.assertIs(True, formset.is_valid())

    def test_one_form_blank(self):
        """One form left empty"""
        data = self.data.copy()
        data['form-0-Austria-Hungary'] = 4
        data['form-0-England'] = 4
        data['form-0-France'] = 4
        data['form-0-Germany'] = 4
        data['form-0-Italy'] = 4
        data['form-0-Russia'] = 3
        data['form-0-Turkey'] = 4
        data['form-0-year'] = 1902
        formset = self.SCCountFormset(data)
        self.assertIs(True, formset.is_valid())

    def test_elimination_year(self):
        """Year with just an elimination"""
        data = self.data.copy()
        data['form-0-Austria-Hungary'] = 4
        data['form-0-England'] = 4
        data['form-0-France'] = 4
        data['form-0-Germany'] = 4
        data['form-0-Italy'] = 4
        data['form-0-Russia'] = 3
        data['form-0-Turkey'] = 4
        data['form-0-year'] = 1902
        data['form-1-Italy'] = 0
        data['form-1-year'] = 1904
        formset = self.SCCountFormset(data)
        self.assertIs(True, formset.is_valid())

    def test_form_error(self):
        """Something wrong in one of the forms"""
        data = self.data.copy()
        for i in range(2):
            data[f'form-{i}-Austria-Hungary'] = 4 + i
            data[f'form-{i}-England'] = 4 + i
            data[f'form-{i}-France'] = 4 + i
            data[f'form-{i}-Germany'] = 4 + i
            data[f'form-{i}-Italy'] = 4 + i
            data[f'form-{i}-Russia'] = 3 + i
            # Negative SC counts are not allowed
            data[f'form-{i}-Turkey'] = i - 1
            data[f'form-{i}-year'] = 1902 + i
        formset = self.SCCountFormset(data)
        self.assertIs(False, formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

    def test_duplicate_year(self):
        """One year is repeated"""
        data = self.data.copy()
        for i in range(2):
            data[f'form-{i}-Austria-Hungary'] = 4 + i
            data[f'form-{i}-England'] = 4 + i
            data[f'form-{i}-France'] = 4 + i
            data[f'form-{i}-Germany'] = 4 + i
            data[f'form-{i}-Italy'] = 4 + i
            data[f'form-{i}-Russia'] = 3 + i
            data[f'form-{i}-Turkey'] = 4 + i
            data[f'form-{i}-year'] = 1902
        formset = self.SCCountFormset(data)
        self.assertIs(False, formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, None, None, 'Year 1902 appears more than once')

    def test_duplicate_elimination_year(self):
        """One year with partial data is repeated"""
        # TODO Ideally, we'd probably allow this as long as there are no inconsistencies
        # (e.g. the data here)
        data = self.data.copy()
        data['form-0-England'] = 0
        data['form-0-year'] = 1904
        data['form-1-Italy'] = 0
        data['form-1-year'] = 1904
        formset = self.SCCountFormset(data)
        self.assertIs(False, formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, None, None, 'Year 1904 appears more than once')

    def test_duplicate_partial_year1(self):
        """One year with partial data is repeated"""
        # TODO Ideally, we'd probably allow this as long as there are no inconsistencies
        # (e.g. the data here)
        data = self.data.copy()
        data['form-0-England'] = 3
        data['form-0-year'] = 1904
        data['form-1-Italy'] = 6
        data['form-1-year'] = 1904
        formset = self.SCCountFormset(data)
        self.assertIs(False, formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, None, None, 'Year 1904 appears more than once')

    def test_duplicate_partial_year2(self):
        """One year with partial data is repeated"""
        data = self.data.copy()
        data['form-0-England'] = 3
        data['form-0-year'] = 1904
        data['form-1-England'] = 6
        data['form-1-year'] = 1904
        formset = self.SCCountFormset(data)
        self.assertIs(False, formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, None, None, 'Year 1904 appears more than once')

    def test_neutrals_increase(self):
        """SupplyCentres become neutral"""
        data = self.data.copy()
        for i in range(2):
            data[f'form-{i}-Austria-Hungary'] = 4
            data[f'form-{i}-England'] = 4
            data[f'form-{i}-France'] = 4
            data[f'form-{i}-Germany'] = 4
            data[f'form-{i}-Italy'] = 4
            data[f'form-{i}-Russia'] = 3
            data[f'form-{i}-year'] = 1902 + i
        data['form-0-Turkey'] = 5
        data['form-1-Turkey'] = 3
        formset = self.SCCountFormset(data)
        self.assertIs(False, formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, None, None, 'Neutrals increases from 6 to 8 in 1903')
