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

from django.test import TestCase

from . import position_str


class PositionStrTests(TestCase):
    # position_str()
    def test_position_str_first(self):
        tests = {1: '1st',
                 2: '2nd',
                 3: '3rd',
                 4: '4th',
                 5: '5th',
                 6: '6th',
                 7: '7th',
                 8: '8th',
                 9: '9th',
                 10: '10th',
                 11: '11th',
                 12: '12th',
                 13: '13th',
                 14: '14th',
                 21: '21st',
                 22: '22nd',
                 23: '23rd',
                 24: '24th',
                 99: '99th',
                 100: '100th',
                 101: '101st',
                }
        for k, v in tests.items():
            with self.subTest(k):
                self.assertEqual(position_str(k), v)
