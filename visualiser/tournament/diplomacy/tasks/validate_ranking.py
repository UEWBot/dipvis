# Diplomacy Tournament Visualiser
# Copyright (C) 2020 Chris Brand
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

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from ..models.great_power import GreatPower

def validate_ranking(value):
    """
    Checks for a valid power rank - 1..7
    """
    if value < 1:
        raise ValidationError(_('%(value)d is not a valid ranking'),
                              params={'value': value})
    if value > GreatPower.objects.count():
        raise ValidationError(_('%(value)d is not a valid ranking'),
                              params={'value': value})