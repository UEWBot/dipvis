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

from django.test import TestCase, tag

from . import InvalidWDRId, WDRBackground


@tag('wdr')
class WDRBackgroundTests(TestCase):

    INVALID_WDR_ID = 0
    CHRIS_BRAND_WDR_ID = 7164

    # WDRBackground mostly gets tested implictly when Players are created. Explicitly test invalid wdd ids
    @tag('wdr')
    def test_wdr_background_id_invalid(self):
        self.assertRaises(InvalidWDRId, WDRBackground, self.INVALID_WDR_ID)

    # WDRBackground.wdd_id()
    @tag('wdr')
    def test_wdr_background_wdd_id(self):
        b = WDRBackground(self.CHRIS_BRAND_WDR_ID)
        self.assertEqual(4173, b.wdd_id())

    # WDRBackground.firstname_lastname()
    @tag('wdr')
    def test_wdr_background_firstname_lastname(self):
        b = WDRBackground(self.CHRIS_BRAND_WDR_ID)
        self.assertEqual(('Chris', 'Brand'), b.firstname_lastname())

    # WDRBackground.nationality()
    @tag('wdr')
    def test_wdr_background_nationality(self):
        b = WDRBackground(self.CHRIS_BRAND_WDR_ID)
        self.assertEqual('CA', b.nationality())

    # WDRBackground.location()
    @tag('wdr')
    def test_wdr_background_location(self):
        b = WDRBackground(self.CHRIS_BRAND_WDR_ID)
        self.assertEqual('CA', b.location())

    # TODO WDRBackground.tournaments()

    # TODO WDRBackground.boards()

    # TODO WDRBackground.awards()

    # TODO WDRBackground.rankings()
