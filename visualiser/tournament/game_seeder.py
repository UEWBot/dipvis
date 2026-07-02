# Diplomacy Tournament Game Seeder
# Copyright (C) 2018 Chris Brand
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
Assign players to Diplomacy games in a tournament setting.
"""

import copy
import itertools
import random
#No auto until python 3.6
#from enum import Enum, auto
from enum import Enum
from operator import itemgetter

from django.utils.translation import gettext as _


class InvalidPlayer(Exception):
    """A player is invalid in some way (unknown, already present, etc)."""
    pass


class InvalidKey(Exception):
    """A key is invalid in some way (duplicated, duplicates a player, etc)."""
    pass


class InvalidPlayerCount(Exception):
    """An invalid number of players. Diplomacy is a seven-player game."""
    pass


class InvalidPlayerPairing(Exception):
    """It is meaningless to pair a player with themselves."""
    pass


class InvalidWeight(Exception):
    """It is meaningless to add a bias with a weight of zero."""
    pass


class PowersNotUnique(Exception):
    """Each player has to play a distinct power."""
    pass


class ImpossibleToSeed(Exception):
    """There is no valid seeding for the player set."""
    pass


class _AssignmentFailed(Exception):
    """
    Internal exception used when we end up with an invalid assignment of players to games.
    """
    pass


class SeedMethod(Enum):
    """
    Method to use to seed games

    RANDOM - try a number of random seedings plus modifications
             and pick the best
    EXHAUSTIVE - try every possible seeding and pick the best (slow)
    BOARD - board-first heuristic assignment plus swap improvements
    """
    #RANDOM = auto()
    #EXHAUSTIVE = auto()
    RANDOM = 1
    EXHAUSTIVE = 2
    BOARD = 3


class GameSeeder:
    """
    Assigns Diplomacy players to games to minimise the number of people they play again.

    Three algorithms are supported:
    EXHAUSTIVE
        Try every possible seeding. This will take a long time with many
        players.
        It may also exhaust memory. Definitely not recommended for 28 players,
        and may well not work with 21.
    RANDOM
        Initially assigns players at random to games, then tries swapping
        players at random between games.
        The number of candidate seedings and the number of iterations can both
        be specified.
    BOARD
        Assign players board-by-board using a constrained badness heuristic,
        then repeatedly improve by swapping player pairs between boards.
    In all cases, a fitness measure is used to determine the best candidate
    seeding.
    """
    def __init__(self,
                 powers,
                 seed_method,
                 starts=1,
                 iterations=1000):
        """
        Create a GameSeeder object

        powers is a list of powers that can be played. Anything unique can be
        used to identify a power.
        seed_method specifies the algorithm used to find a candidate seeding:
            RANDOM - pick sets of players at random
            EXHAUSTIVE - try every possible seeding
            BOARD - board-first heuristic assignment and local optimisation
        starts is the number of initial seedings to generate. Not used with
        EXHAUSTIVE seed_method.
        iterations is the number of times to modify each initial seeding in an
        attempt to improve it. Not used with EXHAUSTIVE or BOARD seed_methods.
        """
        self.games_played = False
        self.seed_method = seed_method
        if seed_method in (SeedMethod.RANDOM, SeedMethod.BOARD):
            self.starts = starts
        if seed_method in (SeedMethod.RANDOM,):
            self.iterations = iterations
        # List of players to use to seed games
        self.players = []
        # Dict, keyed by player, of dicts, keyed by (other) player,
        # of integer counts of shared games
        self.games_played_matrix = {}
        self.powers = powers
        self.num_powers = len(powers)
        # Dict, keyed by player, of dicts, keyed by power,
        # of integer counts of games the player has played that power
        self.powers_played = {}

    def add_player(self, player):
        """
        Add a player to take into account.

        Player is assumed to have played no games.
        Can raise InvalidPlayer if the player is already present.
        """
        if player in self.games_played_matrix:
            raise InvalidPlayer(str(player))
        self.players.append(player)
        self.games_played_matrix[player] = {}
        self.powers_played[player] = {}
        for p in self.powers:
            self.powers_played[player][p] = 0

    def _add_played_game(self, game, matrix):
        """
        Add a previously-played game to take into account.

        game is either a set of (player, power) 2-tuples, or a set of players
        (player can be any type as long as it's the same in all calls to this object).
        Can raise InvalidPlayer if any player is unknown.
        Raises InvalidPlayerCount if the game doesn't have seven players.
        """
        with_powers = False
        for x in game:
            if with_powers or isinstance(x, tuple):
                with_powers = True
                player1, power1 = x
            else:
                player1 = x
            if player1 not in matrix:
                raise InvalidPlayer(str(player1))
            for x in game:
                if with_powers:
                    player2, _ = x
                else:
                    player2 = x
                if player1 != player2:
                    try:
                        matrix[player1][player2] += 1
                    except KeyError:
                        if player2 not in matrix:
                            raise InvalidPlayer(str(player2))
                        matrix[player1][player2] = 1
            if with_powers:
                self.powers_played[player1][power1] += 1
        self.games_played = True

    def add_played_game(self, game):
        """
        Add a previously-played game to take into account.

        game is a set of (player, power) 2-tuples (player can be any type as
        long as it's the same in all calls to this object).
        Can raise InvalidPlayer if any player is unknown.
        Raises InvalidPlayerCount if the game doesn't have seven players.
        Raises PowersNotUnique if any power is present more than once.
        """
        if len(game) != self.num_powers:
            raise InvalidPlayerCount(str(len(game)))
        # Check that each power is only present once
        if len(set([power for player, power in game])) != self.num_powers:
            raise PowersNotUnique()
        self._add_played_game(game, self.games_played_matrix)

    def _add_bias(self, player1, player2, weight):
        """
        Add a bias to take into account.

        This effectively says "treat player1 and player2 as if they have
        already played weight games together". If called again with the
        same pair of players, the weights will be added.
        It is intended to be used to keep pairs of players apart, e.g. family
        members.
        Could also be used to make pairs of players more likely to play
        together if weight is negative.
        Can raise InvalidWeight if weight is zero.
        Can raise InvalidPlayer if any player is unknown.
        Raises InvalidPlayerPairing if player1 == player2.
        """
        if player1 == player2:
            raise InvalidPlayerPairing(str(player1))
        if weight == 0:
            raise InvalidWeight(str(weight))
        if player1 not in self.games_played_matrix:
            raise InvalidPlayer(str(player1))
        if player2 not in self.games_played_matrix:
            raise InvalidPlayer(str(player2))
        try:
            self.games_played_matrix[player1][player2] += weight
        except KeyError:
            self.games_played_matrix[player1][player2] = weight
        try:
            self.games_played_matrix[player2][player1] += weight
        except KeyError:
            self.games_played_matrix[player2][player1] = weight
        # fitness is now meaningful
        self.games_played = True

    # This is the value used by add_bias()
    # It represents the number of games the two players will be assumed to have played together
    _BIAS_WEIGHT = 25

    # This value is used internally to keep players playing two games each apart
    _TEMP_WEIGHT = 10

    def add_bias(self, player1, player2):
        """
        Add a bias to take into account.

        This effectively says "treat player1 and player2 as if they have
        already played several games together".
        It is intended to be used to keep pairs of players apart, e.g. family
        members.
        Can raise InvalidPlayer if any player is unknown.
        Raises InvalidPlayerPairing if player1 == player2.
        """
        self._add_bias(player1, player2, self._BIAS_WEIGHT)

    def _power_fitness(self, game):
        """
        Returns a fitness score (0-??) for a game. Lower is better.

        In this case, a game is a set of (player, power) 2-tuples.
        The value returned is the sum of the number of times each player has
        previously played the specified power.
        """
        f = 0
        for player, power in game:
            f += self.powers_played[player][power]
        return f

    def _assign_some_powers(self, players, powers):
        """
        Returns a list of sets of (player, power) 2- tuples.

        This is the set of all possible games with that player and power list.
        """
        assert len(players) == len(powers)
        # If there's just one player left, there's only one possible game
        if len(players) == 1:
            pair = (players[0], powers[0])
            game = set()
            game.add(pair)
            result = []
            result.append(game)
            return result
        result = []
        player = players.pop(0)
        for power in powers:
            pair = (player, power)
            powers2 = powers.copy()
            powers2.remove(power)
            for game in self._assign_some_powers(players.copy(), powers2):
                game.add(pair)
                result.append(game)
        return result

    def _assign_powers(self, game):
        """
        Returns a 2-tuple containing a set of (player, power) 2-tuples and a list of "issues".

        game is a set of players.
        """
        # Try every combination of power assignments in a random order,
        # and keep the best
        best_fitness = 99999
        player_list = list(game)
        power_list = list(self.powers)
        random.shuffle(player_list)
        games = self._assign_some_powers(player_list, power_list)
        for g in games:
            score = self._power_fitness(g)
            if score < best_fitness:
                best_fitness = score
                best_result = g
        issues = []
        if best_fitness > 0:
            issues.append(_('Game has %(num)d player(s) who have already played their power') % {'num': best_fitness})
        return best_result, issues

    def _fitness_score(self, game, games_played_matrix=None):
        """
        Returns a fitness score (0-??) for a game. Lower is better.

        In this case, a game is just a set of seven players.
        The value returned is twice the square of the number of times each pair
        of players has played together already.
        game is a set of players (player can be any type as long as it's the
        same in all calls to this object).
        """
        if games_played_matrix is None:
            games_played_matrix = self.games_played_matrix
        f = 0
        # Sum the number of times each pair of players has played together
        for p in game:
            for q in game:
                if p != q:
                    try:
                        f += (games_played_matrix[p][q] ** 2)
                    except KeyError:
                        # These players have not played each other
                        pass
        return f

    def _assign_players_to_games_randomly(self, players):
        """
        Assign all the players provided to games completely at random, with no weighting.

        Returns a list of sets of players.
        len(players) must be a multiple of the number of powers.
        Raises _AssignmentFailed if the algorithm messes up.
        """
        res = []
        game = set()
        while players:
            if ((len(players) == self.num_powers)
                    and (len(set(players)) < self.num_powers)):
                # We have just seven players left, but not seven unique players
                raise _AssignmentFailed
            # Pick a random player to add to the current game
            p = random.choice(list(players))
            if p in game:
                # This player is no good
                continue
            players.remove(p)
            game.add(p)
            if len(game) == self.num_powers:
                # Done with this game. Start a new one
                res.append(game)
                game = set()
        return res

    def _set_fitness(self, games, include_these_games=False):
        """
        Calculate a total fitness score for this set of games.

        Range is 0-(42 * len(games)). Lower is better.
        If include_these_games is True, add in a fitness score
        for the games in this set. This helps keeps players
        playing two games apart but is more work
        """
        fitness = 0
        matrix = {}
        for g in games:
            if include_these_games:
                for player in g:
                    if player not in matrix:
                        matrix[player] = {}
            fitness += self._fitness_score(g, self.games_played_matrix)
            if include_these_games:
                fitness += self._fitness_score(g, matrix)
                self._add_played_game(g, matrix)
        return fitness

    def _improve_fitness(self, games, include_these_games=False):
        """
        Try to modify a list of games to find a better set.

        Swaps random players between games in an attempt to improve the
        overall fitness score.
        Returns the best set of games it finds and the fitness score
        for that set.
        If include_these_games is True, add in a fitness score
        for the games in this set. This helps keeps players
        playing two games apart but is more work
        """
        best_set = copy.deepcopy(games)
        best_fitness = self._set_fitness(games, include_these_games)
        # There's nothing to do if we only have one game
        if len(games) >= 2:
            # The more iterations, the better the result, but the longer it takes
            for _ in range(self.iterations):
                # Try swapping a random player between two random games
                g1, g2 = random.sample(games, 2)
                # Pick a player from each game that isn't also playing the other
                p1 = random.choice(list(g1 - g2))
                p2 = random.choice(list(g2 - g1))
                g1.remove(p1)
                g2.remove(p2)
                g1.add(p2)
                g2.add(p1)
                fitness = self._set_fitness(games, include_these_games)
                if fitness < best_fitness:
                    #print("Improving fitness from %d to %d" % (best_fitness, fitness))
                    #print(games)
                    best_fitness = fitness
                    best_set = copy.deepcopy(games)
                    if best_fitness == 0:
                        # A perfect score cannot be improved further.
                        break
        return best_set, best_fitness

    def _assign_players_wrapper(self, players):
        """
        Wrapper that just keeps calling _assign_players_to_games_randomly() until it succeeds.
        """
        while True:
            # _assign_players_to_game() will empty the set of players we pass it
            p = players.copy()
            try:
                res = self._assign_players_to_games_randomly(p)
                break
            except _AssignmentFailed:
                pass
        return res

    def _board_seed_games_once(self,
                               players,
                               include_these_games=False,
                               optimise_swaps=True):
        """
        Assign players to boards using a board-first badness heuristic.

        players is a list that can contain duplicates when players are
        doubling up. Duplicates are treated as distinct entries, but two
        entries representing the same player are never allowed in one board.
        """
        if len(players) % self.num_powers != 0:
            raise InvalidPlayerCount(f'{len(players)} is not an exact multiple of {self.num_powers}')

        num_boards = len(players) // self.num_powers
        entry_players = list(players)
        num_entries = len(entry_players)
        boards = [[] for _ in range(num_boards)]
        board_player_sets = [set() for _ in range(num_boards)]
        unassigned = set(range(len(entry_players)))

        # Pairwise badness between entry indices, derived from historical matrix.
        pair_badness = [[0] * num_entries for _ in range(num_entries)]
        pair_score = [[0] * num_entries for _ in range(num_entries)]
        for i, player_i in enumerate(entry_players):
            for j, player_j in enumerate(entry_players):
                if i == j:
                    continue
                # Two copies of one player should never share a game.
                if player_i == player_j:
                    pair_badness[i][j] = self._BIAS_WEIGHT * 1000
                    pair_score[i][j] = pair_badness[i][j] ** 2
                    continue
                pair_badness[i][j] = self.games_played_matrix[player_i].get(player_j, 0)
                pair_score[i][j] = pair_badness[i][j] ** 2

        for _ in range(len(entry_players)):
            badness_matrix = [[0] * num_entries for _ in range(num_boards)]
            for b_idx, board in enumerate(boards):
                if len(board) >= self.num_powers:
                    continue
                for entry in range(num_entries):
                    badness = 0
                    for existing in board:
                        badness += pair_badness[entry][existing]
                    badness_matrix[b_idx][entry] = badness

            player_to_min_badness = {}
            for entry in unassigned:
                candidate_scores = []
                for b_idx, board in enumerate(boards):
                    if len(board) >= self.num_powers:
                        continue
                    # Never allow identical player objects in one game.
                    if entry_players[entry] in board_player_sets[b_idx]:
                        continue
                    candidate_scores.append(badness_matrix[b_idx][entry])
                if not candidate_scores:
                    raise _AssignmentFailed
                player_to_min_badness[entry] = min(candidate_scores)

            critical_value = max(player_to_min_badness.values())
            set1 = [entry for entry in unassigned if player_to_min_badness[entry] == critical_value]

            min_options = min(
                len([
                    b_idx for b_idx, board in enumerate(boards)
                    if (
                        len(board) < self.num_powers
                        and (entry_players[entry] not in board_player_sets[b_idx])
                        and (badness_matrix[b_idx][entry] == critical_value)
                    )
                ])
                for entry in set1
            )

            set2 = [
                entry for entry in set1
                if len([
                    b_idx for b_idx, board in enumerate(boards)
                    if (
                        len(board) < self.num_powers
                        and (entry_players[entry] not in board_player_sets[b_idx])
                        and (badness_matrix[b_idx][entry] == critical_value)
                    )
                ]) == min_options
            ]

            chosen_entry = random.choice(set2)
            possible_boards = [
                b_idx for b_idx, board in enumerate(boards)
                if (
                    len(board) < self.num_powers
                    and (entry_players[chosen_entry] not in board_player_sets[b_idx])
                    and (badness_matrix[b_idx][chosen_entry] == critical_value)
                )
            ]
            if not possible_boards:
                raise _AssignmentFailed

            freest = min(len(boards[b_idx]) for b_idx in possible_boards)
            restricted_boards = [b_idx for b_idx in possible_boards if len(boards[b_idx]) == freest]
            board_choice = random.choice(restricted_boards)

            boards[board_choice].append(chosen_entry)
            board_player_sets[board_choice].add(entry_players[chosen_entry])
            unassigned.remove(chosen_entry)

        board_entries = [board.copy() for board in boards]

        def entries_to_games(entry_boards):
            return [set(entry_players[idx] for idx in board) for board in entry_boards]

        def board_hist_fitness(entry_board):
            score = 0
            for i in entry_board:
                for j in entry_board:
                    if i != j:
                        score += pair_score[i][j]
            return score

        if include_these_games:
            best_games = entries_to_games(board_entries)
            best_fitness = self._set_fitness(best_games, include_these_games)
            board_costs = None
            current_fitness = best_fitness
        else:
            board_costs = [board_hist_fitness(board) for board in board_entries]
            current_fitness = sum(board_costs)
            best_fitness = current_fitness
            best_games = entries_to_games(board_entries)
        best_entries = [board.copy() for board in board_entries]
        if not optimise_swaps:
            return best_games, best_fitness

        # Greedy pair-swap improvement pass, similar to the contributed script.
        improved = True
        while improved and len(board_entries) >= 2:
            if best_fitness == 0:
                break
            improved = False
            for g1_idx in range(len(board_entries)):
                if improved:
                    break
                for p1_idx in range(self.num_powers):
                    if improved:
                        break
                    for g2_idx in range(g1_idx + 1, len(board_entries)):
                        if improved:
                            break
                        for p2_idx in range(self.num_powers):
                            p1 = board_entries[g1_idx][p1_idx]
                            p2 = board_entries[g2_idx][p2_idx]
                            if p1 == p2:
                                continue
                            v1 = entry_players[p1]
                            v2 = entry_players[p2]
                            if (v2 in board_player_sets[g1_idx]) or (v1 in board_player_sets[g2_idx]):
                                continue

                            old1 = board_costs[g1_idx] if board_costs is not None else None
                            old2 = board_costs[g2_idx] if board_costs is not None else None

                            board_entries[g1_idx][p1_idx] = p2
                            board_entries[g2_idx][p2_idx] = p1
                            board_player_sets[g1_idx].remove(v1)
                            board_player_sets[g1_idx].add(v2)
                            board_player_sets[g2_idx].remove(v2)
                            board_player_sets[g2_idx].add(v1)

                            if include_these_games:
                                candidate_games = entries_to_games(board_entries)
                                candidate_fitness = self._set_fitness(candidate_games,
                                                                      include_these_games)
                            else:
                                new1 = board_hist_fitness(board_entries[g1_idx])
                                new2 = board_hist_fitness(board_entries[g2_idx])
                                candidate_fitness = current_fitness - old1 - old2 + new1 + new2

                            if candidate_fitness < best_fitness:
                                best_fitness = candidate_fitness
                                if include_these_games:
                                    best_games = candidate_games
                                else:
                                    board_costs[g1_idx] = new1
                                    board_costs[g2_idx] = new2
                                    current_fitness = candidate_fitness
                                best_entries = [board.copy() for board in board_entries]
                                improved = True
                                if best_fitness == 0:
                                    break
                                break

                            # Revert unsuccessful swap.
                            board_entries[g1_idx][p1_idx] = p1
                            board_entries[g2_idx][p2_idx] = p2
                            board_player_sets[g1_idx].remove(v2)
                            board_player_sets[g1_idx].add(v1)
                            board_player_sets[g2_idx].remove(v1)
                            board_player_sets[g2_idx].add(v2)

            if improved:
                board_entries = [board.copy() for board in best_entries]

        if not include_these_games:
            best_games = entries_to_games(best_entries)
        return best_games, best_fitness

    def _seed_games_board(self, omitting_players, players_doubling_up):
        """
        Generate seedings using the board-first heuristic method.

        Returns a 2-tuple of (best seeding, fitness).
        """
        players = self._player_pool(omitting_players, players_doubling_up)
        if not players:
            return [], 0
        if len(players) % self.num_powers != 0:
            raise InvalidPlayerCount(f'{len(self.games_played_matrix)} total plus {len(players_doubling_up)} duplicated minus {len(omitting_players)} omitted')
        if players_doubling_up and (len(players) < 2 * self.num_powers):
            raise ImpossibleToSeed(f'{len(self.games_played_matrix)} total plus {len(players_doubling_up)} duplicated minus {len(omitting_players)} omitted')

        starts = 1
        if self.games_played or (len(players_doubling_up) > 1):
            starts = self.starts

        include_these_games = (len(players_doubling_up) > 1)
        optimise_swaps = self.games_played or include_these_games
        best_seeding = None
        best_fitness = None

        for _ in range(starts):
            try:
                seeding, fitness = self._board_seed_games_once(players,
                                                               include_these_games,
                                                               optimise_swaps)
            except _AssignmentFailed as e:
                raise ImpossibleToSeed from e
            if (best_fitness is None) or (fitness < best_fitness):
                best_seeding = seeding
                best_fitness = fitness
            if best_fitness == 0:
                # This is as good as it gets, so no point continuing
                break

        return best_seeding, best_fitness

    def _all_possible_seedings(self, players):
        """
        Returns a list of all possible seedings (each being a list of sets of players).

        It will also include seedings with the same games in different orders.
        Note that this will take a long time for large numbers of players.
        Raises _AssignmentFailed if no valid games can be formed from the
        specified players.
        """
        if len(players) % self.num_powers != 0:
            raise InvalidPlayerCount(f'{len(players)} is not an exact multiple of {self.num_powers}')
        if len(set(players)) < self.num_powers:
            # We've ended up with a group of players that we can't make a valid game from
            raise _AssignmentFailed
        if len(players) == self.num_powers:
            # With this number of players, there is exactly one possible game,
            # and therefore exactly one possible seeding
            return [[set(players)]]
        res = []
        # Go through all possible combinations for the first game:
        for t in itertools.combinations(players, self.num_powers):
            game = set(t)
            if len(game) != self.num_powers:
                # Can't have any players playing themselves
                continue
            # Make a copy of players, and remove the players in game
            p2 = players.copy()
            for p in game:
                p2.remove(p)
            # Now we can create each possible set that includes this game
            try:
                for s in self._all_possible_seedings(p2):
                    s.append(game)
                    res.append(s)
            except _AssignmentFailed:
                # No possible valid games with the remaining players
                continue
        return res

    def _player_pool(self, omitting_players, players_doubling_up):
        """
        Create a pool of players to seed into games

        Returns a list of players containing every known player and every
        player doubling up, but excluding any players in omitting_players.
        """
        # Come up with a list of players to draw from
        players = list(self.games_played_matrix.keys())
        if set(omitting_players) & set(players_doubling_up):
            raise ImpossibleToSeed(f'omitting_players and players_doubling_up are not disjoint')
        # Check the players_doubling_up list
        for p in players_doubling_up:
            if p not in players:
                raise InvalidPlayer(str(p))
        # Omit any players who aren't playing this round
        for p in omitting_players:
            if p not in players:
                raise InvalidPlayer(str(p))
            players.remove(p)
        # Add in any duplicate players
        players += list(players_doubling_up)
        return players

    def _seed_games(self, omitting_players, players_doubling_up):
        """
        Seed players into games

        Returns a list of games, where each game is a set of players, and the
        fitness score for the set.
        omitting_players is a set of previously-added players not to assign
        to games.
        players_doubling_up is an optional set of previously-added players to
        assign to two games each.
        Can raise InvalidPlayer if any player in omitting_players or
        players_doubling_up is unknown.
        Can raise InvalidPlayerCount if the resulting number of players isn't
        an exact multiple of the number of powers.
        """
        players = self._player_pool(omitting_players, players_doubling_up)
        if not players:
            return [], 0
        # Check that we have a multiple of seven players
        if len(players) % self.num_powers != 0:
            raise InvalidPlayerCount(f'{len(self.games_played_matrix)} total plus {len(players_doubling_up)} duplicated minus {len(omitting_players)} omitted')
        # If any players are playing two games, there must be at least two games
        if players_doubling_up:
            if len(players) < 2 * self.num_powers:
                raise ImpossibleToSeed(f'{len(self.games_played_matrix)} total plus {len(players_doubling_up)} duplicated minus {len(omitting_players)} omitted')
        res = self._assign_players_wrapper(players)
        # There's no point iterating if all solutions have a fitness of zero
        if self.games_played or (len(players_doubling_up) > 1):
            res, fitness = self._improve_fitness(res, include_these_games=(len(players_doubling_up) > 1))
        else:
            fitness = 0
        # Return the resulting list of games
        return res, fitness

    def seed_games_and_powers(self, omitting_players=(), players_doubling_up=()):
        """
        Seed players into games and assign powers

        Returns a list of games, where each game is a 2-tuple containing a set of
        (player, power) 2-tuples and a list of issues.
        Parameters and exceptions are the same as seed_games()
        """
        result = []
        games = self.seed_games(omitting_players, players_doubling_up)
        for game in games:
            result.append(self._assign_powers(game))
        return result

    def _add_bias_for_doublers(self, players_doubling_up, add):
        """
        Keep players playing two games in a round apart by adding bias

        Adds or removes bias for every possible pair of players in the list.
        add is a boolean = True to add bias, False to add negative bias,
        undoing an earlier call with add=True.
        """
        if add:
            w = self._TEMP_WEIGHT
        else:
            w = -self._TEMP_WEIGHT
        for (p1, p2) in itertools.combinations(players_doubling_up, 2):
            self._add_bias(p1, p2, w)

    def seed_games(self, omitting_players=(), players_doubling_up=()):
        """
        Seed players into games

        Returns a list of games, where each game is a set of players.
        omitting_players is an optional set of previously-added players not to
        assign to games.
        players_doubling_up is an optional set of previously-added players to
        assign to two games each.
        Internally, this will generate the number of sets specified when the
        class was instantiated, and return the best one.
        Can raise InvalidPlayer if any player in omitting_players is unknown.
        Can raise InvalidPlayerCount if the resulting number of players isn't
        an exact multiple of the number of powers.
        Can raise ImpossibleToSeed if no valid seeding is possible.
        """
        # Add temporary bias to keep players_doubling_up apart
        self._add_bias_for_doublers(players_doubling_up, add=True)
        try:
            # Generate the specified number of seedings
            # Use the random method if no games have been played yet and at most
            # one player is playing two games, because any seeding is fine.
            if self.seed_method == SeedMethod.BOARD:
                seedings = [self._seed_games_board(omitting_players,
                                                   players_doubling_up)]
            elif ((not self.games_played) and (len(players_doubling_up) < 2)) or (self.seed_method == SeedMethod.RANDOM):
                seedings = []
                # No point generating multiples if they're all equally good
                starts = 1
                if self.games_played or (len(players_doubling_up) > 1):
                    starts = self.starts
                for _ in range(starts):
                    # This gives us a list of 2-tuples with (seeding, fitness)
                    candidate = self._seed_games(omitting_players,
                                                 players_doubling_up)
                    seedings.append(candidate)
                    if candidate[1] == 0:
                        # Perfect random seeding found; no need to evaluate more starts.
                        break
            else:  # self.seed_method == SeedMethod.EXHAUSTIVE
                players = self._player_pool(omitting_players, players_doubling_up)
                seedings = []
                try:
                    for s in self._all_possible_seedings(players):
                        fitness = self._set_fitness(s, include_these_games=(len(players_doubling_up) > 1))
                        seedings.append((s, fitness))
                except _AssignmentFailed as e:
                    # Remove temporary bias
                    self._add_bias_for_doublers(players_doubling_up, add=False)
                    raise ImpossibleToSeed from e
            # Sort them by fitness
            seedings.sort(key=itemgetter(1))
            if self.seed_method == SeedMethod.RANDOM:
                bg_str = f'With starts={self.starts} and iterations={self.iterations}'
            elif self.seed_method == SeedMethod.BOARD:
                bg_str = f'With Board seeding, starts={self.starts}'
            else:
                bg_str = 'With Exhaustive seeding'
            print(f'{bg_str}, best fitness score is {seedings[0][1]} in {len(seedings)} seedings')
        finally:
            # Remove temporary bias
            self._add_bias_for_doublers(players_doubling_up, add=False)
        # Return the best (we don't care if multiple seedings are equally good)
        return seedings[0][0]
