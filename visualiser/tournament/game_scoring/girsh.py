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

from math import floor

from django.utils.translation import gettext as _

from tournament.diplomacy import FIRST_YEAR

from .game_scoring_system import GameScoringSystem
from .utils import _countback_rank_scores, _sorted_scores


class GScoringGIRSH(GameScoringSystem):
    """
    Gap Incentivised Rank SC Hybrid scoring system.

    Players receive rank points of 130, 90, 60, 40, 30, 20, and 10.
    Ties on final supply centre count are resolved by count-back through
    previous game years. Persistent ties split the points for the ranks
    occupied by the tied players.
    In a non-solo game, survivors receive 5 points per supply centre.
    In a solo, the soloer instead receives 90 points.
    In a non-solo game, a sole board topper at least 3 centres ahead
    receives 10 points per centre of lead, capped at 60. Each other
    survivor pays an equal share rounded down to a whole point.
    Finally, players receive one point for each year survived, including
    their elimination year or the final year for survivors.
    """

    def __init__(self):
        self.name = _('Gap Incentivised Rank SC Hybrid')
        self.rank_points = [130, 90, 60, 40, 30, 20, 10]
        self.dead_score_can_change = False

    @staticmethod
    def _survival_score(state, power):
        elimination_year = state.year_eliminated(power)
        scoring_year = elimination_year or state.last_full_year()
        return scoring_year - FIRST_YEAR + 1

    @staticmethod
    def _gap_scores(state):
        scores = {power: 0 for power in state.all_powers()}
        if state.soloer() is not None:
            return scores

        survivors = list(state.survivors())
        leader_centres = state.highest_dot_count()
        leaders = [power for power in survivors if state.dot_count(power) == leader_centres]
        if len(leaders) != 1:
            return scores

        leader = leaders[0]
        payers = [power for power in survivors if power != leader]
        # The rules of the game guarantee at least one other survivor
        assert payers
        second_centres = max(state.dot_count(power) for power in payers)
        gap = leader_centres - second_centres
        if gap < 3:
            return scores

        bonus = min(gap, 6) * 10
        payment = floor(bonus / len(payers))
        scores[leader] = bonus
        for power in payers:
            scores[power] = -payment
        return scores

    def scores(self, state):
        # Get rank points for each power
        powers = list(state.all_powers())
        scores = _countback_rank_scores(state,
                                        state.last_full_year(),
                                        powers,
                                        self.rank_points)
        soloer = state.soloer()
        gap_scores = self._gap_scores(state)
        # Add centre-count and solo bonuses, then the survival and gap penalties
        for power in powers:
            if soloer is None:
                if state.dot_count(power) > 0:
                    scores[power] += 5 * state.dot_count(power)
            elif power == soloer:
                scores[power] += 90
            scores[power] += gap_scores[power]
            scores[power] += self._survival_score(state, power)
        return _sorted_scores(scores, state)
