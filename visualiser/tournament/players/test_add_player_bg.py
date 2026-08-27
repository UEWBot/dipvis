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
from unittest.mock import patch
import importlib

from django.test import TestCase, tag

from tournament.diplomacy import GreatPower
from tournament.players import Player, WDDPlayer, WDRNotAccessible

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
        # Without a WDR player ID, no tournament rankings or game results should
        # be added (those come exclusively from WDR).
        self.assertEqual(0, p.playereventranking_set.count())
        self.assertEqual(0, p.playergameresult_set.count())

    def test_add_player_bg_wdr_not_accessible(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='Unavailable',
                                  wdr_player_id=9999)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
            mock_wiki.return_value.titles.return_value = []
            with patch.object(add_bg_module,
                              '_add_player_bg_from_wdr',
                              side_effect=WDRNotAccessible):
                add_player_bg(p)
        # Cleanup
        p.delete()

    def test_add_player_bg_wdr_sets_top_board_flag(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='TopBoard',
                                  wdr_player_id=9998)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        fake_wdr = {
            'tournaments': [{
                'tournament_id': 7001,
                'tournament_wdd_id': -1,
                'tournament_name': 'WDC Test',
                'tournament_start_date': '2024-08-01',
                'tournament_end_date': '2024-08-04',
                'tournament_kind': 'WDC',
                'tournament_player_rank': 9,
            }],
            'boards': [{
                'board_round': 7,
                'board_number': 1,
                'board_is_top': True,
                'board_tournament': 7001,
                'board_power': 'Austria',
                'board_centers': 8,
                'board_score': 8.0,
                'board_rank': 2,
                'board_year_of_elimination': None,
                'board_url': '',
                'board_variant': 'Classic',
            }],
        }
        with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
            mock_wiki.return_value.titles.return_value = []
            with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
                mock_wdr.return_value.tournaments.return_value = fake_wdr['tournaments']
                mock_wdr.return_value.boards.return_value = fake_wdr['boards']
                mock_wdr.return_value.awards.return_value = []
                mock_wdr.return_value.rankings.return_value = {}
                mock_wdr.return_value.nationality.return_value = ''
                mock_wdr.return_value.location.return_value = ''
                add_player_bg(p)
        pgr = p.playergameresult_set.get(round_number=7, game_number=1)
        self.assertIs(True, pgr.is_top_board)
        # Cleanup
        p.delete()

    @tag('wdr')
    def test_add_player_bg_wdr(self):
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        wdd.delete()
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        p = Player.objects.get(wdr_player_id = CHRIS_BRAND_WDR_ID)
        ptr_count_before = p.playereventranking_set.count()
        pgr_count_before = p.playergameresult_set.count()
        add_player_bg(p)
        # WDR data should have been loaded on top of whatever was already present.
        self.assertGreater(p.playereventranking_set.count(), ptr_count_before)
        self.assertGreater(p.playergameresult_set.count(), pgr_count_before)
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
        ptrs = p.playereventranking_set.all()
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
        ptrs = p.playereventranking_set.filter(year=2008)
        self.assertEqual(4, ptrs.count())
        # Cleanup
        p.delete()

    def test_add_player_bg_invalid_dates(self):
        """Tournaments and awards with no dates are skipped without crashing."""
        p = Player.objects.create(first_name='Test', last_name='InvalidDate',
                                  wdr_player_id=9997)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        fake_tournaments = [{
            'tournament_id': 8001,
            'tournament_wdd_id': -1,
            'tournament_name': 'No Date Tournament',
            'tournament_start_date': None,
            'tournament_end_date': None,
            'tournament_kind': 'CUP',
            'tournament_player_rank': 1,
        }]
        fake_awards = [{
            'award_country': 'France',
            'award_tournament': 8001,
        }]
        with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
            mock_wiki.return_value.titles.return_value = []
            with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
                mock_wdr.return_value.tournaments.return_value = fake_tournaments
                mock_wdr.return_value.boards.return_value = []
                mock_wdr.return_value.awards.return_value = fake_awards
                mock_wdr.return_value.rankings.return_value = {}
                mock_wdr.return_value.nationality.return_value = ''
                mock_wdr.return_value.location.return_value = ''
                add_player_bg(p)  # must not raise
        # The records with invalid dates should be silently skipped.
        self.assertEqual(0, p.playereventranking_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        # Cleanup
        p.delete()

    @tag('slow', 'wdr')
    def test_add_player_bg_td(self):
        # Matt has tournaments listings for tournaments when he was TD
        p = Player.objects.create(first_name='Matt',
                                  last_name='Shields',
                                  wdr_player_id=MATT_SHIELDS_WDR_ID)
        add_player_bg(p)
        # Validate results
        # Tournament should not be included
        ptrs = p.playereventranking_set.filter(event_name='WAC 10 2013')
        self.assertEqual(0, ptrs.count())
        # WAC 10 he played Germany and Turkey, and we want to include those games
        pgrs = p.playergameresult_set.filter(event_name='WAC 10 2013')
        self.assertEqual(2, pgrs.count())
        # Cleanup
        p.delete()

    def test_add_player_bg_variant_games_filtered(self):
        """Boards for non-standard variants are excluded; standard boards are kept."""
        p = Player.objects.create(first_name='Test', last_name='Variant',
                                  wdr_player_id=9996)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        fake_tournaments = [{
            'tournament_id': 9001,
            'tournament_wdd_id': -1,
            'tournament_name': 'Mix Tournament',
            'tournament_start_date': '2012-01-01',
            'tournament_end_date': '2012-01-02',
            'tournament_kind': 'CUP',
            'tournament_player_rank': 3,
        }]
        fake_boards = [
            {
                'board_round': 1, 'board_number': 1, 'board_is_top': False,
                'board_tournament': 9001, 'board_power': 'Austria',
                'board_centers': 8, 'board_score': 8.0, 'board_rank': 2,
                'board_year_of_elimination': None, 'board_url': '',
                'board_variant': 'Standard',
            },
            {
                'board_round': 2, 'board_number': 1, 'board_is_top': False,
                'board_tournament': 9001, 'board_power': 'France',
                'board_centers': 5, 'board_score': 5.0, 'board_rank': 3,
                'board_year_of_elimination': None, 'board_url': '',
                'board_variant': 'Empire',  # variant - should be excluded
            },
        ]
        with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
            mock_wiki.return_value.titles.return_value = []
            with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
                mock_wdr.return_value.tournaments.return_value = fake_tournaments
                mock_wdr.return_value.boards.return_value = fake_boards
                mock_wdr.return_value.awards.return_value = []
                mock_wdr.return_value.rankings.return_value = {}
                mock_wdr.return_value.nationality.return_value = ''
                mock_wdr.return_value.location.return_value = ''
                add_player_bg(p)
        pgrs = p.playergameresult_set.all()
        self.assertEqual(1, pgrs.count())
        self.assertEqual(1, pgrs.first().round_number)  # only the Standard board
        # Cleanup
        p.delete()

    @tag('slow', 'wdr')
    def test_add_player_bg_unranked(self):
        # Melinda has games listed with no ranking (n.c)
        p = Player.objects.create(first_name='Melinda',
                                  last_name='Holley',
                                  wdr_player_id=MELINDA_HOLLEY_WDR_ID)
        add_player_bg(p)
        # Validate results
        pgrs = p.playergameresult_set.filter(event_name__contains='DipCon')
        self.assertNotEqual(0, pgrs.count())
        pgrs = pgrs.filter(event_name__contains='DipCon 27')
        self.assertEqual(0, pgrs.count())
        # Cleanup
        p.delete()

    def test_add_player_bg_unknown(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        add_player_bg(p)
        # Validate results
        self.assertEqual(0, p.playereventranking_set.count())
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
