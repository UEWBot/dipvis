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

from tournament.background import WDD_Background, InvalidWDDId

INVALID_WDD_ID = 1

class WDDBackgroundTests(TestCase):
    # Wikipedia_Background.titles() gets tested implicitly when Players are created

    # WDD_Background mostly gets tested implictly when Players are created. Explicitly test invalid wdd ids
    # WDD_Background.wdd_name()
    def test_wdd_background_wdd_name_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.wdd_name)

    # WDD_Background.finishes()
    def test_wdd_background_finishes_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.finishes)

    # WDD_Background.tournaments()
    def test_wdd_background_tournaments_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.tournaments)

    # WDD_Background.boards()
    def test_wdd_background_boards_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.boards)

    # WDD_Background.awards()
    def test_wdd_background_awards_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.awards)

    # WDD_Background.rankings()
    def test_wdd_background_awards_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.rankings)
