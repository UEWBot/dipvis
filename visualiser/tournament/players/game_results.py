# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016 Chris Brand
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

# This file contains code related to Diplomacy players themselves.
# This is predominantly the Player class, but also the various classes
# used to cache background information about players' Diplomacy
# tournament history.

"""
This module provides classes to describe Diplomacy players.

Most of the code is dedicated to storing background information
about a player and retrieving it as needed.
"""

from django.db import models
from django.utils.translation import gettext as _


class GameResults(models.TextChoices):
    """How a game ended, from one player's perspective"""
    # These encodings happen to co-incide with the coding used by the WDD
    WIN = 'W', _('Win')
    DRAW_2 = 'D2', _('2-way draw')
    DRAW_3 = 'D3', _('3-way draw')
    DRAW_4 = 'D4', _('4-way draw')
    DRAW_5 = 'D5', _('5-way draw')
    DRAW_6 = 'D6', _('6-way draw')
    DRAW_7 = 'D7', _('7-way draw')
    LOSS = 'L', _('Loss')
