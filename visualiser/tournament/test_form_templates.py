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
Form template Tests for the Diplomacy Tournament Visualiser.
"""
import uuid
from types import SimpleNamespace

from django import forms
from django.template.loader import render_to_string
from django.test import SimpleTestCase


class HiddenFieldForm(forms.Form):
    hidden_value = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField()

    # Attributes used by rounds/get_seven.html
    all_standbys_needed = False
    sitters = 0
    doubles = 0
    standbys = 0


class HelpTextForm(forms.Form):
    name = forms.CharField(help_text='Some help')


class HiddenFieldTemplateTests(SimpleTestCase):
    """Templates that render a form field-by-field should handle hidden fields."""

    def _check(self, template, extra_context):
        form = HiddenFieldForm({'hidden_value': 'not-a-number', 'name': 'Name'})
        self.assertFalse(form.is_valid())
        html = render_to_string(template, {'form': form, **extra_context})
        # The hidden field should be present, but without a label
        self.assertEqual(html.count('name="hidden_value"'), 1)
        self.assertNotIn('for="id_hidden_value"', html)
        # Its error should identify the field
        self.assertEqual(html.count('Enter a whole number.'), 1)
        self.assertIn('(Hidden field hidden_value) Enter a whole number.', html)
        # The visible field should still be rendered with its label
        self.assertIn('name="name"', html)
        self.assertIn('<label for="id_name">', html)

    def test_enter_url(self):
        self._check('backstabbr/enter_url.html', {})

    def test_get_seven(self):
        self._check('rounds/get_seven.html',
                    {'tournament': SimpleNamespace(id=1),
                     'round': SimpleNamespace(number=1),
                     'playing': 7,
                     'standbys': 0})

    def test_vote(self):
        for concession in [False, True]:
            with self.subTest(concession=concession):
                self._check('games/vote.html',
                            {'tournament': SimpleNamespace(id=1),
                             'game': SimpleNamespace(name='G1', final_year=1905),
                             'player_count': 3,
                             'concession': concession})

    def test_player_entry(self):
        self._check('tournaments/player_entry.html',
                    {'tournament': SimpleNamespace(id=1),
                     'uuid': uuid.uuid4(),
                     'prefs_list': []})

    def test_player_entry_help_text(self):
        """Help text should be shown, and linked to its field."""
        form = HelpTextForm()
        html = render_to_string('tournaments/player_entry.html',
                                {'form': form,
                                 'tournament': SimpleNamespace(id=1),
                                 'uuid': uuid.uuid4(),
                                 'prefs_list': []})
        self.assertInHTML('<p class="helptext" id="id_name_helptext">Some help</p>', html)
        self.assertIn('aria-describedby="id_name_helptext"', html)
