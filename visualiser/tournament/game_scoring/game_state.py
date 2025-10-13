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
This module contains the GameState abstract base class and associated exceptions
"""
from abc import ABC, abstractmethod


class InvalidYear(Exception):
    """The specified year is invalid for the GameState."""
    pass


class DotCountUnknown(Exception):
    """The dot count for the specified year is unknown."""
    pass


class GameState(ABC):
    """
    The state of a Game to be scored.

    Encapsulates all the information needed to calculate a score for each power.
    """

    @abstractmethod
    def all_powers(self):
        """Returns an iterable of all the powers."""
        raise NotImplementedError

    @abstractmethod
    def soloer(self):
        """Returns the power that soloed the game or was conceded to, or None."""
        raise NotImplementedError

    @abstractmethod
    def survivors(self):
        """
        Returns an iterable of the subset of powers that are still alive.
        """
        raise NotImplementedError

    @abstractmethod
    def powers_in_draw(self):
        """
        Returns an iterable of all the powers that are included in a draw.

        For a concession, return an iterable containing just the power conceded to.
        If there is no passed draw vote or concession, returns survivors().
        """
        raise NotImplementedError

    @abstractmethod
    def solo_year(self):
        """Returns the year in which a solo occurred, or None."""
        raise NotImplementedError

    @abstractmethod
    def num_powers_with(self, centres):
        """returns the number of powers that own the specified number of supply centres."""
        raise NotImplementedError

    @abstractmethod
    def highest_dot_count(self):
        """Returns the number of supply centres owned by the strongest power(s)."""
        raise NotImplementedError

    @abstractmethod
    def dot_count(self, power, year=None):
        """
        Returns the number of supply centres owned by the specified power.

        If year is specified, returns the numer of centres owned at the end
        of that year. Otherwise, returns the latest number.
        May raise InvaidYear or DotCountUnknown if year is provided.
        """
        raise NotImplementedError

    @abstractmethod
    def year_eliminated(self, power):
        """Returns the year in which the specified power was eliminated, or None."""
        raise NotImplementedError

    @abstractmethod
    def last_full_year(self):
        """
        Returns the year that the SC counts are for.

        As SC ownerships change after Fall retreats, this will be the previous year
        if currently playing spring or fall, and the current year if currently doing
        adjustments.
        """
        raise NotImplementedError
