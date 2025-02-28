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

from tournament.background import WikipediaBackground
from tournament.background import WDDBackground, InvalidWDDId
from tournament.background import WDRBackground, InvalidWDRId


class WikipediaBackgroundTests(TestCase):

    def test_wikipedia_background_titles(self):
        name = 'Cyrille Sevin'
        flags = ['France']
        bg = WikipediaBackground(name)
        titles = bg.titles()
        self.assertEqual(len(titles), 8)
        for t in titles:
            with self.subTest(title=t):
                if t['Year'] == 1997:
                    if t['Tournament'] == 'EuroDipCon':
                        self.assertEqual(t['European Champion'], name)
                        self.assertEqual(t['European Champion Flags'], flags)
                    else:
                        self.assertEqual(t['World Champion'], name)
                        self.assertEqual(t['World Champion Flags'], flags)
                elif t['Year'] == 2001:
                    self.assertEqual(t['World Champion'], name)
                    self.assertEqual(t['World Champion Flags'], flags)
                elif t['Year'] == 2004:
                    self.assertEqual(t['Third'], name)
                    self.assertEqual(t['Third Flags'], flags)
                elif t['Year'] == 2006:
                    self.assertEqual(t['Second'], name)
                    self.assertEqual(t['Second Flags'], flags)
                elif t['Year'] == 2008:
                    self.assertEqual(t['Second'], name)
                    self.assertEqual(t['Second Flags'], flags)
                elif t['Year'] == 2013:
                    self.assertEqual(t['World Champion'], name)
                    self.assertEqual(t['World Champion Flags'], flags)
                else:
                    # 2015
                    self.assertEqual(t['European Champion'], name)
                    self.assertEqual(t['European Champion Flags'], flags)

    def test_wikipedia_background_nationalities(self):
        # Check that multi-nationals get parsed correctly
        name = 'Antonio Ribeiro da Silva'
        flags = ['France', 'Portugal']
        bg = WikipediaBackground(name)
        titles = bg.titles()
        self.assertEqual(len(titles), 1)
        for t in titles:
            with self.subTest(title=t):
                self.assertEqual(t['Second'], name)
                self.assertEqual(t['Second Flags'], flags)


@tag('wdd')
class WDDBackgroundTests(TestCase):

    INVALID_WDD_ID = 1
    BRANDON_FOGEL_WDD_ID = 13051
    MELINDA_HOLLEY_WDD_ID = 5185
    MEHMET_ALPASLAN_WDD_ID = 14082
    BEN_JAMES_WDD_ID = 14140

    # WDDBackground mostly gets tested implictly when Players are created. Explicitly test invalid wdd ids
    # WDDBackground._wdd_name()
    @tag('wdd')
    def test_wdd_background_wdd_name_invalid(self):
        b = WDDBackground(self.INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b._wdd_name)

    @tag('wdd')
    def test_wdd_background_wdd_firstname_lastname(self):
        cases = {12108: ('Benjy', 'AARONS-RICHARDSON'),
                 13747: ('Vincent', '?'),
                 7089: ('Jo Andre', 'AAKVIK'),
                 1664: ('Emmanuel', 'AH-CHIOW'),
                 # WDD names with accents seem to be messed up right now
                 #4640: ('Stéphane', 'AIT OUHFOUR'),
                 2785: ('Espen H.', 'ANDERSEN'),
                 7699: ('J.C.', 'BLISS'),
                 6505: ('Ray J', 'DION'),
                 10835: ('John Mark', 'EDMUNDSON'),
                 2859: ('Henri', 'FLOTTE DE POUZOLS'),
                 2749: ('Jorn R. T.', 'GRANDE'),
                 7189: ('A Dash', 'GREENTREE'),
                }
        for id in cases.keys():
            with self.subTest(wdd_id=id):
                b = WDDBackground(id)
                self.assertEqual(b.wdd_firstname_lastname(), cases[id])

    # WDDBackground.nationalities()
    @tag('wdd')
    def test_wdd_background_nationalities(self):
        # Mehmet has different location and nationality
        b = WDDBackground(self.MEHMET_ALPASLAN_WDD_ID)
        nats = b.nationalities()
        self.assertEqual(len(nats), 1)
        self.assertEqual(nats[0], 'TUR')

    @tag('wdd')
    def test_wdd_background_nationalities_none(self):
        # Mehmet has different location and nationality
        b = WDDBackground(self.BEN_JAMES_WDD_ID)
        nats = b.nationalities()
        self.assertEqual(len(nats), 0)

    # WDDBackground.finishes()
    @tag('wdd')
    def test_wdd_background_finishes_invalid(self):
        b = WDDBackground(self.INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.finishes)

    @tag('wdd')
    def test_wdd_background_finishes_no_type(self):
        # Brandon has http://world-diplomacy-database.com/php/results/tournament_class.php?id_tournament=1602
        # listed as a tournament, and it has an empty "Type" column
        b = WDDBackground(self.BRANDON_FOGEL_WDD_ID)
        b.finishes()

    # WDDBackground.tournaments()
    @tag('wdd')
    def test_wdd_background_tournaments_invalid(self):
        b = WDDBackground(self.INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.tournaments)

    # WDDBackground.boards()
    @tag('wdd')
    def test_wdd_background_boards_invalid(self):
        b = WDDBackground(self.INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.boards)

    @tag('wdd')
    def test_wdd_background_boards_nc(self):
        # Melinda has three boards listed on
        # http://www.world-diplomacy-database.com/php/results/player_fiche9.php?id_player=5185
        # with a rank of "n.c.". See Bug #117.
        b = WDDBackground(self.MELINDA_HOLLEY_WDD_ID)
        b.boards()

    # WDDBackground.awards()
    @tag('wdd')
    def test_wdd_background_awards_invalid(self):
        b = WDDBackground(self.INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.awards)

    # WDDBackground.rankings()
    @tag('wdd')
    def test_wdd_background_rankings_invalid(self):
        b = WDDBackground(self.INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.rankings)

    # WDDBackground.wpe_scores()
    @tag('wdd')
    def test_wdd_background_wpe_scores_invalid(self):
        b = WDDBackground(self.INVALID_WDD_ID)
        s = b.wpe_scores()
        self.assertEqual(len(s), 0)

    @tag('wdd')
    def test_wdd_background_wpe_scores(self):
        b = WDDBackground(self.MELINDA_HOLLEY_WDD_ID)
        scores = b.wpe_scores()
        for s in scores:
            with self.subTest(s['Tournament']):
                if s['Date'] == '2013-10-13':
                    self.assertEqual(s['Score'], '21.00')
                elif s['Date'] == '2009-09-19':
                    self.assertEqual(s['Score'], '14.40')
                elif s['Date'] == '1998-07-06':
                    self.assertEqual(s['Score'], '4.00')


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
