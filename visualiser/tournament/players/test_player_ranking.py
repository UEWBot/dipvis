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

from django.test import TestCase, tag

from tournament.diplomacy import GreatPower
from tournament.players import Player, WDDPlayer

from . import PlayerRanking


class PlayerRankingTests(TestCase):
    """Test the PlayerRanking class"""
    fixtures = ['game_sets.json', 'players.json']

    # PlayerRanking.wdd_url()
    def test_playerranking_wdd_url_wpe(self):
        p = Player.objects.first()
        self.assertNotEqual(p.wddplayer_set.count(), 0)
        pr = PlayerRanking(player=p,
                           system='World Performance Evaluation',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdd_url()
        # TODO Validate results

    def test_playerranking_wdd_url_dip_pouch(self):
        p = Player.objects.first()
        self.assertNotEqual(p.wddplayer_set.count(), 0)
        pr = PlayerRanking(player=p,
                           system='Dip Pouch Tournament Rating',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdd_url()
        # TODO Validate results

    def test_playerranking_wdd_url_sdr(self):
        p = Player.objects.first()
        self.assertNotEqual(p.wddplayer_set.count(), 0)
        pr = PlayerRanking(player=p,
                           system='SDR Marathon',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdd_url()
        # TODO Validate results

    def test_playerranking_wdd_url_other(self):
        p = Player.objects.first()
        self.assertNotEqual(p.wddplayer_set.count(), 0)
        pr = PlayerRanking(player=p,
                           system='WPE7',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdd_url()
        # TODO Validate results

    @tag('slow', 'wdd')
    def test_playerranking_wdd_url_no_id(self):
        wdd = WDDPlayer.objects.first()
        p = wdd.player
        wdd_id = wdd.wdd_player_id
        wdd.delete()
        pr = PlayerRanking(player=p,
                           system='World Performance Evaluation',
                           international_rank='8',
                           national_rank='3')
        self.assertEqual('', pr.wdd_url())
        # Cleanup
        WDDPlayer.objects.create(wdd_player_id=wdd_id,
                                 player=p)

    # PlayerRanking.wdr_url()
    def test_playerranking_wdr_url_wpe1(self):
        p = Player.objects.first()
        pr = PlayerRanking(player=p,
                           system='WPE7',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdr_url()
        # TODO Validate results

    def test_playerranking_wdr_url_wpe2(self):
        p = Player.objects.first()
        pr = PlayerRanking(player=p,
                           system='World Performance Evaluation',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdr_url()
        # TODO Validate results

    # PlayerRanking.national_str()
    def test_playerranking_national_str(self):
        p = Player.objects.first()
        pr = PlayerRanking(player=p,
                           system='World Performance Evaluation',
                           international_rank='8',
                           national_rank='3')
        # TODO Validate results
        pr.national_str()

    # PlayerRanking.__str__()
    def test_playerranking_str(self):
        p = Player.objects.first()
        pr = PlayerRanking(player=p,
                           system='World Performance Evaluation',
                           international_rank='8',
                           national_rank='3')
        # TODO Validate results
        str(pr)
