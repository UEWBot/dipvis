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
import json
import logging
import random
from collections import Counter
from enum import Enum, auto
from operator import itemgetter

from django.conf import settings
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

# Default for settings.GAME_SEEDER_MAX_EXHAUSTIVE_PLAYERS
DEFAULT_MAX_EXHAUSTIVE_PLAYERS = 14

_REPLAY_HINT = 'To reproduce, pass this (after json.loads()) to GameSeeder.replay():\n'


class InvalidPlayer(Exception):
    """A player is invalid in some way (unknown, already present, etc)."""
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
    RANDOM = auto()
    EXHAUSTIVE = auto()
    BOARD = auto()


def _unique_names(names):
    """Return a copy of a list of names, numbering any duplicates to make them unique"""
    counts = Counter(names)
    seen = Counter()
    result = []
    for name in names:
        seen[name] += 1
        result.append(name if counts[name] == 1 else f'{name} #{seen[name]}')
    return result


def _doublers_placeable(need, forbidden, capacity):
    """
    Can each player p be put on need[p] distinct boards, none in forbidden[p],
    without putting more than capacity[b] players on board b?

    Uses augmenting paths (max flow), so the answer is exact.
    """
    if sum(need.values()) > sum(capacity):
        return False
    free = list(capacity)
    on_board = {p: set() for p in need}

    def augment(p, visited):
        for b in range(len(free)):
            if (b in visited) or (b in forbidden[p]) or (b in on_board[p]):
                continue
            visited.add(b)
            if free[b] > 0:
                free[b] -= 1
                on_board[p].add(b)
                return True
            # Board b is full - try moving someone off it
            for q in need:
                if b in on_board[q]:
                    on_board[q].remove(b)
                    if augment(q, visited):
                        on_board[p].add(b)
                        return True
                    on_board[q].add(b)
        return False

    return all(augment(p, set()) for p, n in need.items() for _ in range(n))


class GameSeeder:
    """
    Assigns Diplomacy players to games to minimise the number of people they play again.

    Three algorithms are supported:
    EXHAUSTIVE
        Try every possible seeding. This will take a long time with many
        players, and may exhaust memory, so the number of players (counting
        players doubling up twice) is limited by
        settings.GAME_SEEDER_MAX_EXHAUSTIVE_PLAYERS (default 14).
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
                 iterations=1000,
                 random_seed=None):
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
        random_seed seeds the random number generator, making the results
        repeatable (e.g. for testing). By default, a random seed is chosen.
        Either way, it is recorded so that problems can be reproduced
        (see state() and replay()).
        """
        if random_seed is None:
            random_seed = random.SystemRandom().randrange(2 ** 32)
        self.random_seed = random_seed
        self._random = random.Random(random_seed)
        self._init_args = {'seed_method': seed_method.name,
                           'starts': starts,
                           'iterations': iterations}
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
        self.powers = list(powers)
        self.num_powers = len(self.powers)
        # Dict, keyed by player, of dicts, keyed by power,
        # of integer counts of games the player has played that power
        self.powers_played = {}
        # Positions of players and powers in self.players and self.powers
        self._player_index = {}
        self._power_index = {p: i for i, p in enumerate(self.powers)}
        # Everything this seeder has been told, in order, so that it can be replayed
        self._operations = []

    def add_player(self, player):
        """
        Add a player to take into account.

        Player is assumed to have played no games.
        Can raise InvalidPlayer if the player is already present.
        """
        if player in self.games_played_matrix:
            raise InvalidPlayer(str(player))
        self._player_index[player] = len(self.players)
        self.players.append(player)
        self.games_played_matrix[player] = {}
        self.powers_played[player] = {}
        for p in self.powers:
            self.powers_played[player][p] = 0
        self._operations.append(['add_player', self._player_index[player]])

    def _in_player_order(self, players):
        """
        Return the players in a collection, in the order they were added.

        Set iteration order can vary from run to run, so use this before making
        random choices, to keep results repeatable with a given random_seed.
        """
        return [p for p in self.players if p in players]

    def _add_played_game(self, game, matrix):
        """
        Add a previously-played game to take into account.

        game is either a set of (player, power) 2-tuples, or a set of players
        (player can be any type as long as it's the same in all calls to this object).
        Can raise InvalidPlayer if any player is unknown.
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
        self._operations.append(['add_played_game',
                                 sorted([self._player_index[player], self._power_index[power]]
                                        for player, power in game)])

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

    # Worst measured failure rate per attempt is ~0.54, so 100 failures means a bug, not bad luck
    _MAX_RANDOM_ATTEMPTS = 100

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
        self._operations.append(['add_bias', self._player_index[player1], self._player_index[player2]])

    def _assign_powers(self, game, this_round):
        """
        Returns a 2-tuple containing a set of (player, power) 2-tuples and a list of "issues".

        game is a set of players.
        this_round is a Counter, keyed by (player, power), of powers already
        assigned in other games this round.
        The powers are assigned to minimise the total number of times players
        have already played their power, including earlier games this round.
        """
        player_list = self._in_player_order(game)
        # Shuffle the players so that ties are broken randomly
        self._random.shuffle(player_list)
        costs = [[self.powers_played[player][power] + this_round[(player, power)]
                  for power in self.powers]
                 for player in player_list]
        # Try every combination of power assignments, and keep the best
        best_fitness = None
        for perm in itertools.permutations(range(self.num_powers)):
            score = sum(row[i] for row, i in zip(costs, perm))
            if (best_fitness is None) or (score < best_fitness):
                best_fitness = score
                best_perm = perm
                if best_fitness == 0:
                    # This is as good as it gets - no player has played their power before
                    break
        best_result = {(player, self.powers[i]) for player, i in zip(player_list, best_perm)}
        issues = []
        repeats = sum(1 for player, power in best_result if self.powers_played[player][power])
        if repeats:
            issues.append(_('Game has %(num)d player(s) who have already played their power') % {'num': repeats})
        same_power = sum(1 for player, power in best_result if this_round[(player, power)])
        if same_power:
            issues.append(_('Game has %(num)d player(s) playing the same power in both their games this round') % {'num': same_power})
        return best_result, issues

    def _fitness_score(self, game, earlier_meetings=None):
        """
        Returns a fitness score (0-??) for a game. Lower is better.

        In this case, a game is just a set of seven players.
        The value returned is twice the square of the number of times each pair
        of players has played together already.
        game is a set of players (player can be any type as long as it's the
        same in all calls to this object).
        earlier_meetings is an optional Counter, keyed by (player, player), of
        additional meetings to add to those already played.
        """
        f = 0
        # Sum the number of times each pair of players has played together
        for p in game:
            played = self.games_played_matrix[p]
            for q in game:
                if p != q:
                    n = played.get(q, 0)
                    if earlier_meetings:
                        n += earlier_meetings[(p, q)]
                    f += n ** 2
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
                raise _AssignmentFailed(f"{self.num_powers} remaining players includes duplicates")
            # Pick a random player to add to the current game
            p = self._random.choice(players)
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

    def _set_fitness(self, games):
        """
        Calculate a total fitness score for this set of games. Lower is better.

        Meetings in earlier games in the set are added to the previous meetings
        before squaring, so a pair meeting twice in the set costs as much as
        one more previous meeting.
        """
        if sum(len(g) for g in games) - len(set().union(*games)) < 2:
            # Fewer than two players in more than one game, so nobody can meet twice
            return sum(self._fitness_score(g) for g in games)
        appearances = Counter(p for g in games for p in g)
        repeated = {p for p, n in appearances.items() if n > 1}
        fitness = 0
        this_set = Counter()
        for g in games:
            fitness += self._fitness_score(g, this_set)
            # Only players in more than one game can meet again
            in_game = repeated.intersection(g)
            this_set.update((p, q) for p in in_game for q in in_game if p != q)
        return fitness

    def _improve_fitness(self, games):
        """
        Try to modify a list of games to find a better set.

        Swaps random players between games in an attempt to improve the
        overall fitness score.
        Returns the best set of games it finds and the fitness score
        for that set.
        """
        best_set = copy.deepcopy(games)
        best_fitness = self._set_fitness(games)
        # There's nothing to do if we only have one game
        if len(games) >= 2:
            # The more iterations, the better the result, but the longer it takes
            for _ in range(self.iterations):
                # Try swapping a random player between two random games
                g1, g2 = self._random.sample(games, 2)
                # Pick a player from each game that isn't also playing the other
                p1 = self._random.choice(self._in_player_order(g1 - g2))
                p2 = self._random.choice(self._in_player_order(g2 - g1))
                g1.remove(p1)
                g2.remove(p2)
                g1.add(p2)
                g2.add(p1)
                fitness = self._set_fitness(games)
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
        Keep calling _assign_players_to_games_randomly() until it succeeds.

        Raises ImpossibleToSeed if it fails _MAX_RANDOM_ATTEMPTS times.
        """
        for _ in range(self._MAX_RANDOM_ATTEMPTS):
            # _assign_players_to_game() will empty the set of players we pass it
            p = players.copy()
            try:
                return self._assign_players_to_games_randomly(p)
            except _AssignmentFailed:
                pass
        raise ImpossibleToSeed(f'Random assignment failed {self._MAX_RANDOM_ATTEMPTS} times')

    def _board_seed_games_once(self,
                               players,
                               optimise_swaps=True):
        """
        Assign players to boards using a board-first badness heuristic.

        players is a list that can contain duplicates when players are
        doubling up. Duplicates are treated as distinct entries, but two
        entries representing the same player are never allowed in one board.
        """
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

        copies = Counter(entry_players)
        has_doublers = any(n > 1 for n in copies.values())
        # Swapping a doubler can then change the cost of other boards, so score the whole set
        doublers_can_meet = sum(1 for n in copies.values() if n > 1) > 1

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

            # Greedy placement alone can leave a doubler's second copy with only its own board
            # (or two copies with only one board), so only allow placements that avoid that
            need = Counter()
            if has_doublers:
                need = Counter(entry_players[e] for e in unassigned if copies[entry_players[e]] > 1)
                forbidden = {p: {b for b, s in enumerate(board_player_sets) if p in s} for p in need}
                capacity = [self.num_powers - len(board) for board in boards]

            def keeps_doublers_placeable(entry, b_idx):
                player = entry_players[entry]
                remaining = need.copy()
                if player in remaining:
                    remaining[player] -= 1
                    if not remaining[player]:
                        del remaining[player]
                if not remaining:
                    return True
                cap = capacity.copy()
                cap[b_idx] -= 1
                forb = forbidden
                if player in remaining:
                    forb = dict(forbidden)
                    forb[player] = forbidden[player] | {b_idx}
                return _doublers_placeable(remaining, forb, cap)

            allowed = {}
            for entry in unassigned:
                allowed[entry] = [b_idx for b_idx, board in enumerate(boards)
                                  if (len(board) < self.num_powers)
                                  # Never allow identical player objects in one game.
                                  and (entry_players[entry] not in board_player_sets[b_idx])
                                  and ((not need) or keeps_doublers_placeable(entry, b_idx))]

            player_to_min_badness = {}
            for entry in unassigned:
                if allowed[entry]:
                    player_to_min_badness[entry] = min(badness_matrix[b_idx][entry]
                                                       for b_idx in allowed[entry])
            if not player_to_min_badness:
                raise _AssignmentFailed("No valid placement")

            critical_value = max(player_to_min_badness.values())
            set1 = [entry for entry in player_to_min_badness
                    if player_to_min_badness[entry] == critical_value]

            options = {entry: [b_idx for b_idx in allowed[entry]
                               if badness_matrix[b_idx][entry] == critical_value]
                       for entry in set1}
            min_options = min(len(o) for o in options.values())
            set2 = [entry for entry in set1 if len(options[entry]) == min_options]

            chosen_entry = self._random.choice(set2)
            possible_boards = options[chosen_entry]

            freest = min(len(boards[b_idx]) for b_idx in possible_boards)
            restricted_boards = [b_idx for b_idx in possible_boards if len(boards[b_idx]) == freest]
            board_choice = self._random.choice(restricted_boards)

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

        if doublers_can_meet:
            best_games = entries_to_games(board_entries)
            best_fitness = self._set_fitness(best_games)
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

                            if doublers_can_meet:
                                candidate_games = entries_to_games(board_entries)
                                candidate_fitness = self._set_fitness(candidate_games)
                            else:
                                new1 = board_hist_fitness(board_entries[g1_idx])
                                new2 = board_hist_fitness(board_entries[g2_idx])
                                candidate_fitness = current_fitness - old1 - old2 + new1 + new2

                            if candidate_fitness < best_fitness:
                                best_fitness = candidate_fitness
                                if doublers_can_meet:
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

        if not doublers_can_meet:
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

        starts = 1
        if self.games_played or (len(players_doubling_up) > 1):
            starts = self.starts

        optimise_swaps = self.games_played or (len(players_doubling_up) > 1)
        best_seeding = None
        best_fitness = None

        for _ in range(starts):
            try:
                seeding, fitness = self._board_seed_games_once(players,
                                                               optimise_swaps)
            except _AssignmentFailed:
                continue
            if (best_fitness is None) or (fitness < best_fitness):
                best_seeding = seeding
                best_fitness = fitness
            if best_fitness == 0:
                # This is as good as it gets, so no point continuing
                break

        if best_fitness is None:
            raise ImpossibleToSeed(f"Tried {starts} times, and didn't find a valid seeding. doublers={players_doubling_up}")

        return best_seeding, best_fitness

    def _all_possible_seedings(self, players):
        """
        Returns a list of all possible seedings (each being a list of sets of players).

        It will also include seedings with the same games in different orders.
        Note that this will take a long time for large numbers of players.
        Raises _AssignmentFailed if no valid games can be formed from the
        specified players.
        """
        if len(set(players)) < self.num_powers:
            # We've ended up with a group of players that we can't make a valid game from
            raise _AssignmentFailed(f"{len(set(players))} players is fewer than the {self.num_powers} needed")
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

    def _check_seeding_args(self, omitting_players, players_doubling_up):
        """
        Check the arguments to a seeding call, raising an exception if they're invalid.

        Can raise ImpossibleToSeed if omitting_players and players_doubling_up
        overlap.
        Can raise InvalidPlayer if any player is unknown.
        Can raise InvalidPlayerCount if the resulting number of players isn't
        an exact multiple of the number of powers, or is too large for
        EXHAUSTIVE seeding.
        """
        if set(omitting_players) & set(players_doubling_up):
            raise ImpossibleToSeed(f'omitting_players and players_doubling_up are not disjoint')
        for p in itertools.chain(players_doubling_up, omitting_players):
            if p not in self.games_played_matrix:
                raise InvalidPlayer(str(p))
        player_count = len(self.players) - len(set(omitting_players)) + len(players_doubling_up)
        if player_count % self.num_powers != 0:
            raise InvalidPlayerCount(f'{len(self.games_played_matrix)} total plus {len(players_doubling_up)} duplicated minus {len(omitting_players)} omitted')
        if self.seed_method == SeedMethod.EXHAUSTIVE:
            max_players = getattr(settings,
                                  'GAME_SEEDER_MAX_EXHAUSTIVE_PLAYERS',
                                  DEFAULT_MAX_EXHAUSTIVE_PLAYERS)
            if player_count > max_players:
                raise InvalidPlayerCount(f'{player_count} players is more than the {max_players} allowed for EXHAUSTIVE seeding (see settings.GAME_SEEDER_MAX_EXHAUSTIVE_PLAYERS)')

    def _player_pool(self, omitting_players, players_doubling_up):
        """
        Create a pool of players to seed into games

        Returns a list of players containing every known player and every
        player doubling up, but excluding any players in omitting_players.
        """
        self._check_seeding_args(omitting_players, players_doubling_up)
        # Come up with a list of players to draw from
        players = [p for p in self.players if p not in omitting_players]
        # Add in any duplicate players
        players += self._in_player_order(players_doubling_up)
        if players and (len(set(players)) < self.num_powers):
            # We've ended up with a group of players that we can't make a valid game from
            raise ImpossibleToSeed('Too few unique players for a single game')
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
        res = self._assign_players_wrapper(players)
        # There's no point iterating if all solutions have a fitness of zero
        if self.games_played or (len(players_doubling_up) > 1):
            res, fitness = self._improve_fitness(res)
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
        return self._run_seeding('seed_games_and_powers',
                                 omitting_players,
                                 players_doubling_up,
                                 self._choose_seeding_and_powers)

    def _choose_seeding_and_powers(self, omitting_players, players_doubling_up):
        """Implementation of seed_games_and_powers()"""
        result = []
        games = self._choose_seeding(omitting_players, players_doubling_up)
        # So that players in two games aren't given the same power in both
        this_round = Counter()
        for game in games:
            game_with_powers, issues = self._assign_powers(game, this_round)
            result.append((game_with_powers, issues))
            this_round.update(game_with_powers)
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
        If seeding fails for any reason other than invalid arguments, the
        exception has a seeder_state attribute (also added as an exception
        note), which can be passed to replay() to reproduce the problem.
        """
        return self._run_seeding('seed_games',
                                 omitting_players,
                                 players_doubling_up,
                                 self._choose_seeding)

    def _run_seeding(self, operation, omitting_players, players_doubling_up, seeding_method):
        """
        Check and record a seeding call, then make it.

        If the call fails for any reason other than invalid arguments, the
        seeder's state is attached to the exception, so that the problem can be
        reproduced with replay().
        If it succeeds, the state is logged unless settings.GAME_SEEDER_LOG_STATE
        is False.
        """
        self._check_seeding_args(omitting_players, players_doubling_up)
        self._operations.append([operation,
                                 [self._player_index[p] for p in self._in_player_order(omitting_players)],
                                 [self._player_index[p] for p in self._in_player_order(players_doubling_up)]])
        try:
            result = seeding_method(omitting_players, players_doubling_up)
        except Exception as e:
            self._attach_state(e)
            raise
        if getattr(settings, 'GAME_SEEDER_LOG_STATE', True) and logger.isEnabledFor(logging.INFO):
            logger.info('Seeding succeeded. %s%s', _REPLAY_HINT, json.dumps(self.state()))
        return result

    def _attach_state(self, exc):
        """Attach the seeder's state to an exception"""
        state = self.state()
        exc.seeder_state = state
        exc.add_note(_REPLAY_HINT + json.dumps(state))

    def state(self):
        """
        Return everything needed to reproduce this seeder's behaviour.

        The result can be converted to JSON, and can be passed to replay().
        Players and powers are recorded by name, in the order they were added.
        """
        return {'version': 1,
                **self._init_args,
                'random_seed': self.random_seed,
                'powers': [str(p) for p in self.powers],
                'players': [str(p) for p in self.players],
                'operations': copy.deepcopy(self._operations)}

    @classmethod
    def replay(cls, state):
        """
        Recreate a seeder from the output of state(), and repeat everything it did.

        Players and powers are represented by their names.
        Returns the result of the last seeding call, so if that call raised an
        exception, so will this.
        """
        powers = _unique_names(state['powers'])
        players = _unique_names(state['players'])
        seeder = cls(powers,
                     SeedMethod[state['seed_method']],
                     starts=state['starts'],
                     iterations=state['iterations'],
                     random_seed=state['random_seed'])
        result = None
        for operation, *args in state['operations']:
            if operation == 'add_player':
                seeder.add_player(players[args[0]])
            elif operation == 'add_played_game':
                seeder.add_played_game({(players[i], powers[p]) for i, p in args[0]})
            elif operation == 'add_bias':
                seeder.add_bias(players[args[0]], players[args[1]])
            elif operation in ('seed_games', 'seed_games_and_powers'):
                omitting_players, players_doubling_up = args
                result = getattr(seeder, operation)({players[i] for i in omitting_players},
                                                    {players[i] for i in players_doubling_up})
            else:
                raise ValueError(f'Unknown operation {operation}')
        return result

    def _choose_seeding(self, omitting_players, players_doubling_up):
        """Implementation of seed_games()"""
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
                        fitness = self._set_fitness(s)
                        seedings.append((s, fitness))
                except _AssignmentFailed as e:
                    # Remove temporary bias
                    self._add_bias_for_doublers(players_doubling_up, add=False)
                    raise ImpossibleToSeed from e
            # Sort them by fitness
            seedings.sort(key=itemgetter(1))
        finally:
            # Remove temporary bias
            self._add_bias_for_doublers(players_doubling_up, add=False)
        # Return the best (we don't care if multiple seedings are equally good)
        return seedings[0][0]
