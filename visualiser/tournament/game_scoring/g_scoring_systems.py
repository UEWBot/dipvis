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

from tournament.game_scoring.bangkok import GScoringBangkok
from tournament.game_scoring.base3 import GScoringBase3
from tournament.game_scoring.carnage import GScoringCarnage
from tournament.game_scoring.cdiplo import GScoringCDiplo
from tournament.game_scoring.cdiplo_namur import GScoringCDiploNamur
from tournament.game_scoring.detour09 import GScoringDetour09
from tournament.game_scoring.draw_size import GScoringDrawSize
from tournament.game_scoring.haight import GScoringHaight
from tournament.game_scoring.manorcon import GScoringManorCon
from tournament.game_scoring.maxonian import GScoringMaxonian
from tournament.game_scoring.open_mind_the_gap import GScoringOMG
from tournament.game_scoring.open_tribute import GScoringOpenTribute
from tournament.game_scoring.ranked_classic import GScoringRankedClassic
from tournament.game_scoring.solos import GScoringSolos
from tournament.game_scoring.southern_sun import GScoringSouthernSun
from tournament.game_scoring.sum_of_squares import GScoringSumOfSquares
from tournament.game_scoring.tribute import GScoringTribute
from tournament.game_scoring.whipping import GScoringWhipping
from tournament.game_scoring.world_classic import GScoringWorldClassic


# All the game scoring systems we support
G_SCORING_SYSTEMS = [
    GScoringBangkok(),
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
    GScoringCDiplo(_('CDiplo 80'), 80.0, 0.0, 25.0, 14.0, 7.0),
    GScoringCDiploNamur(),
    GScoringDetour09(),
    GScoringDrawSize(),
    GScoringHaight(),
    GScoringManorCon(_('ManorCon'), 75, True),
    GScoringManorCon(_('Original ManorCon'), 100, True),
    GScoringManorCon(_('ManorCon v2'), 100, False),
    GScoringMaxonian(_('Maxonian'), 13),
    GScoringMaxonian(_('7Eleven'), 11),
    GScoringOMG(),
    GScoringRankedClassic(),
    GScoringSolos(),
    GScoringSumOfSquares(),
    GScoringSouthernSun(),
    GScoringTribute(),
    GScoringOpenTribute(),
    GScoringWhipping(_('Whipping'), 468),
    GScoringWorldClassic('World Classic'),
    GScoringWorldClassic('Summer Classic', no_3ways=True),
]
