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

from datetime import date, timedelta

from django.test import TestCase

from tournament.diplomacy import GreatPower
from tournament.players import Player, WDDPlayer

from . import PlayerEventRanking, PlayerGameResult


class PlayerGameResultTests(TestCase):
    """Test the PlayerGameResult class"""
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')
        cls.best_ranking = PlayerEventRanking.objects.create(player=Player.objects.first(),
                                                             event_name='Best Tournament',
                                                             date=date.today())
        cls.worst_ranking = PlayerEventRanking.objects.create(player=Player.objects.first(),
                                                              event_name='Worst Tournament',
                                                              date=date.today() - timedelta(days=1))

    # PlayerGameResult.for_same_game()
    def test_playergameresult_same(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        per2 = PlayerEventRanking.objects.create(player=p2,
                                                 event_name=self.best_ranking.event_name,
                                                 date=self.best_ranking.date)
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(event_ranking=self.best_ranking,
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                position=2)
        pgr2 = PlayerGameResult(event_ranking=per2,
                                round_number=pgr1.round_number,
                                game_number=pgr1.game_number,
                                player=p2,
                                power=self.russia,
                                position=4)
        self.assertIs(True, pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_tournament(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        per2 = PlayerEventRanking.objects.create(player=p2,
                                                 event_name=self.worst_ranking.event_name,
                                                 date=self.best_ranking.date)
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(event_ranking=self.best_ranking,
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                position=2)
        pgr2 = PlayerGameResult(event_ranking=per2,
                                round_number=pgr1.round_number,
                                game_number=pgr1.game_number,
                                player=p2,
                                power=self.russia,
                                position=4)
        self.assertIs(False, pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_round(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        per2 = PlayerEventRanking.objects.create(player=p2,
                                                 event_name=self.best_ranking.event_name,
                                                 date=self.best_ranking.date)
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(event_ranking=self.best_ranking,
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                position=2)
        pgr2 = PlayerGameResult(event_ranking=per2,
                                round_number=2,
                                game_number=1,
                                player=p2,
                                power=self.russia,
                                position=4)
        self.assertIs(False, pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_game(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        per2 = PlayerEventRanking.objects.create(player=p2,
                                                 event_name=self.best_ranking.event_name,
                                                 date=self.best_ranking.date)
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(event_ranking=self.best_ranking,
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                position=2)
        pgr2 = PlayerGameResult(event_ranking=per2,
                                round_number=1,
                                game_number=2,
                                player=p2,
                                power=self.russia,
                                position=4)
        self.assertIs(False, pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_date(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        per2 = PlayerEventRanking.objects.create(player=p2,
                                                 event_name=self.best_ranking.event_name,
                                                 date=self.worst_ranking.date)
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(event_ranking=self.best_ranking,
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                position=2)
        pgr2 = PlayerGameResult(event_ranking=per2,
                                round_number=pgr1.round_number,
                                game_number=pgr1.game_number,
                                player=p2,
                                power=self.russia,
                                position=4)
        self.assertIs(False, pgr1.for_same_game(pgr2))

    # PlayeGameResult.game_name()
    def test_playergameresult_game_name(self):
        p = Player.objects.first()
        pgr = PlayerGameResult(event_ranking=self.best_ranking,
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               position=2)
        name = pgr.game_name()
        self.assertEqual(name, 'R 1 B 3')

    # PlayerGameResult.wdd_url()
    def test_playergameresult_wdd_url(self):
        p = Player.objects.first()
        pgr = PlayerGameResult(event_ranking=self.best_ranking,
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               position=2)
        # Check wdd_url() for a PGR with no WDD id
        self.assertIsNone(pgr.event_ranking.wdd_tournament_id)
        self.assertEqual('', pgr.wdd_url())

        ranking = PlayerEventRanking.objects.create(player=p,
                                event_name='WDD Linked Tournament',
                                date=date.today(),
                                wdd_tournament_id=369)
        pgr = PlayerGameResult(event_ranking=ranking,
                       round_number=1,
                       game_number=3,
                       player=p,
                       power=self.austria,
                       position=2)
        url = pgr.wdd_url()
        self.assertIn('https://world-diplomacy-database.com/php/results/tournament_board.php', url)
        self.assertIn('id_tournament=369', url)
        self.assertIn('id_round=1', url)
        self.assertIn('id_board=3', url)

    # PlayerGameResult.wdr_url()
    def test_playergameresult_wdr_url(self):
        wdd = WDDPlayer.objects.first()
        p = wdd.player
        pgr = PlayerGameResult(event_ranking=self.best_ranking,
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               position=2)
        # Check wdr_url() for a PGR with no WDR id
        self.assertIsNone(pgr.event_ranking.wdr_tournament_id)
        self.assertEqual('', pgr.wdr_url())

        ranking = PlayerEventRanking.objects.create(player=p,
                                event_name='WDR Linked Tournament',
                                date=date.today(),
                                wdr_tournament_id=369)
        pgr = PlayerGameResult(event_ranking=ranking,
                       round_number=1,
                       game_number=3,
                       player=p,
                       power=self.austria,
                       position=2)
        url = pgr.wdr_url()
        self.assertEqual('https://www.world-diplomacy-reference.com/tournaments/369/boards', url)

    # PlayerGameResult.__str__()
    def test_playergameresult_str(self):
        p = Player.objects.first()
        pgr = PlayerGameResult(event_ranking=self.best_ranking,
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               position=2)
        p_str = str(pgr)
        # We expect to find player name and power name
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(pgr.power.name, p_str)

    def test_playergameresult_top_board_default_false(self):
        p = Player.objects.first()
        pgr = PlayerGameResult.objects.create(event_ranking=self.best_ranking,
                                              round_number=2,
                                              game_number=2,
                                              player=p,
                                              power=self.austria,
                                              position=3)
        self.assertIs(False, pgr.is_top_board)
        # Cleanup
        pgr.delete()
