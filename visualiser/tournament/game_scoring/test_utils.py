# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2025 Chris Brand
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

from tournament.diplomacy.models.great_power import GreatPower
from tournament.game_scoring.utils import _adjust_rank_score_lower_special


class UtilsTests(TestCase):
    """
    Test utility functions
    """
    fixtures = ['game_sets.json']

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

    # Some tests of _adjust_rank_score_lower_special
    def test_adjust_rank_score_lower_special_2_way_ties(self):
        POS_PTS = [70, 60, 50, 40, 30, 20, 10]
        POS_PTS_2_TIED = [30, 20, 10]
        dots = [(self.austria, 14),
                (self.england, 8),
                (self.france, 8),
                (self.germany, 2),
                (self.italy, 2),
                (self.russia, 0),
                (self.turkey, 0)]
        # 1st from POS_PTS, then 2 from POS_PTS_2_TIED, rest are beyond the end of POS_PTS_2_TIED
        EXPECT = [70, 20, 20, 0, 0, 0, 0]
        result = _adjust_rank_score_lower_special(dots,
                                                  POS_PTS,
                                                  POS_PTS_2_TIED)
        self.assertEqual(result, EXPECT)

    def test_adjust_rank_score_lower_special_short_rank_pts(self):
        POS_PTS = [70, 60, 50, 40, 30]
        POS_PTS_2_TIED = [30, 20, 10]
        dots = [(self.austria, 14),
                (self.england, 8),
                (self.france, 7),
                (self.germany, 2),
                (self.italy, 1),
                (self.russia, 1),
                (self.turkey, 0)]
        # 1st from POS_PTS, then 2 from POS_PTS_2_TIED, rest are beyond the end of POS_PTS_2_TIED
        EXPECT = [70, 60, 50, 40, 0, 0, 0]
        result = _adjust_rank_score_lower_special(dots,
                                                  POS_PTS,
                                                  POS_PTS_2_TIED)
        self.assertEqual(result, EXPECT)
