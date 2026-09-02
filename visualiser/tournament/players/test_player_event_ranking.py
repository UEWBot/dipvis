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

from datetime import datetime
from datetime import timezone as datetime_timezone

from django.test import TestCase

from tournament.diplomacy import GreatPower
from tournament.players import Player, WDDPlayer

from . import PlayerEventRanking


class PlayerEventRankingTests(TestCase):
    """Test the PlayerEventRanking class"""
    fixtures = ['players.json']

    # PlayerEventRanking.wdd_url()
    def test_playereventranking_wdd_url(self):
        p = Player.objects.first()
        ptr = PlayerEventRanking(player=p,
                                 event_name='Some tournament',
                                 rank=3,
                                 date=datetime.now(datetime_timezone.utc),
                                 wdd_tournament_id=369)
        url = ptr.wdd_url()
        # Player.objects.first() has no WDDPlayer, so no URL can be formed
        self.assertEqual('', url)
        # Also check wdr_url() for a PTR with no WDR id
        self.assertEqual('', ptr.wdr_url())

    def test_playereventranking_wdd_url_with_wdd_player(self):
        p = Player.objects.create(first_name='PTR',
                                  last_name='WDDURL')
        wdd = WDDPlayer.objects.create(player=p,
                                       wdd_player_id=990001)
        ptr = PlayerEventRanking(player=p,
                                 event_name='Some tournament',
                                 rank=3,
                                 date=datetime.now(datetime_timezone.utc),
                                 wdd_tournament_id=369)
        url = ptr.wdd_url()
        self.assertIn('https://', url)
        self.assertIn('tournament_player.php', url)
        self.assertIn('id_tournament=369', url)
        self.assertIn('id_player=990001', url)
        # Cleanup
        wdd.delete()
        p.delete()

    # PlayerEventRanking.wdr_url()
    def test_playereventranking_wdr_url(self):
        p = Player.objects.first()
        ptr = PlayerEventRanking(player=p,
                                 event_name='Some tournament',
                                 rank=3,
                                 date=datetime.now(datetime_timezone.utc),
                                 wdr_tournament_id=369)
        url = ptr.wdr_url()
        self.assertEqual('https://www.world-diplomacy-reference.com/tournaments/369', url)
        # Also check wdd_url() for a PTR with no WDD id
        self.assertEqual('', ptr.wdd_url())

    # PlayerEventRanking.__str__()
    def test_playereventranking_str(self):
        p = Player.objects.first()
        ptr = PlayerEventRanking(player=p,
                                 event_name='Some tournament',
                                 rank=3,
                                 date=datetime.now(datetime_timezone.utc))
        p_str = str(ptr)
        # We expect to find player name, tournament name, and year
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(ptr.event_name, p_str)
        self.assertIn(str(ptr.date.year), p_str)

    def test_playereventranking_str_unranked(self):
        p = Player.objects.first()
        ptr = PlayerEventRanking(player=p,
                                 event_name='Some tournament',
                                 rank=None,
                                 date=datetime.now(datetime_timezone.utc))
        p_str = str(ptr)
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(ptr.event_name, p_str)
        self.assertIn('unranked', p_str)

    def test_playereventranking_str_with_year(self):
        p = Player.objects.first()
        ptr = PlayerEventRanking(player=p,
                                 event_name='Some tournament 1974',
                                 rank=3,
                                 date=datetime.now(datetime_timezone.utc))
        p_str = str(ptr)
        # We expect to find player name, tournament name, and year
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(ptr.event_name, p_str)
        self.assertIn('1974', p_str)
