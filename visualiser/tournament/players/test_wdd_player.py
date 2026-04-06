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

from django.test import TestCase, tag

from tournament.diplomacy import GreatPower
from tournament.players import (PlayerAward, PlayerGameResult, PlayerRanking,
                                PlayerTitle, PlayerTournamentRanking)

from . import WDDPlayer


MELINDA_HOLLEY_WDD_ID = 5185


class WDDPlayerTests(TestCase):
    """Test the WDDPlayer class"""
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

    # TODO WDDPlayer._clear_background()

    # WDDPlayer.wdd_url()
    def test_wddplayer_wdd_url(self):
        wdd = WDDPlayer.objects.first()
        url = wdd.wdd_url()
        # TODO verify result

    # WDDPlayer.wdd_firstname_lastname()
    @tag('wdd')
    def test_wddplayer_wdd_name1(self):
        wdd = WDDPlayer.objects.first()
        name = wdd.wdd_firstname_lastname()
        # TODO verify result

    @tag('wdd')
    def test_wddplayer_wdd_name2(self):
        """Fast path if already cached"""
        wdd = WDDPlayer.objects.first()
        wdd._wdd_firstname = 'Arthur'
        name = wdd.wdd_firstname_lastname()
        self.assertEqual(name[0], 'Arthur')

    # WDDPlayer.delete()
    def test_wddplayer_delete(self):
        wdd = WDDPlayer.objects.first()
        p = wdd.player
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        wdd_id = wdd.wdd_player_id
        # Create one of each type of background record
        PlayerTournamentRanking.objects.create(player=p,
                                               tournament='Some tournament',
                                               position=3,
                                               year=1974)
        PlayerTitle.objects.create(player=p,
                                   title='Canadian Beaver',
                                   year=1976)
        PlayerGameResult.objects.create(player=p,
                                        tournament_name='Some tournament',
                                        round_number=4,
                                        game_number=17,
                                        power=self.austria,
                                        date=datetime.now(datetime_timezone.utc),
                                        position=2)
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=datetime.now(datetime_timezone.utc),
                                   name='Nicest Person')
        PlayerRanking.objects.create(player=p,
                                     system='Who Chris Likes Most',
                                     international_rank='8',
                                     national_rank='3')
        wdd.delete()
        # Deletion should trigger clearing of background
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        # Clean up
        WDDPlayer.objects.create(wdd_player_id=wdd_id,
                                 player=p)

    # Change of WDDPlayer.wdd_player_id
    # This mostly tests WDDPlayerIdField.pre_save()
    def test_wddplayer_save(self):
        wdd = WDDPlayer.objects.first()
        p = wdd.player
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        wdd_id = wdd.wdd_player_id
        # Create one of each type of background record
        PlayerTournamentRanking.objects.create(player=p,
                                               tournament='Some tournament',
                                               position=3,
                                               year=1974)
        PlayerTitle.objects.create(player=p,
                                   title='Canadian Beaver',
                                   year=1976)
        PlayerGameResult.objects.create(player=p,
                                        tournament_name='Some tournament',
                                        round_number=4,
                                        game_number=17,
                                        power=self.austria,
                                        date=datetime.now(datetime_timezone.utc),
                                        position=2)
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=datetime.now(datetime_timezone.utc),
                                   name='Nicest Person')
        PlayerRanking.objects.create(player=p,
                                     system='Who Chris Likes Most',
                                     international_rank='8',
                                     national_rank='3')
        wdd.wdd_player_id = MELINDA_HOLLEY_WDD_ID
        wdd.save(update_fields=['wdd_player_id'])
        # Change in wdd_player_id should trigger clearing of background
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        # Clean up
        wdd.wdd_player_id = wdd_id
        wdd.save(update_fields=['wdd_player_id'])

    # WDDPlayer.__str__()
    def test_wddplayer_str(self):
        wdd = WDDPlayer.objects.first()
        string = str(wdd)
        # TODO Verify result
