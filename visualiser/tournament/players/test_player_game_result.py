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

from . import PlayerGameResult


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

    # PlayerGameResult.for_same_game()
    def test_playergameresult_same(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(tournament_name='Best Tournament',
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                date=date.today(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name=pgr1.tournament_name,
                                round_number=pgr1.round_number,
                                game_number=pgr1.game_number,
                                player=p2,
                                power=self.russia,
                                date=pgr1.date,
                                position=4)
        self.assertIs(True, pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_tournament(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(tournament_name='Best Tournament',
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                date=date.today(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name='Worst Tournament',
                                round_number=pgr1.round_number,
                                game_number=pgr1.game_number,
                                player=p2,
                                power=self.russia,
                                date=pgr1.date,
                                position=4)
        self.assertIs(False, pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_round(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(tournament_name='Best Tournament',
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                date=date.today(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name=pgr1.tournament_name,
                                round_number=2,
                                game_number=1,
                                player=p2,
                                power=self.russia,
                                date=pgr1.date,
                                position=4)
        self.assertIs(False, pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_game(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(tournament_name='Best Tournament',
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                date=date.today(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name=pgr1.tournament_name,
                                round_number=1,
                                game_number=2,
                                player=p2,
                                power=self.russia,
                                date=pgr1.date,
                                position=4)
        self.assertIs(False, pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_date(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(tournament_name='Best Tournament',
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                date=date.today(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name=pgr1.tournament_name,
                                round_number=pgr1.round_number,
                                game_number=pgr1.game_number,
                                player=p2,
                                power=self.russia,
                                date=date.today() + timedelta(hours=24),
                                position=4)
        self.assertIs(False, pgr1.for_same_game(pgr2))

    # PlayeGameResult.game_name()
    def test_playergameresult_game_name(self):
        p = Player.objects.first()
        pgr = PlayerGameResult(tournament_name='Best Tournament',
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               date=date.today(),
                               position=2)
        name = pgr.game_name()
        self.assertEqual(name, 'R 1 B 3')

    # PlayerGameResult.wdd_url()
    def test_playergameresult_wdd_url(self):
        p = Player.objects.first()
        pgr = PlayerGameResult(tournament_name='Best Tournament',
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               date=date.today(),
                               position=2,
                               wdd_tournament_id=369)
        url = pgr.wdd_url()
        # TODO verify result
        # Check wdr_url() for a PGR with no WDR id
        self.assertIsNone(pgr.wdr_tournament_id)
        url = pgr.wdr_url()

    # PlayerGameResult.wdr_url()
    def test_playergameresult_wdr_url(self):
        wdd = WDDPlayer.objects.first()
        p = wdd.player
        pgr = PlayerGameResult(tournament_name='Best Tournament',
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               date=date.today(),
                               position=2,
                               wdr_tournament_id=369)
        url = pgr.wdr_url()
        # TODO verify result
        # Check wdr_url() for a PGR with no WDR id
        self.assertIsNotNone(pgr.wdr_tournament_id)
        url = pgr.wdr_url()

    # PlayerGameResult.__str__()
    def test_playergameresult_str(self):
        p = Player.objects.first()
        pgr = PlayerGameResult(tournament_name='Best Tournament',
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               date=date.today(),
                               position=2)
        p_str = str(pgr)
        # We expect to find player name and power name
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(pgr.power.name, p_str)
