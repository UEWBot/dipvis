# Diplomacy Tournament Visualiser
# Copyright (C) 2026 Chris Brand
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
formset_table.html Tests for the Diplomacy Tournament Visualiser.
"""
import re

from django import forms
from django.forms import formset_factory
from django.template.loader import render_to_string
from django.test import SimpleTestCase

from tournament.test_form_templates import assert_aria_describedby_targets_exist


class SimpleForm(forms.Form):
    value = forms.IntegerField()


class TwoFieldForm(forms.Form):
    name = forms.CharField()
    value = forms.IntegerField()


class HiddenFieldForm(forms.Form):
    hidden_value = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField()


class HelpTextForm(forms.Form):
    name = forms.CharField(help_text='Some help')
    value = forms.IntegerField(help_text='More help')


class FormsetTableTests(SimpleTestCase):
    def _render(self, template, num_forms, form=SimpleForm):
        formset = formset_factory(form, extra=num_forms)()
        return render_to_string(template, {'formset': formset})

    def test_tbody_balanced(self):
        for template in ['formset_table.html', 'formset_table_row_labels.html']:
            for num_forms in [0, 1, 3]:
                with self.subTest(template=template, num_forms=num_forms):
                    html = self._render(template, num_forms)
                    self.assertEqual(html.count('<tbody>'), html.count('</tbody>'))
                    expected = 1 if num_forms or template == 'formset_table_row_labels.html' else 0
                    self.assertEqual(html.count('<tbody>'), expected)
                    self.assertEqual(html.count('<tr class='), num_forms)

    def test_column_headings(self):
        html = self._render('formset_table.html', 3, form=TwoFieldForm)
        self.assertEqual(html.count('<th scope="col">Name</th>'), 1)
        self.assertEqual(html.count('<th scope="col">Value</th>'), 1)
        self.assertNotIn('<th>', html)

    def test_first_column_is_row_heading(self):
        html = self._render('formset_table.html', 3, form=TwoFieldForm)
        self.assertEqual(html.count('<th scope="row">'), 3)
        self.assertEqual(html.count('<td>'), 3)
        self.assertEqual(len(re.findall(r'<th[ >]', html)), html.count('</th>'))
        self.assertEqual(len(re.findall(r'<td[ >]', html)), html.count('</td>'))

    def test_hidden_field_errors_in_error_cell(self):
        """Hidden field errors should be in the trailing error cell, not the row heading."""
        data = {'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '0',
                'form-0-hidden_value': 'not-a-number',
                'form-0-name': 'Name'}
        formset = formset_factory(HiddenFieldForm)(data)
        self.assertFalse(formset.is_valid())
        html = render_to_string('formset_table.html', {'formset': formset})
        row_heading = re.search(r'<th scope="row">(.*?)</th>', html, re.DOTALL).group(1)
        self.assertNotIn('errorlist', row_heading)
        self.assertInHTML('<td><ul class="errorlist nonfield"><li>(Hidden field hidden_value) Enter a whole number.</li></ul></td>',
                          html)

    def test_row_labels(self):
        html = self._render('formset_table_row_labels.html', 3)
        self.assertEqual(html.count('<th scope="row">'), 3)
        self.assertNotIn('<thead>', html)

    def test_help_text(self):
        """Help text should be shown for each field in each row, and linked to its field."""
        for template, fields in [('formset_table.html', {'name': 'Some help', 'value': 'More help'}),
                                 ('formset_table_row_labels.html', {'name': 'Some help'})]:
            with self.subTest(template=template):
                html = self._render(template, 2, form=HelpTextForm)
                for n in range(2):
                    for name, text in fields.items():
                        self.assertInHTML(f'<span class="helptext" id="id_form-{n}-{name}_helptext">{text}</span>',
                                          html)
                        self.assertIn(f'aria-describedby="id_form-{n}-{name}_helptext"', html)
                assert_aria_describedby_targets_exist(self, html)

    def test_errors_linked(self):
        """Fields with errors refer to them with aria-describedby, so they must exist."""
        data = {'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '0',
                'form-0-name': '',
                'form-0-value': 'not-a-number'}
        for template in ['formset_table.html', 'formset_table_row_labels.html']:
            with self.subTest(template=template):
                formset = formset_factory(HelpTextForm)(data)
                self.assertFalse(formset.is_valid())
                html = render_to_string(template, {'formset': formset})
                self.assertIn('id_form-0-name_error', html)
                assert_aria_describedby_targets_exist(self, html)

    def test_row_labels_hidden_field_errors_after_field(self):
        """Hidden field errors should be identified, and shown after the field."""
        data = {'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '0',
                'form-0-hidden_value': 'not-a-number',
                'form-0-name': 'Name'}
        formset = formset_factory(HiddenFieldForm)(data)
        self.assertFalse(formset.is_valid())
        html = render_to_string('formset_table_row_labels.html', {'formset': formset})
        self.assertEqual(html.count('errorlist'), 1)
        error = html.index('(Hidden field hidden_value) Enter a whole number.')
        self.assertGreater(error, html.index('name="form-0-name"'))
        self.assertLess(error, html.index('</td>'))
