# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2020 Chris Brand
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

"""
This module contains the G_SCORING_SYSTEMS array.
"""
from django.utils.translation import gettext as _

from .bangkok import GScoringBangkok
from .bangkok_pike import GScoringBangkokPike
from .base3 import GScoringBase3
from .carnage import GScoringCarnage
from .cdiplo import GScoringCDiplo
from .cdiplo_namur import GScoringCDiploNamur
from .detour09 import GScoringDetour09
from .draw_size import GScoringDrawSize
from .haight import GScoringHaight
from .manorcon import GScoringManorCon
from .maxonian import GScoringMaxonian
from .open_mind_the_gap import GScoringOMG
from .open_tribute import GScoringOpenTribute
from .ranked_classic import GScoringRankedClassic
from .solos import GScoringSolos
from .southern_sun import GScoringSouthernSun
from .sum_of_squares import GScoringSumOfSquares
from .tribute import GScoringTribute
from .vulcan import GScoringVulcan
from .whipping import GScoringWhipping
from .world_classic import GScoringWorldClassic
from .your_draw_size import GScoringYourDrawSize


# All the game scoring systems we support
G_SCORING_SYSTEMS = [
    GScoringBangkok(_('Bangkok'), 41, 0.5, 3, 2,   1),
    GScoringBangkok(_('Olympic'), 46, 0,   4, 1.5, 0.5),
    GScoringBangkokPike(),
    GScoringBase3(),
    GScoringCarnage(_('Carnage with dead equal'),
                    centre_based=False,
                    dead_equal=True,
                    pts_per_dot_lead=0),
    GScoringCarnage(_('Carnage with elimination order'),
                    centre_based=False,
                    dead_equal=False,
                    pts_per_dot_lead=0),
    GScoringCarnage(_('Center-count Carnage'),
                    centre_based=True,
                    dead_equal=False,
                    pts_per_dot_lead=0),
    GScoringCarnage(_('Carnage 2023'),
                    centre_based=False,
                    dead_equal=False,
                    pts_per_dot_lead=300),
    GScoringCDiplo(_('CDiplo 100'), 100.0, 1.0, 38.0, 14.0, 7.0),
    GScoringCDiplo(_('CDiplo 80'),   80.0, 0.0, 25.0, 14.0, 7.0),
    GScoringCDiploNamur(),
    GScoringDetour09(),
    GScoringDrawSize(),
    GScoringHaight(),
    GScoringManorCon(_('ManorCon'),           75, True),
    GScoringManorCon(_('Original ManorCon'), 100, True),
    GScoringManorCon(_('ManorCon v2'),       100, False),
    GScoringMaxonian(_('Maxonian'), 13),
    GScoringMaxonian(_('7Eleven'),  11),
    GScoringOMG(),
    GScoringRankedClassic(),
    GScoringSolos(),
    GScoringSumOfSquares(),
    GScoringSouthernSun(),
    GScoringTribute(),
    GScoringOpenTribute(),
    GScoringVulcan(),
    GScoringWhipping(_('Whipping'), 468),
    GScoringWorldClassic('World Classic'),
    GScoringWorldClassic('Summer Classic', no_3ways=True),
    GScoringYourDrawSize('Your Draw Size (short games)',     300),
    GScoringYourDrawSize('Your Draw Size (unlimited games)', 320),
]
