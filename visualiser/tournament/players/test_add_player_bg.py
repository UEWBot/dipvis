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

import importlib
from datetime import date
from unittest.mock import patch

from django_countries.fields import Country

from django.test import TestCase, tag

from tournament.diplomacy import GreatPower
from tournament.players import (EventKinds, Player, PlayerEventRanking,
                                PlayerTitle,
                                WDDPlayer, WDRNotAccessible)

from . import add_player_bg


CHRIS_BRAND_WDD_ID = 4173

CHRIS_BRAND_WDR_ID = 7164
MATT_SHIELDS_WDR_ID = 8838
SPIROS_BOBETSIS_WDR_ID = 1777
MELINDA_HOLLEY_WDR_ID = 8142


class AddPlayerBgTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    def test_positive_rank_normalizes_wdr_values(self):
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        self.assertEqual(3, add_bg_module._positive_rank('3'))
        self.assertEqual(3, add_bg_module._positive_rank(3))
        self.assertIsNone(add_bg_module._positive_rank('-1'))
        self.assertIsNone(add_bg_module._positive_rank(-1))
        self.assertIsNone(add_bg_module._positive_rank(0))
        self.assertIsNone(add_bg_module._positive_rank(None))
        self.assertIsNone(add_bg_module._positive_rank(''))

    def test_add_player_bg_keeps_wdr_tournament_with_null_rank(self):
        player = Player.objects.create(first_name='Unranked', last_name='Player')
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        tournament = {
            'tournament_id': 1352,
            'tournament_wdd_id': None,
            'tournament_name': 'NADF Masters 2011',
            'tournament_start_date': '2011-01-14',
            'tournament_end_date': '2011-01-16',
            'tournament_kind': 'MASTERS',
            'tournament_event_type': 'Tournament',
            'tournament_player_rank': None,
        }
        with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
            mock_wdr.return_value.tournaments.return_value = [tournament]
            mock_wdr.return_value.boards.return_value = []
            mock_wdr.return_value.awards.return_value = []
            mock_wdr.return_value.rankings.return_value = {}
            mock_wdr.return_value.nationality.return_value = ''
            mock_wdr.return_value.location.return_value = ''
            add_bg_module._add_player_bg_from_wdr(player, 11753)

        ranking = player.playereventranking_set.get(wdr_tournament_id=1352)
        self.assertIsNone(ranking.rank)

    def test_add_player_bg_keeps_partial_wdr_board(self):
        player = Player.objects.create(first_name='Adam', last_name='Silverman')
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        tournament = {
            'tournament_id': 2313,
            'tournament_wdd_id': -1,
            'tournament_name': 'World Masters Diplomacy 2004 S4 (2004-2005)',
            'tournament_start_date': '2004-01-01',
            'tournament_end_date': '2005-12-31',
            'tournament_kind': 'CUP ☆☆☆',
            'tournament_event_type': 'Tournament',
            'tournament_player_rank': 35,
        }
        board = {
            'board_round': 3,
            'board_number': 1,
            'board_is_top': False,
            'board_tournament': 2313,
            'board_power': 'England',
            'board_centers': -1,
            'board_score': None,
            'board_rank': -1,
            'board_year_of_elimination': None,
            'board_url': None,
            'board_variant': 'Standard',
        }
        with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
            mock_wdr.return_value.tournaments.return_value = [tournament]
            mock_wdr.return_value.boards.return_value = [board]
            mock_wdr.return_value.awards.return_value = []
            mock_wdr.return_value.rankings.return_value = {}
            mock_wdr.return_value.nationality.return_value = ''
            mock_wdr.return_value.location.return_value = ''
            add_bg_module._add_player_bg_from_wdr(player, 7213)

        result = player.playergameresult_set.get()
        self.assertEqual('England', str(result.power))
        self.assertIsNone(result.rank)
        self.assertIsNone(result.score)
        self.assertIsNone(result.final_sc_count)
        england = player.background_data()['game_results']['England']
        self.assertEqual(1, england['games'])
        self.assertEqual(0, england['solos']['count'])
        self.assertEqual(0, england['board_tops']['count'])

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

    @patch('builtins.print')
    def test_add_player_bg_wdr_not_accessible(self, mock_print):
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
        mock_print.assert_called_with('Unable to read from WDR for id 9999')
        # Cleanup
        p.delete()

    def test_add_player_bg_reads_wdr_before_wikipedia(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='ThenWiki',
                                  wdr_player_id=9998)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        calls = []

        def fake_add_player_bg_from_wdr(player, wdr_id):
            calls.append('wdr')
            return []

        def fake_titles():
            calls.append('wikipedia')
            return []

        with patch.object(add_bg_module,
                          '_add_player_bg_from_wdr',
                          side_effect=fake_add_player_bg_from_wdr):
            with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
                mock_wiki.return_value.titles.side_effect = fake_titles
                add_player_bg(p)

        self.assertEqual(['wdr', 'wikipedia'], calls)
        # Cleanup
        p.delete()

    def test_add_player_bg_links_wikipedia_title_to_event_ranking(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='TitleLink',
                                  wdr_player_id=9991)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        fake_wdr = {
            'tournaments': [{
                'tournament_id': 7006,
                'tournament_wdd_id': -1,
                'tournament_name': 'WDC 2016',
                'tournament_start_date': '2016-08-01',
                'tournament_end_date': '2016-08-04',
                'tournament_kind': 'WDC',
                'tournament_event_type': 'Tournament',
                'tournament_player_rank': 1,
            }],
            'boards': [],
            'awards': [],
        }
        fake_titles = [{
            'Tournament': 'The World Diplomacy Championship',
            'Year': 2016,
            'World Champion': str(p),
        }]
        with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
            mock_wiki.return_value.titles.return_value = fake_titles
            with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
                mock_wdr.return_value.tournaments.return_value = fake_wdr['tournaments']
                mock_wdr.return_value.boards.return_value = fake_wdr['boards']
                mock_wdr.return_value.awards.return_value = fake_wdr['awards']
                mock_wdr.return_value.rankings.return_value = {}
                mock_wdr.return_value.nationality.return_value = ''
                mock_wdr.return_value.location.return_value = ''
                add_player_bg(p)

        ranking = p.playereventranking_set.get(wdr_tournament_id=7006)
        title = p.playertitle_set.get(title='World Champion', year=2016)
        self.assertEqual(ranking, title.ranking)
        # Cleanup
        p.delete()

    def test_add_player_bg_uses_wikipedia_tournament_kind_to_link_wdc_title(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='KindTitle',
                                  wdr_player_id=9991)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        fake_wdr = {
            'tournaments': [
                {
                    'tournament_id': 7010,
                    'tournament_wdd_id': -1,
                    'tournament_name': 'Some Open 2016',
                    'tournament_start_date': '2016-07-01',
                    'tournament_end_date': '2016-07-03',
                    'tournament_kind': 'OPEN',
                    'tournament_event_type': 'Tournament',
                    'tournament_player_rank': 1,
                },
                {
                    'tournament_id': 7011,
                    'tournament_wdd_id': -1,
                    'tournament_name': 'World DipCon Chicago 2016 Weasel Moot',
                    'tournament_start_date': '2016-08-01',
                    'tournament_end_date': '2016-08-04',
                    'tournament_kind': 'WDC',
                    'tournament_event_type': 'Tournament',
                    'tournament_player_rank': 1,
                },
            ],
            'boards': [],
            'awards': [],
        }
        fake_titles = [{
            'Tournament': 'The World Diplomacy Championship',
            'Year': 2016,
            'World Champion': str(p),
        }]
        with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
            mock_wiki.return_value.titles.return_value = fake_titles
            with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
                mock_wdr.return_value.tournaments.return_value = fake_wdr['tournaments']
                mock_wdr.return_value.boards.return_value = fake_wdr['boards']
                mock_wdr.return_value.awards.return_value = fake_wdr['awards']
                mock_wdr.return_value.rankings.return_value = {}
                mock_wdr.return_value.nationality.return_value = ''
                mock_wdr.return_value.location.return_value = ''
                add_player_bg(p)

        title = p.playertitle_set.get(title='World Champion', year=2016)
        self.assertEqual(7011, title.ranking.wdr_tournament_id)
        self.assertEqual('WDC', title.ranking.tournament_kind)
        # Cleanup
        p.delete()

    def test_add_player_bg_links_multiple_titles_to_one_event_ranking(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='MultiTitle',
                                  wdr_player_id=9990)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        fake_wdr = {
            'tournaments': [{
                'tournament_id': 7007,
                'tournament_wdd_id': -1,
                'tournament_name': 'WDC 2017',
                'tournament_start_date': '2017-08-01',
                'tournament_end_date': '2017-08-04',
                'tournament_kind': 'WDC',
                'tournament_event_type': 'Tournament',
                'tournament_player_rank': 1,
            }],
            'boards': [],
            'awards': [],
        }
        fake_titles = [{
            'Tournament': 'The World Diplomacy Championship',
            'Year': 2017,
            'World Champion': str(p),
            'North American Champion': str(p),
        }]
        with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
            mock_wiki.return_value.titles.return_value = fake_titles
            with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
                mock_wdr.return_value.tournaments.return_value = fake_wdr['tournaments']
                mock_wdr.return_value.boards.return_value = fake_wdr['boards']
                mock_wdr.return_value.awards.return_value = fake_wdr['awards']
                mock_wdr.return_value.rankings.return_value = {}
                mock_wdr.return_value.nationality.return_value = ''
                mock_wdr.return_value.location.return_value = ''
                add_player_bg(p)

        ranking = p.playereventranking_set.get(wdr_tournament_id=7007)
        titles = p.playertitle_set.order_by('title')
        self.assertEqual(2, titles.count())
        self.assertEqual({'North American Champion', 'World Champion'},
                         {title.title for title in titles})
        self.assertEqual({ranking}, {title.ranking for title in titles})
        # Cleanup
        p.delete()

    def test_add_player_bg_uses_wikipedia_event_kind_to_link_titles(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='CircuitTitle',
                                  wdr_player_id=9989)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        fake_wdr = {
            'tournaments': [
                {
                    'tournament_id': 7008,
                    'tournament_wdd_id': -1,
                    'tournament_name': 'Portland Diplomacy Open 2000',
                    'tournament_start_date': '2000-07-08',
                    'tournament_end_date': '2000-07-08',
                    'tournament_kind': 'OPEN',
                    'tournament_event_type': 'Tournament',
                    'tournament_player_rank': 1,
                },
                {
                    'tournament_id': 7009,
                    'tournament_wdd_id': -1,
                    'tournament_name': 'North American Grand Prix 2000',
                    'tournament_start_date': '2000-01-08',
                    'tournament_end_date': '2001-08-05',
                    'tournament_kind': 'NAGP',
                    'tournament_event_type': 'Circuit',
                    'tournament_player_rank': 1,
                },
            ],
            'boards': [],
            'awards': [],
        }
        fake_titles = [{
            'Tournament': 'North American Grand Prix',
            'Year': 2000,
            'Winner': str(p),
        }]
        with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
            mock_wiki.return_value.titles.return_value = fake_titles
            with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
                mock_wdr.return_value.tournaments.return_value = fake_wdr['tournaments']
                mock_wdr.return_value.boards.return_value = fake_wdr['boards']
                mock_wdr.return_value.awards.return_value = fake_wdr['awards']
                mock_wdr.return_value.rankings.return_value = {}
                mock_wdr.return_value.nationality.return_value = ''
                mock_wdr.return_value.location.return_value = ''
                add_player_bg(p)

        title = p.playertitle_set.get(title='North American Grand Prix Winner',
                                      year=2000)
        self.assertEqual(7009, title.ranking.wdr_tournament_id)
        self.assertEqual(EventKinds.CIRCUIT, title.ranking.event_kind)
        # Cleanup
        p.delete()

    @patch('builtins.print')
    def test_wikipedia_event_kind_unknown_event(self, mock_print):
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        title = {'Tournament': 'Mystery Event',
                 'Year': 2026}

        self.assertIsNone(add_bg_module._event_kind_for_wikipedia_event(title))
        mock_print.assert_called_once_with("Unrecognised Wikipedia event Mystery Event in {'Tournament': 'Mystery Event', 'Year': 2026}")

    def test_event_ranking_for_wiki_title_rejects_implausible_year(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='WrongYear')
        ranking = PlayerEventRanking.objects.create(player=p,
                                                    event_name='The World Diplomacy Championship 2018',
                                                    date=date(2018, 8, 4),
                                                    rank=1,
                                                    event_kind=EventKinds.TOURNAMENT)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        title = {'Tournament': 'The World Diplomacy Championship',
                 'Year': 2016,
                 'World Champion': str(p)}

        self.assertIsNone(add_bg_module._event_ranking_for_wiki_title(p, title, ranking.rank))
        # Cleanup
        p.delete()

    @patch('builtins.print')
    def test_event_ranking_for_wiki_title_without_tournament_requires_unique_candidate(self, mock_print):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='NoTournament')
        PlayerEventRanking.objects.create(player=p,
                                          event_name='WDC 2016',
                                          date=date(2016, 8, 4),
                                          rank=1,
                                          event_kind=EventKinds.TOURNAMENT)
        PlayerEventRanking.objects.create(player=p,
                                          event_name='DipCon 2016',
                                          date=date(2016, 7, 4),
                                          rank=1,
                                          event_kind=EventKinds.TOURNAMENT)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        title = {'Year': 2016,
                 'World Champion': str(p)}

        self.assertIsNone(add_bg_module._event_ranking_for_wiki_title(p, title, 1))
        mock_print.assert_called_once_with("Unrecognised Wikipedia event None in {'Year': 2016, 'World Champion': 'Wdr NoTournament'}")
        # Cleanup
        p.delete()

    def test_event_ranking_for_wiki_title_rejects_ambiguous_name_matches(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='AmbiguousCircuit')
        PlayerEventRanking.objects.create(player=p,
                                          event_name='North American Grand Prix 2000 East',
                                          date=date(2001, 8, 5),
                                          rank=1,
                                          event_kind=EventKinds.CIRCUIT)
        PlayerEventRanking.objects.create(player=p,
                                          event_name='North American Grand Prix 2000 West',
                                          date=date(2000, 12, 31),
                                          rank=1,
                                          event_kind=EventKinds.CIRCUIT)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        title = {'Tournament': 'North American Grand Prix',
                 'Year': 2000,
                 'Winner': str(p)}

        self.assertIsNone(add_bg_module._event_ranking_for_wiki_title(p, title, 1))
        # Cleanup
        p.delete()

    @patch('builtins.print')
    def test_update_or_create_playertitle_wiki_handles_save_exception(self, mock_print):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='TitleError')
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        title = {'Tournament': 'The World Diplomacy Championship',
                 'Year': 2016,
                 'World Champion': str(p)}

        with patch.object(add_bg_module.traceback, 'print_exc') as mock_traceback:
            with patch.object(add_bg_module.PlayerTitle.objects,
                              'update_or_create',
                              side_effect=Exception('boom')):
                add_bg_module._update_or_create_playertitle_wiki(p, title)

        self.assertEqual('Failed to save PlayerTitle', mock_print.call_args_list[0].args[0])
        self.assertEqual('player=Wdr TitleError, title=World Champion, year=2016',
                         mock_print.call_args_list[1].args[0])
        mock_traceback.assert_called_once_with()
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
                'tournament_event_type': 'Tournament',
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
        self.assertIsNotNone(pgr.event_ranking)
        self.assertEqual('WDC Test', pgr.event_ranking.event_name)
        # Cleanup
        p.delete()

    def test_add_player_bg_wdr_links_awards_and_results_to_event_ranking(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='Linked',
                                  wdr_player_id=9994)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        fake_wdr = {
            'tournaments': [{
                'tournament_id': 7002,
                'tournament_wdd_id': -1,
                'tournament_name': 'WDC Linked Test',
                'tournament_start_date': '2023-08-01',
                'tournament_end_date': '2023-08-04',
                'tournament_kind': 'WDC',
                'tournament_event_type': 'Tournament',
                'tournament_player_rank': 3,
            }],
            'boards': [{
                'board_round': 2,
                'board_number': 4,
                'board_is_top': False,
                'board_tournament': 7002,
                'board_power': 'Austria',
                'board_centers': 10,
                'board_score': 10.0,
                'board_rank': 2,
                'board_year_of_elimination': None,
                'board_url': '',
                'board_variant': 'Classic',
            }],
            'awards': [{
                'award_country': 'Austria',
                'award_tournament': 7002,
            }],
        }
        with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
            mock_wiki.return_value.titles.return_value = []
            with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
                mock_wdr.return_value.tournaments.return_value = fake_wdr['tournaments']
                mock_wdr.return_value.boards.return_value = fake_wdr['boards']
                mock_wdr.return_value.awards.return_value = fake_wdr['awards']
                mock_wdr.return_value.rankings.return_value = {}
                mock_wdr.return_value.nationality.return_value = ''
                mock_wdr.return_value.location.return_value = ''
                add_player_bg(p)
        pgr = p.playergameresult_set.get(round_number=2, game_number=4)
        pa = p.playeraward_set.get(name='Best Austria')
        self.assertIsNotNone(pgr.event_ranking)
        self.assertIsNotNone(pa.event_ranking)
        self.assertEqual(pgr.event_ranking, pa.event_ranking)
        self.assertEqual('WDC Linked Test', pgr.event_ranking.event_name)
        # Cleanup
        p.delete()

    def test_add_player_bg_stores_tournament_kind(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='Kinds',
                                  wdr_player_id=9993)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        fake_wdr = {
            'tournaments': [
                {
                    'tournament_id': 7003,
                    'tournament_wdd_id': -1,
                    'tournament_name': 'League Event',
                    'tournament_start_date': '2024-01-01',
                    'tournament_end_date': '2024-01-02',
                    'tournament_kind': 'LEAGUE',
                    'tournament_event_type': 'League',
                    'tournament_player_rank': 4,
                },
                {
                    'tournament_id': 7004,
                    'tournament_wdd_id': -1,
                    'tournament_name': 'Cup Event',
                    'tournament_start_date': '2024-02-01',
                    'tournament_end_date': '2024-02-02',
                    'tournament_kind': 'CUP Online',
                    'tournament_event_type': 'Tournament',
                    'tournament_player_rank': 1,
                },
            ],
            'boards': [{
                'board_round': 1,
                'board_number': 2,
                'board_is_top': False,
                'board_tournament': 7003,
                'board_power': 'Austria',
                'board_centers': 9,
                'board_score': 9.0,
                'board_rank': 2,
                'board_year_of_elimination': None,
                'board_url': '',
                'board_variant': 'Classic',
            }],
            'awards': [],
        }
        with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
            mock_wiki.return_value.titles.return_value = []
            with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
                mock_wdr.return_value.tournaments.return_value = fake_wdr['tournaments']
                mock_wdr.return_value.boards.return_value = fake_wdr['boards']
                mock_wdr.return_value.awards.return_value = fake_wdr['awards']
                mock_wdr.return_value.rankings.return_value = {}
                mock_wdr.return_value.nationality.return_value = ''
                mock_wdr.return_value.location.return_value = ''
                add_player_bg(p)
        per_league = p.playereventranking_set.get(wdr_tournament_id=7003)
        self.assertEqual('LEAGUE', per_league.tournament_kind)
        self.assertEqual(EventKinds.LEAGUE, per_league.event_kind)
        per_cup = p.playereventranking_set.get(wdr_tournament_id=7004)
        self.assertEqual('CUP Online', per_cup.tournament_kind)
        self.assertEqual(EventKinds.TOURNAMENT, per_cup.event_kind)
        pgr = p.playergameresult_set.get(round_number=1, game_number=2)
        self.assertEqual(per_league, pgr.event_ranking)
        # Cleanup
        p.delete()

    def test_add_player_bg_updates_existing_event_ranking_by_name_and_date(self):
        p = Player.objects.create(first_name='Wdr',
                                  last_name='Existing',
                                  wdr_player_id=9992)
        existing = PlayerEventRanking.objects.create(player=p,
                                                     event_name='Thailand Diplomacy Championship 2022-2023',
                                                     date=date(2023, 12, 15),
                                                     rank=2)
        add_bg_module = importlib.import_module('tournament.players.add_player_bg')
        fake_wdr = {
            'tournaments': [{
                'tournament_id': 7005,
                'tournament_wdd_id': -1,
                'tournament_name': 'Thailand Diplomacy Championship 2022-2023',
                'tournament_start_date': '2022-01-01',
                'tournament_end_date': '2023-12-15',
                'tournament_kind': 'LEAGUE',
                'tournament_event_type': 'League',
                'tournament_player_rank': 4,
            }],
            'boards': [{
                'board_round': 1,
                'board_number': 2,
                'board_is_top': False,
                'board_tournament': 7005,
                'board_power': 'Austria',
                'board_centers': 9,
                'board_score': 9.0,
                'board_rank': 2,
                'board_year_of_elimination': None,
                'board_url': '',
                'board_variant': 'Classic',
            }],
            'awards': [],
        }
        with patch.object(add_bg_module, 'WikipediaBackground') as mock_wiki:
            mock_wiki.return_value.titles.return_value = []
            with patch.object(add_bg_module, 'WDRBackground') as mock_wdr:
                mock_wdr.return_value.tournaments.return_value = fake_wdr['tournaments']
                mock_wdr.return_value.boards.return_value = fake_wdr['boards']
                mock_wdr.return_value.awards.return_value = fake_wdr['awards']
                mock_wdr.return_value.rankings.return_value = {}
                mock_wdr.return_value.nationality.return_value = ''
                mock_wdr.return_value.location.return_value = ''
                add_player_bg(p)
        existing.refresh_from_db()
        self.assertEqual(1, p.playereventranking_set.count())
        self.assertEqual(7005, existing.wdr_tournament_id)
        self.assertEqual(EventKinds.LEAGUE, existing.event_kind)
        self.assertEqual(4, existing.rank)
        pgr = p.playergameresult_set.get(round_number=1, game_number=2)
        self.assertEqual(existing, pgr.event_ranking)
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
        self.assertEqual(4, ptrs.count())
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
        ptrs = p.playereventranking_set.filter(date__year=2008)
        self.assertEqual(6, ptrs.count())
        # Cleanup
        p.delete()

    @patch('builtins.print')
    def test_add_player_bg_invalid_dates(self, mock_print):
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
            'tournament_event_type': 'Tournament',
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
        mock_print.assert_called_with('Skipping No Date Tournament for Test InvalidDate with no date')
        # The records with invalid dates should be silently skipped.
        self.assertEqual(0, p.playereventranking_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        # Cleanup
        p.delete()

    @tag('slow', 'wdr')
    @patch('builtins.print')
    def test_add_player_bg_td(self, mock_print):
        # Matt has tournaments listings for tournaments when he was TD
        p = Player.objects.create(first_name='Matt',
                                  last_name='Shields',
                                  wdr_player_id=MATT_SHIELDS_WDR_ID)
        add_player_bg(p)
        # Validate results
        # The event is retained even though WDR has no tournament rank.
        ptrs = p.playereventranking_set.filter(event_name='WAC 10 2013')
        self.assertEqual(1, ptrs.count())
        self.assertIsNone(ptrs.first().rank)
        # WAC 10 he played Germany and Turkey, and we want to include those games
        pgrs = p.playergameresult_set.filter(event_ranking__event_name='WAC 10 2013')
        self.assertEqual(2, pgrs.count())
        self.assertEqual(2, pgrs.exclude(event_ranking__isnull=True).count())
        # Cleanup
        p.delete()

    @patch('builtins.print')
    def test_add_player_bg_variant_games_filtered(self, mock_print):
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
            'tournament_event_type': 'Tournament',
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
        mock_print.assert_called_with('Skipping board with variant Empire')
        pgrs = p.playergameresult_set.all()
        self.assertEqual(1, pgrs.count())
        self.assertEqual(1, pgrs.first().round_number)  # only the Standard board
        # Cleanup
        p.delete()

    @tag('slow', 'wdr')
    @patch('builtins.print')
    def test_add_player_bg_unranked(self, mock_print):
        # Melinda has games listed with no ranking (n.c)
        p = Player.objects.create(first_name='Melinda',
                                  last_name='Holley',
                                  wdr_player_id=MELINDA_HOLLEY_WDR_ID)
        add_player_bg(p)
        # Validate results
        pgrs = p.playergameresult_set.filter(event_ranking__event_name__contains='DipCon')
        self.assertNotEqual(0, pgrs.count())
        pgrs = pgrs.filter(event_ranking__event_name__contains='DipCon 27')
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
