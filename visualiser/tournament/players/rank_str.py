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

from django.utils.translation import gettext as _


def rank_str(rank):
    """Return the ordinal string for a rank, for example '1st' or '12th'."""
    # TODO translation support ?
    result = str(rank)
    rank_mod_100 = rank % 100
    if 3 < rank_mod_100 < 21:
        result += u'th'
    elif rank_mod_100 % 10 == 1:
        result += u'st'
    elif rank_mod_100 % 10 == 2:
        result += u'nd'
    elif rank_mod_100 % 10 == 3:
        result += u'rd'
    else:
        result += u'th'
    return _(result)