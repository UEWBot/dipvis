# Diplomacy Tournament Visualiser
# Copyright (C) 2025 Chris Brand
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

from django.core.validators import MaxValueValidator

from ..models.great_power import GreatPower
from ..values.diplomacy_values import TOTAL_GREAT_POWERS


# Referenced by old migrations
def num_greatpowers():
    return GreatPower.objects.count()


"""
Checks that value doesn't exceed the number of GreatPowers
"""
# A constant, because Django's system checks evaluate a callable limit, before any tables exist
validate_max_greatpowers = MaxValueValidator(TOTAL_GREAT_POWERS)
