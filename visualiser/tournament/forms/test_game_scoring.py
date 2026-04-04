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
Game Scoring Forms Tests for the Diplomacy Tournament Visualiser.
"""
from django.test import TestCase

from tournament.diplomacy import GreatPower
from tournament.forms import GameScoreForm


class GameScoreFormTest(TestCase):
    fixtures = ['game_sets.json']

    def test_name_field_disabled(self):
        form = GameScoreForm()
        self.assertIs(True, form.fields['name'].disabled)
        attrs = form.fields['name'].widget.attrs
        self.assertEqual(attrs['size'], attrs['maxlength'])

    def test_power_fields_exist(self):
        form = GameScoreForm()
        for power in GreatPower.objects.all():
            with self.subTest(power=power.name):
                self.assertIn(power.name, form.fields)
                attrs = form.fields[power.name].widget.attrs
                self.assertEqual(attrs['maxlength'], '10')
                self.assertEqual(attrs['size'], attrs['maxlength'])

    def test_power_fields_optional(self):
        form = GameScoreForm()
        for power in GreatPower.objects.all():
            with self.subTest(power=power.name):
                self.assertIs(False, form.fields[power.name].required)

    def test_has_changed(self):
        initial = {'name': 'Only Game'}
        data = {'name': 'Only Game'}
        for gp in GreatPower.objects.all():
            initial[gp.name] = gp.id
            data[gp.name] = str(gp.id)
        form = GameScoreForm(initial=initial,
                             data=data)
        self.assertIs(False, form.has_changed())
