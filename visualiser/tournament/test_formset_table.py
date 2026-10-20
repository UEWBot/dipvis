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

from django import forms
from django.forms import formset_factory
from django.template.loader import render_to_string
from django.test import SimpleTestCase


class SimpleForm(forms.Form):
    value = forms.IntegerField()


class FormsetTableTests(SimpleTestCase):
    def _render(self, template, num_forms):
        formset = formset_factory(SimpleForm, extra=num_forms)()
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
        html = self._render('formset_table.html', 3)
        self.assertEqual(html.count('<th>Value</th>'), 1)
        self.assertNotIn('<th scope="row">', html)

    def test_row_labels(self):
        html = self._render('formset_table_row_labels.html', 3)
        self.assertEqual(html.count('<th scope="row">'), 3)
        self.assertNotIn('<thead>', html)
