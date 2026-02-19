# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2025 Chris Brand
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

from tournament.diplomacy.values.diplomacy_values import (FIRST_YEAR,
                                                          TOTAL_SCS,
                                                          WINNING_SCS)
from tournament.game_scoring.game_state import DotCountUnknown, GameState


class InvalidState(Exception):
    """The game state is invalid"""
    pass


class SCChartGameState(GameState):
    """
    State of a single Game
    """

    def __init__(self, powers, sc_counts):
        """
        Create a SCChartGameState from a supply centre chart.

        powers should be an iterable representing the Great Powers.
        sc_counts should be a dict, keyed by year, of dicts, keyed by power, of ints.
        """
        # Note that we use a reference to the parameters
        self.powers = powers
        self.sc_counts = sc_counts
        self.final_year = FIRST_YEAR
        # Minimal sanity-check of the parameter
        for year, counts in sc_counts.items():
            if year > self.final_year:
                self.final_year = year
            total = sum(counts.values())
            if total > TOTAL_SCS:
                raise InvalidState(f'(Total SC count in {year} is {total}')

    def all_powers(self):
        return self.powers

    def soloer(self):
        for year, counts in self.sc_counts.items():
            for power, count in counts.items():
                if count >= WINNING_SCS:
                    return power
        return None

    def survivors(self):
        counts = self.sc_counts[self.final_year]
        return [p for p, c in counts.items() if c > 0]

    def powers_in_draw(self):
        return self.survivors()

    def solo_year(self):
        counts = self.sc_counts[self.final_year]
        for power, count in counts.items():
            if count >= WINNING_SCS:
                return self.final_year
        return None

    def num_powers_with(self, centres):
        counts = self.sc_counts[self.final_year]
        return len([c for c in counts.values() if c == centres])

    def highest_dot_count(self):
        counts = self.sc_counts[self.final_year]
        return max(counts.values())

    def dot_count(self, power, year=None):
        if year is None:
            year = self.final_year
        try:
            counts = self.sc_counts[year]
        except KeyError:
            raise DotCountUnknown(f'{power} for year {year}')
        return counts[power]

    def year_eliminated(self, power):
        for year in sorted(self.sc_counts.keys()):
            if self.sc_counts[year][power] == 0:
                return year
        return None

    def elimination_year_list(self):
        retval = []
        counts = self.sc_counts[self.final_year]
        for p in self.powers:
            if counts[p]:
                retval.append[None]
            else:
                retval.append(self.year_eliminated(p))
        return retval

    def last_full_year(self):
        return self.final_year
