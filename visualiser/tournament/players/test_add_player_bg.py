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

from django_countries.fields import Country

from django.test import TestCase, tag

from tournament.diplomacy import GreatPower
from tournament.players import Player, WDDPlayer

from . import add_player_bg


CHRIS_BRAND_WDD_ID = 4173

CHRIS_BRAND_WDR_ID = 7164
MATT_SHIELDS_WDR_ID = 8838
SPIROS_BOBETSIS_WDR_ID = 1777
MELINDA_HOLLEY_WDR_ID = 8142


class AddPlayerBgTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    # add_player_bg()
    def test_add_player_bg_wiki1(self):
        """Test adding PlayerTitles based on Wikipedia"""
        p = Player.objects.create(first_name='Brandon', last_name='Fogel')
        add_player_bg(p)
        pts = p.playertitle_set.all()
        self.assertEqual(len(pts), 2)
        for pt in pts:
            if pt.year == 2022:
                self.assertEqual(pt.title, 'Virtual Diplomacy League (VDL) Champion')
            elif pt.year == 2023:
                self.assertEqual(pt.title, 'DBNI Diplomat of the Year')
        # Cleanup
        p.delete()

    def test_add_player_bg_wiki2(self):
        """Test adding PlayerTitles based on Wikipedia"""
        p = Player.objects.create(first_name='Graham', last_name='Woodring')
        add_player_bg(p)
        pts = p.playertitle_set.all()
        self.assertEqual(len(pts), 1)
        for pt in pts:
            if pt.year == 2013:
                self.assertEqual(pt.title, 'North American Grand Prix Winner')
        # Cleanup
        p.delete()

    def test_add_player_bg_wiki3(self):
        """Test adding PlayerTitles based on Wikipedia"""
        p = Player.objects.create(first_name='Richard', last_name='Ackerlay')
        add_player_bg(p)
        pts = p.playertitle_set.all()
        self.assertEqual(len(pts), 1)
        for pt in pts:
            if pt.year == 1972:
                self.assertEqual(pt.title, 'North American Champion')
        # Cleanup
        p.delete()

    def test_add_player_no_wdr(self):
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        add_player_bg(p)
        # TODO Validate results

    @tag('wdr')
    def test_add_player_bg_wdr(self):
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        wdd.delete()
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        p = Player.objects.get(wdr_player_id = CHRIS_BRAND_WDR_ID)
        add_player_bg(p)
        # TODO Validate results
        # Cleanup
        WDDPlayer.objects.create(wdd_player_id=CHRIS_BRAND_WDD_ID,
                                 player=p)
        p.wdr_player_id = None
        p.save()

    @tag('slow', 'wdr')
    def test_add_player_bg_no_podiums(self):
        # Spiros has no podium finishes
        p = Player.objects.create(first_name='Spiros',
                                  last_name='Bobetsis',
                                  wdr_player_id=SPIROS_BOBETSIS_WDR_ID)
        add_player_bg(p)
        # Validate results
        ptrs = p.playertournamentranking_set.all()
        self.assertEqual(2, ptrs.count())
        # Cleanup
        p.delete()

    @tag('slow', 'wdr')
    def test_add_player_bg_with_podiums(self):
        # Matt has podium finishes in 2008
        p = Player.objects.create(first_name='Matt',
                                  last_name='Shields',
                                  wdr_player_id=MATT_SHIELDS_WDR_ID)
        add_player_bg(p)
        # Validate results (mostly check that no tournaments get double-counted)
        ptrs = p.playertournamentranking_set.filter(year=2008)
        self.assertEqual(4, ptrs.count())
        # Cleanup
        p.delete()

    # TODO Test handling of invalid dates (PlayerTournamentRanking and PlayerAward)

    @tag('slow', 'wdr')
    def test_add_player_bg_td(self):
        # Matt has tournaments listings for tournaments when he was TD
        p = Player.objects.create(first_name='Matt',
                                  last_name='Shields',
                                  wdr_player_id=MATT_SHIELDS_WDR_ID)
        add_player_bg(p)
        # Validate results
        # Tournament should not be included
        ptrs = p.playertournamentranking_set.filter(tournament='WAC 10 2013')
        self.assertEqual(0, ptrs.count())
        # WAC 10 he played Germany and Turkey, and we want to include those games
        pgrs = p.playergameresult_set.filter(tournament_name='WAC 10 2013')
        self.assertEqual(2, pgrs.count())
        # Cleanup
        p.delete()

    # TODO Test filtering out variant games
    #      There is a variant game in the Windy City Weasels 2012 league,
    #      but we only look at tournament games

    @tag('slow', 'wdr')
    def test_add_player_bg_unranked(self):
        # Melinda has games listed with no ranking (n.c)
        p = Player.objects.create(first_name='Melinda',
                                  last_name='Holley',
                                  wdr_player_id=MELINDA_HOLLEY_WDR_ID)
        add_player_bg(p)
        # Validate results
        pgrs = p.playergameresult_set.filter(tournament_name__contains='DipCon')
        self.assertNotEqual(0, pgrs.count())
        pgrs = pgrs.filter(tournament_name__contains='DipCon 27')
        self.assertEqual(0, pgrs.count())
        # Cleanup
        p.delete()

    def test_add_player_bg_unknown(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        add_player_bg(p)
        # Validate results
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        # Cleanup
        p.delete()

    @tag('slow', 'wdr')
    def test_add_player_bg_wdr_places_nop(self):
        """add_player_bg() from WDR with existing nationalities and location"""
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        self.assertEqual(p.location, '')
        self.assertEqual(len(p.nationalities), 0)
        wdd.delete()
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.nationalities = Country('US')
        p.location = "The moon"
        p.save()
        add_player_bg(p)
        # check results - existing values should be left intact
        p.refresh_from_db()
        self.assertEqual(p.nationalities, [Country('US')])
        self.assertEqual(p.location, 'The moon')
        # Cleanup
        WDDPlayer.objects.create(player=p,
                                 wdd_player_id=CHRIS_BRAND_WDD_ID)
        p.wdr_player_id = None
        p.location = ''
        p.nationalities = []
        p.save()

    @tag('slow', 'wdr')
    def test_add_player_bg_wdr_places(self):
        """add_player_bg() from WDR without existing nationalities and location"""
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        self.assertEqual(p.location, '')
        self.assertEqual(len(p.nationalities), 0)
        wdd.delete()
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        add_player_bg(p)
        # check results - values from WDR should be stored
        p.refresh_from_db()
        self.assertEqual(p.nationalities, [Country('CA')])
        self.assertEqual(p.location, 'Canada')
        # Cleanup
        WDDPlayer.objects.create(player=p,
                                 wdd_player_id=CHRIS_BRAND_WDD_ID)
        p.wdr_player_id = None
        p.location = ''
        p.nationalities = []
        p.save()
