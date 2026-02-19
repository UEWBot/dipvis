# Diplomacy Tournament Visualiser
# Copyright (C) 2020-2025 Chris Brand
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
Minimalist GameState
"""

from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from tournament.diplomacy.values.diplomacy_values import (FIRST_YEAR,
                                                          TOTAL_SCS,
                                                          WINNING_SCS)
from tournament.game_scoring.game_state import DotCountUnknown, GameState


class InvalidState(Exception):
    """The game state is invalid"""
    pass


class SimpleGameState(GameState):
    """
    Minimal description of a single game, for scoring purposes.
    """

    def __init__(self, sc_counts, final_year, elimination_years, draw=None):
        """
        Create a SimpleGameState from minimal info about a Game

        sc_counts should be a dict, keyed by power, of ints
        final_year should be the year of the last fall turn that was adjudicated
        elimination_years should be a dict, keyed by power, of ints
        draw should be a set, list, or tuple of powers, or None
        If the game was conceded, len(draw) should be one
        """
        self.sc_counts = sc_counts
        self.final_year = final_year
        self.elimination_years = elimination_years
        self.draw = draw
        # Sanity-check the parameters
        total = sum(sc_counts.values())
        if total > TOTAL_SCS:
            raise InvalidState(_('Total supply centre count is %(total)d\n') % {'total': total})
        for p, y in elimination_years.items():
            if y < FIRST_YEAR:
                raise InvalidState(_('%(power)s cannot be eliminated in %(year)d') % {'power': str(p),
                                                                                      'year': y})
            if y > final_year:
                raise InvalidState(_('%(power)s cannot be eliminated in %(year)d if the game ended in %(end)d') % {'power': str(p),
                                                                                                                   'year': y,
                                                                                                                   'end': final_year})
            if sc_counts[p]:
                raise InvalidState(ngettext('%(power)s cannot be eliminated in %(year)d and now have one centre',
                                            '%(power)s cannot be eliminated in %(year)d and now have %(dots)d centres',
                                            sc_counts[p])
                                   % {'power': str(p),
                                      'year': y,
                                      'dots': sc_counts[p]})

    def all_powers(self):
        """Returns an iterable of all the powers."""
        return self.sc_counts.keys()

    def soloer(self):
        """Returns the power that soloed the game or was conceded to, or None."""
        for p, c in self.sc_counts.items():
            if c >= WINNING_SCS:
                return p
        if self.draw is not None and len(self.draw) == 1:
            return self.draw[0]
        return None

    def survivors(self):
        """Returns an iterable of the subset of powers that are still alive."""
        return [p for p, c in self.sc_counts.items() if c > 0]

    def powers_in_draw(self):
        """
        Returns an iterable of all the powers that are included in a draw.

        For a concession, return an iterable containing just the power conceded to.
        If there is no passed draw vote or concession, returns survivors().
        """
        return self.draw or self.survivors()

    def solo_year(self):
        """Returns the year in which a solo occurred, or None."""
        for c in self.sc_counts.values():
            if c >= WINNING_SCS:
                return self.final_year
        return None

    def num_powers_with(self, centres):
        """
        Returns the number of powers that own the specified number of supply centres.
        """
        return len([c for c in self.sc_counts.values() if c == centres])

    def highest_dot_count(self):
        """Returns the number of supply centres owned by the strongest power(s)."""
        return max(self.sc_counts.values())

    def dot_count(self, power, year=None):
        """Returns the number of supply centres owned by the specified power."""
        if (year is not None) and (year != self.final_year):
            raise DotCountUnknown(f'{power} in {year}')
        return self.sc_counts[power]

    def year_eliminated(self, power):
        """Returns the year in which the specified power was eliminated, or None."""
        return self.elimination_years[power]

    def elimination_year_list(self):
        """
        Returns a list with the elimination year for each power in all_powers() order.

        Entry is None is the power is still alive.
        """
        retval = []
        for p, c in self.sc_counts.items():
            if c:
                retval.append(None)
            else:
                retval.append(self.elimination_years[p])
        return retval

    def last_full_year(self):
        """Returns the last year for which we have SC ownerships."""
        return self.final_year
