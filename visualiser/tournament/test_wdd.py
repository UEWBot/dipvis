# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2024 Chris Brand
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

from django.core.exceptions import ValidationError
from django.test import TestCase, tag

from tournament.wdd import wdd_url_to_tournament_id
from tournament.wdd import validate_wdd_player_id, validate_wdd_tournament_id


class WDDTests(TestCase):

    # validate_wdd_player_id()
    @tag('wdd')
    def test_validate_wdd_player_id_me(self):
        self.assertIsNone(validate_wdd_player_id(4173))

    @tag('wdd')
    def test_validate_wdd_player_id_1(self):
        # 1 is known to be unused
        # Note that this test will fail if the WDD can't be reached
        # (in that case, we assume the id is valid)
        self.assertRaises(ValidationError, validate_wdd_player_id, 1)

    # validate_wdd_tournament_id()
    @tag('wdd')
    def test_validate_wdd_tournament_id_cascadia(self):
        self.assertIsNone(validate_wdd_tournament_id(1545))

    @tag('wdd')
    def test_validate_wdd_tournament_id_0(self):
        # 0 is known to be unused
        # Note that this test will fail if the WDD can't be reached
        # (in that case, we assume the id is valid)
        self.assertRaises(ValidationError, validate_wdd_tournament_id, 0)

    # wdd_url_to_tournament_id()
    def test_wdd_url_to_tournament_id_valid(self):
        self.assertEqual(wdd_url_to_tournament_id('https://world-diplomacy-database.com/php/results/tournament_class.php?id_tournament=1766'), 1766)

    def test_wdd_url_to_tournament_id_invalid(self):
        self.assertEqual(wdd_url_to_tournament_id('https://world-diplomacy-database.com/php/results/tournament_list.php'), 0)
