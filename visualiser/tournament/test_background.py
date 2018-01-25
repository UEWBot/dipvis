# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016 Chris Brand
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

from tournament.background import WDDBackground, InvalidWDDId

INVALID_WDD_ID = 1

@tag('wdd')
class WDDBackgroundTests(TestCase):
    # WikipediaBackground.titles() gets tested implicitly when Players are created

    # WDDBackground mostly gets tested implictly when Players are created. Explicitly test invalid wdd ids
    # WDDBackground.wdd_name()
    def test_wdd_background_wdd_name_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.wdd_name)

    # WDDBackground.finishes()
    def test_wdd_background_finishes_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.finishes)

    # WDDBackground.tournaments()
    def test_wdd_background_tournaments_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.tournaments)

    # WDDBackground.boards()
    def test_wdd_background_boards_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.boards)

    # WDDBackground.awards()
    def test_wdd_background_awards_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.awards)

    # WDDBackground.rankings()
    def test_wdd_background_rankings_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.rankings)
