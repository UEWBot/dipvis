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


def validate_preference_string(the_string):
    """
    Checks that the string represents a valid power preference list.
    It must only contain the single-letter abbreviations for the great powers
    (upper or lower case), with each present at most once.
    """
    # Convert the preference string to all uppercase
    the_string = the_string.upper()
    # Check for duplicated powers in the string
    if len(the_string) != len(set(the_string)):
        raise ValidationError(_('%(prefs)s contains duplicate characters'),
                              params={'prefs': the_string})
    # Check for invalid powers in the string
    all_powers = set()
    for p in GreatPower.objects.all():
        all_powers.add(p.abbreviation)
    invalid = set(the_string) - all_powers
    if invalid:
        raise ValidationError(_('%(prefs)s contains invalid character(s)'),
                              params={'prefs': the_string})
