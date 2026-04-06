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

from . import PlayerAward


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

    # PlayerAward.wdd_url()
    def test_playeraward_wdd_url_power(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         tournament='Some tournament',
                         date=datetime.now(datetime_timezone.utc),
                         name='Nicest Player of France',
                         wdd_tournament_id=369,
                         power=self.france)
        url = pa.wdd_url()
        # TODO verify result
        # Also check wdr_url() for a PA with no WDR id
        self.assertEqual('', pa.wdr_url())

    def test_playeraward_wdd_url_no_power(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         tournament='Some tournament',
                         date=datetime.now(datetime_timezone.utc),
                         name='Nicest Person',
                         wdd_tournament_id=369)
        url = pa.wdd_url()
        # TODO verify result

    # PlayerAward.wdr_url()
    def test_playeraward_wdr_url(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         tournament='Some tournament',
                         date=datetime.now(datetime_timezone.utc),
                         name='Nicest Person',
                         wdr_tournament_id=369)
        url = pa.wdr_url()
        # TODO verify result
        # Also check wdd_url() for a PA with no WDD id
        self.assertEqual('', pa.wdd_url())

    # PlayerAward.__str__()
    def test_playeraward_str(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         tournament='Some tournament',
                         date=datetime.now(datetime_timezone.utc),
                         name='Nicest Person')
        p_str = str(pa)
        # We expect to find player name, award name, and tournament name
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(pa.name, p_str)
        self.assertIn(pa.tournament, p_str)
