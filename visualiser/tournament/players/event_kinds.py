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
    def event_words(cls, event_kind):
        """
        Return a 3-tuple of (an_event, event, events) for the given event kind.

        Returns translations for ('an event', 'event', 'events') when event_kind
        is None or unrecognized.
        """
        if event_kind == cls.TOURNAMENT:
            return (_('a tournament'), _('tournament'), _('tournaments'))
        if event_kind == cls.LEAGUE:
            return (_('a league'), _('league'), _('leagues'))
        if event_kind == cls.CIRCUIT:
            return (_('a circuit'), _('circuit'), _('circuits'))
        return (_('an event'), _('event'), _('events'))
