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

"""
This module contains the interface between the game scoring code and the tournament database.
"""

from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR, WINNING_SCS
from tournament.diplomacy.models.great_power import GreatPower
from tournament.game_scoring.game_state import GameState
from tournament.game_scoring.game_state import InvalidYear, DotCountUnknown


class TournamentGameState(GameState):
    """
    Abstraction of a single Game in a Tournament, for scoring purposes.
    """

    # TODO This version makes more sense, but the tests are currently written
    #      to score games at various points rather than always at the end
    #def __init__(self, game):
    #    """Create the object corresponding to the specific Game."""
    #    self.game = game
    #    self.scs = game.supplycentre_set.all()
    #    self.draw = game.passed_draw()
    #    self.final_year = self.scs.order_by('-year')[0].year
    #    self.final_year_scs = return self.scs.filter(year=self.final_year).order_by('-count')

    def __init__(self, scs):
        """Create the object corresponding to the specific Game."""
        self.scs = scs
        self.game = scs.first().game
        self.draw = self.game.passed_draw()
        self.final_year = self.scs.order_by('-year')[0].year
        self.final_year_scs = self.scs.filter(year=self.final_year).order_by('-count')

    def _validate_year(self, year):
        """Check that the year is reasonable. Raise InvalidYear if it isn't."""
        # 1900 gives the starting SC count
        if (year < FIRST_YEAR - 1) or (year > self.final_year):
            raise InvalidYear(year)

    def all_powers(self):
        """Returns an iterable of all the powers."""
        return GreatPower.objects.all()

    def soloer(self):
        """Returns the power that soloed the game or was conceded to, or None."""
        if self.final_year_scs[0].count >= WINNING_SCS:
            return self.final_year_scs[0].power
        if self.draw is not None:
            draw_powers = self.draw.powers()
            if len(draw_powers) == 1:
                return draw_powers[0]
        return None

    def survivors(self):
        """
        Returns an iterable of the subset of powers that are still alive.
        """
        return [sc.power for sc in self.final_year_scs.filter(count__gt=0)]

    def powers_in_draw(self):
        """
        Returns an iterable of all the powers that are included in a draw.

        For a concession, return an iterable containing just the power conceded to.
        If there is no passed draw vote or concession, returns survivors().
        """
        if self.draw is not None:
            return self.draw.powers()
        return self.survivors()

    def solo_year(self):
        """Returns the year in which a solo occurred, or None."""
        top = self.final_year_scs[0]
        if top.count >= WINNING_SCS:
            return top.year
        if self.draw is not None:
            if len(self.draw.powers()) == 1:
                return self.draw.year
        return None

    def num_powers_with(self, centres):
        """
        Returns the number of powers that own the specified number of supply centres.
        """
        return self.final_year_scs.filter(count=centres).count()

    def highest_dot_count(self):
        """Returns the number of supply centres owned by the strongest power(s)."""
        return self.final_year_scs[0].count

    def dot_count(self, power, year=None):
        """Returns the number of supply centres owned by the specified power."""
        if year is not None:
            self._validate_year(year)
            try:
                return self.scs.filter(year=year).get(power=power).count
            # We can't import CentreCount here
            except BaseException as e:
                raise DotCountUnknown from e
        return self.final_year_scs.get(power=power).count

    def year_eliminated(self, power):
        """Returns the year in which the specified power was eliminated, or None."""
        try:
            return self.scs.filter(power=power).filter(count=0).order_by('year').first().year
        except AttributeError:
            return None

    def last_full_year(self):
        """Returns the last year for which SCs have been entered."""
        return self.final_year
