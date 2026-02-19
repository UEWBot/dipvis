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

from tournament.wdr import (validate_wdr_player_id, validate_wdr_tournament_id,
                            wdr_tournament_as_json)


class WDRTests(TestCase):
    fixtures = ['game_sets.json']

    # validate_wdr_player_id()
    @tag('wdr')
    def test_validate_wdr_player_id_me(self):
        self.assertIsNone(validate_wdr_player_id(4173))

    @tag('wdr')
    def test_validate_wdr_player_id_0(self):
        # 0 is known to be unused
        # Note that this test will fail if the WDR can't be reached
        # (in that case, we assume the id is valid)
        self.assertRaises(ValidationError, validate_wdr_player_id, 0)

    # validate_wdd_tournament_id()
    @tag('wdr')
    def test_validate_wdr_tournament_id_cascadia(self):
        self.assertIsNone(validate_wdr_tournament_id(1545))

    @tag('wdr')
    def test_validate_wdr_tournament_id_0(self):
        # 0 is known to be unused
        # Note that this test will fail if the WDR can't be reached
        # (in that case, we assume the id is valid)
        self.assertRaises(ValidationError, validate_wdr_tournament_id, 0)

    @tag('wdr')
    def test_wdr_tournament_as_json(self):
        json = wdr_tournament_as_json(1545)
        # TODO Validate result
