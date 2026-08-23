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
from tournament.players import Player

from . import PlayerAward, PlayerEventRanking


class PlayerAwardTests(TestCase):
    """Test the PlayerAward class"""
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
        cls.ranking = PlayerEventRanking.objects.create(player=Player.objects.first(),
                                                        event_name='Some tournament',
                                                        date=datetime.now())

    # PlayerAward.wdd_url()
    def test_playeraward_wdd_url_power(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         event_ranking=self.ranking,
                         name='Nicest Player of France',
                         power=self.france)
        # check wdd_url() for a PA with no WDD id
        self.assertIsNone(pa.event_ranking.wdd_tournament_id)
        self.assertEqual('', pa.wdd_url())

        ranking = PlayerEventRanking.objects.create(player=p,
                                                    event_name='WDD Linked Tournament',
                                                    date=datetime.now(),
                                                    wdd_tournament_id=369)
        pa = PlayerAward(player=p,
                         event_ranking=ranking,
                         name='Nicest Player of France',
                         power=self.france)
        url = pa.wdd_url()
        self.assertIn('https://world-diplomacy-database.com/php/results/tournament_best_countries.php', url)
        self.assertIn('id_tournament=369', url)

    def test_playeraward_wdd_url_no_power(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         event_ranking=self.ranking,
                         name='Nicest Person')
        # check wdd_url() for a PA with no WDD id
        self.assertIsNone(pa.event_ranking.wdd_tournament_id)
        self.assertEqual('', pa.wdd_url())

        ranking = PlayerEventRanking.objects.create(player=p,
                                                    event_name='WDD Linked Tournament',
                                                    date=datetime.now(),
                                                    wdd_tournament_id=369)
        pa = PlayerAward(player=p,
                         event_ranking=ranking,
                         name='Nicest Person')
        url = pa.wdd_url()
        self.assertIn('https://world-diplomacy-database.com/php/results/tournament_award.php', url)
        self.assertIn('id_tournament=369', url)

    # PlayerAward.wdr_url()
    def test_playeraward_wdr_url(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         event_ranking=self.ranking,
                         name='Nicest Person')
        # check wdr_url() for a PA with no WDR id
        self.assertIsNone(pa.event_ranking.wdr_tournament_id)
        self.assertEqual('', pa.wdr_url())

        ranking = PlayerEventRanking.objects.create(player=p,
                                                    event_name='WDR Linked Tournament',
                                                    date=datetime.now(),
                                                    wdr_tournament_id=369)
        pa = PlayerAward(player=p,
                         event_ranking=ranking,
                         name='Nicest Person')
        url = pa.wdr_url()
        self.assertEqual('https://www.world-diplomacy-reference.com/tournaments/369', url)

    # PlayerAward.__str__()
    def test_playeraward_str(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         event_ranking=self.ranking,
                         name='Nicest Person')
        p_str = str(pa)
        # We expect to find player name, award name, and event name
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(pa.name, p_str)
        self.assertIn(pa.event_ranking.event_name, p_str)
