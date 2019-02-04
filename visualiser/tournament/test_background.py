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
    @tag('wdd')
    def test_wdd_background_wdd_name_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.wdd_name)

    def test_wdd_background_wdd_firstname_lastname(self):
        cases = {13747: ('Benjy', 'AARONS-RICHARDSON'),
                 13747: ('Vincent', '?'),
                 7089: ('Jo Andre', 'AAKVIK'),
                 1664: ('Emmanuel', 'AH-CHIOW'),
                 4640: ('Stéphane', 'AIT OUHFOUR'),
                 2785: ('Espen H.', 'ANDERSEN'),
                 7699: ('J.C.', 'BLISS'),
                 6505: ('Ray J', 'DION'),
                 10835: ('John Mark', 'EDMUNDSON'),
                 2859: ('Henri', 'FLOTTE DE POUZOLS'),
                 2749: ('Jorn R. T.', 'GRANDE'),
                 7189: ('A Dash', 'GREENTREE'),
                }
        for id in cases.keys():
            b = WDDBackground(id)
            self.assertEqual(b.wdd_firstname_lastname(), cases[id])

    # WDDBackground.finishes()
    @tag('wdd')
    def test_wdd_background_finishes_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.finishes)

    # WDDBackground.tournaments()
    @tag('wdd')
    def test_wdd_background_tournaments_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.tournaments)

    # WDDBackground.boards()
    @tag('wdd')
    def test_wdd_background_boards_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.boards)

    # WDDBackground.awards()
    @tag('wdd')
    def test_wdd_background_awards_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.awards)

    # WDDBackground.rankings()
    @tag('wdd')
    def test_wdd_background_rankings_invalid(self):
        b = WDDBackground(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.rankings)
