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

from ..models.supply_centre import SupplyCentre

def num_supplycentres():
    return SupplyCentre.objects.count()

"""
Checks that value doesn't exceed the number of SupplyCentres
"""
# Workaround migration issue by using intermediate callable
validate_max_supplycentres = MaxValueValidator(num_supplycentres)
