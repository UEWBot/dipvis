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

from . import PlayerTitle


class PlayerTitleTests(TestCase):
    """Test the PlayerTitle class"""
    fixtures = ['players.json']

    # PlayerTitle.__str__()
    def test_playertitle_str(self):
        pt = PlayerTitle(player=Player.objects.first(),
                         title='Dogwasher of the Year',
                         year=1900)
        p_str = str(pt)
        # We expect to find player name, title, and year
        self.assertIn(pt.player.first_name, p_str)
        self.assertIn(pt.player.last_name, p_str)
        self.assertIn(pt.title, p_str)
        self.assertIn(str(pt.year), p_str)
