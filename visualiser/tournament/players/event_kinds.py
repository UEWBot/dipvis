# Diplomacy Tournament Visualiser
# Copyright (C) 2026 Chris Brand
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
This module provides classes to categorise Diplomacy tournament events.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class EventKinds(models.TextChoices):
    """
    Kind of Diplomacy event.
    """
    TOURNAMENT = 'T', _('Tournament')
    LEAGUE = 'L', _('League')
    CIRCUIT = 'C', _('Circuit')
    OTHER = 'O', _('Other')

    @classmethod
    def event_word(cls, event_kind):
        """
        Deduce the descriptive noun for a given event kind.

        Returns 'event' when event_kind is None (all events) or unrecognized.
        """
        if event_kind == cls.TOURNAMENT:
            return 'tournament'
        if event_kind == cls.LEAGUE:
            return 'league'
        if event_kind == cls.CIRCUIT:
            return 'circuit'
        return 'event'
