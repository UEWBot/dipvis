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

from django.test import TestCase

from tournament.diplomacy import GreatPower
from tournament.players import Player

from . import PlayerTournamentRanking


class PlayerTournamentRankingTests(TestCase):
    """Test the PlayerTournamentRanking class"""
    fixtures = ['players.json']

    # PlayerTournamentRanking.wdd_url()
    def test_playertournamentranking_wdd_url(self):
        p = Player.objects.first()
        ptr = PlayerTournamentRanking(player=p,
                                      tournament='Some tournament',
                                      position=3,
                                      year=1974,
                                      wdd_tournament_id=369)
        url = ptr.wdd_url()
        # TODO verify result
        # Also check wdr_url() for a PTR with no WDR id
        self.assertEqual('', ptr.wdr_url())

    # PlayerTournamentRanking.wdr_url()
    def test_playertournamentranking_wdr_url(self):
        p = Player.objects.first()
        ptr = PlayerTournamentRanking(player=p,
                                      tournament='Some tournament',
                                      position=3,
                                      year=1974,
                                      wdr_tournament_id=369)
        url = ptr.wdr_url()
        # TODO verify result
        # Also check wdd_url() for a PTR with no WDD id
        self.assertEqual('', ptr.wdd_url())

    # PlayerTournamentRanking.__str__()
    def test_playertournamentranking_str(self):
        p = Player.objects.first()
        ptr = PlayerTournamentRanking(player=p,
                                      tournament='Some tournament',
                                      position=3,
                                      year=1974)
        p_str = str(ptr)
        # We expect to find player name, tournament name, and year
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(ptr.tournament, p_str)
        self.assertIn(str(ptr.year), p_str)

    def test_playertournamentranking_str_with_year(self):
        p = Player.objects.first()
        ptr = PlayerTournamentRanking(player=p,
                                      tournament='Some tournament 1974',
                                      position=3,
                                      year=1974)
        p_str = str(ptr)
        # We expect to find player name, tournament name, and year
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(ptr.tournament, p_str)
        self.assertIn(str(ptr.year), p_str)
