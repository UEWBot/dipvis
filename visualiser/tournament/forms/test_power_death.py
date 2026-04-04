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
Power Death Forms Tests for the Diplomacy Tournament Visualiser.
"""
from django.test import TestCase

from tournament.diplomacy import GreatPower

from . import DeathYearForm


class DeathYearFormTest(TestCase):
    fixtures = ['game_sets.json']

    def test_label_field_disabled(self):
        form = DeathYearForm()
        self.assertIs(True, form.fields['label'].disabled)

    def test_all_power_fields_not_required(self):
        form = DeathYearForm()
        for power in GreatPower.objects.all():
            with self.subTest(power=power):
                self.assertIs(False, form.fields[power.name].required)
                attrs = form.fields[power.name].widget.attrs
                self.assertEqual(attrs['size'], '4')
                self.assertEqual(attrs['size'], attrs['maxlength'])

    def test_year_1900(self):
        data = {'France': 1900,
               }
        form = DeathYearForm(data=data)
        self.assertIs(False, form.is_valid())

    def test_year_1901(self):
        data = {'Austria-Hungary': 1901,
               }
        form = DeathYearForm(data=data)
        self.assertIs(True, form.is_valid())

    def test_has_changed(self):
        data = {'Germany': '1905'}
        initial = {'Germany': 1905}
        form = DeathYearForm(data=data, initial=initial)
        self.assertIs(False, form.has_changed())
