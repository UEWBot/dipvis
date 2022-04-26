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

# This file contains the basics of the standard game of Diplomacy.
# Which powers exist, how many Supply Centres there are, which colour
# represents each power, etc.

"""
This module provides classes describing the core Diplomacy board game.

If we ever want to support variants, then these are the definitions
that will need to differ for different variants.
"""

import os

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _







