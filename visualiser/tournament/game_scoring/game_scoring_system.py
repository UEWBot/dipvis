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
This module contains the GameScoringSystem abstract base class
"""
from abc import ABC, abstractmethod

from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _


class GameScoringSystem(ABC):
    # TODO This doesn't deal with multiple players playing one power
    """
    A scoring system for a Game.

    Provides a method to calculate a score for each player of one game.
    """
    MAX_NAME_LENGTH = 40
    name = u''
    """
    False if a power's score is fixed at elimination,
    True if their score may still change.
    """
    dead_score_can_change = False

    @abstractmethod
    def scores(self, state):
        """
        Takes a GameState object.

        Returns a dict, indexed by power id, of scores.
        """
        raise NotImplementedError

    @property
    def slug(self):
        """Slug for the system"""
        # In theory, two systems could have matching slugs, but the usage means that should never happen
        return slugify(self.name)

    @property
    def description(self):
        """Returns a string describing the scoring system"""
        # By default, use the docstring for the class
        return _(self.__doc__)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('game_scoring_detail', args=(self.slug,))
