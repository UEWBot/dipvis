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
    Internal exception used when we end up with an invalid assignment of
    players to games.
    """
    pass


class SeedMethod(Enum):
    """
    Method to use to seed games
    RANDOM - try a number of random seedings plus modifications
             and pick the best
    EXHAUSTIVE - try every possible seeding and pick the best (slow)
    """
    #RANDOM = auto()
    #EXHAUSTIVE = auto()
    RANDOM = 1
    EXHAUSTIVE = 2


class GameSeeder:
    """
    Assigns Diplomacy players to games to minimise the number of people they
    play again.
    Two algorithms are supported:
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
    In both cases, a fitness measure is used to determine the best candidate
    seeding.
    """
    def __init__(self,
                 powers,
                 starts=1,
                 iterations=1000,
                 seed_method=SeedMethod.RANDOM):
        """
        powers is a list of powers that can be played. Anything unique can be
        used to identify a power.
        seed_method specifies the algorithm used to find a candidate seeding:
            RANDOM - pick sets of players at random
            EXHAUSTIVE - try every possible seeding
        starts is the number of initial seedings to generate. Not used with
        EXHAUSTIVE seed_method.
        iterations is the number of times to modify each initial seeding in an
        attempt to improve it. Not used with EXHAUSTIVE seed_method.
        """
        self.games_played = False
        self.seed_method = seed_method
        if seed_method == SeedMethod.RANDOM:
            self.starts = starts
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
            result = list()
            result.append(game)
            return result
        result = list()
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
        Returns a 2-tuple containing a set of (player, power) 2-tuples and
        a list of "issues".
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
        Assign all the players provided to games completely at random, with no
        weighting.
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
        Try swapping random players between games to see if we can improve the
        overall fitness score.
        Returns the best set of games it finds and the fitness score
        for that set.
        If include_these_games is True, add in a fitness score
        for the games in this set. This helps keeps players
        playing two games apart but is more work
        """
        best_set = copy.deepcopy(games)
        best_fitness = self._set_fitness(games, include_these_games)
        # The more iterations, the better the result, but the longer it takes
        for _ in range(self.iterations):
            # Try swapping a random player between two random games
            g1, g2 = random.sample(games,2)
            p1 = g1.pop()
            p2 = g2.pop()
            if (p1 in g2) or (p2 in g1):
                # Don't try to create games with players playing themselves
                g1.add(p1)
                g2.add(p2)
                continue
            g1.add(p2)
            g2.add(p1)
            fitness = self._set_fitness(games, include_these_games)
            if fitness < best_fitness:
                #print("Improving fitness from %d to %d" % (best_fitness, fitness))
                #print(games)
                best_fitness = fitness
                best_set = copy.deepcopy(games)
        return best_set, best_fitness

    def _assign_players_wrapper(self, players):
        """
        Wrapper that just keeps calling _assign_players_to_games_randomly()
        until it succeeds.
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

    def _all_possible_seedings(self, players):
        """
        Returns a list of all possible seedings (each being a list of sets of
        players).
        It will also include seedings with the same games in different orders.
        Note that this will take a long time for large numbers of players.
        Raises _AssignmentFailed if no valid games can be formed from the
        specified players.
        """
        if len(players) % self.num_powers != 0:
            raise InvalidPlayerCount("%d is not an exact multiple of %d"
                                     % (len(players), self.num_powers))
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
        Returns a list of players containing every known player and every
        player doubling up, but excluding any players in omitting_players.
        """
        # Come up with a list of players to draw from
        players = list(self.games_played_matrix.keys())
        # Check the players_doubling_up list
        for p in players_doubling_up:
            if p not in players:
                raise InvalidPlayer(str(p))
        # Add in any duplicate players
        players += list(players_doubling_up)
        # And omit any who aren't playing this round
        for p in omitting_players:
            if p not in players:
                raise InvalidPlayer(str(p))
            players.remove(p)
        return players

    def _seed_games(self, omitting_players, players_doubling_up):
        """
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
            raise InvalidPlayerCount("%d total plus %d duplicated minus %d omitted"
                                     % (len(self.games_played_matrix),
                                        len(players_doubling_up),
                                        len(omitting_players)))
        # If any players are playing two games, there must be at least two games
        if players_doubling_up:
            if len(players) < 2 * self.num_powers:
                raise ImpossibleToSeed("%d total plus %d duplicated minus %d omitted"
                                       % (len(self.games_played_matrix),
                                          len(players_doubling_up),
                                          len(omitting_players)))
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
        Returns a list of games, where each game is a 2-tuple containing a set of
        (player, power) 2-tuples and a list of issues.
        Parameters and exceptions are the same as seed_games()
        """
        result = list()
        games = self.seed_games(omitting_players, players_doubling_up)
        for game in games:
            result.append(self._assign_powers(game))
        return result

    def _add_bias_for_doublers(self, players_doubling_up, add):
        """
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
            # one player is playing two games, because any seeding is fine
            if ((not self.games_played) and (len(players_doubling_up) < 2)) or (self.seed_method == SeedMethod.RANDOM):
                seedings = []
                # No point generating multiples if they're all equally good
                starts = 1
                if self.games_played or (len(players_doubling_up) > 1):
                    starts = self.starts
                for _ in range(starts):
                    # This gives us a list of 2-tuples with (seeding, fitness)
                    seedings.append(self._seed_games(omitting_players,
                                                     players_doubling_up))
            elif self.seed_method == SeedMethod.EXHAUSTIVE:
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
                bg_str = "With starts=%d and iterations=%d" % (self.starts,
                                                               self.iterations)
            else:
                bg_str = "With Exhaustive seeding"
            print("%s, best fitness score is %d in %d seedings" % (bg_str,
                                                                   seedings[0][1],
                                                                   len(seedings)))
        finally:
            # Remove temporary bias
            self._add_bias_for_doublers(players_doubling_up, add=False)
        # Return the best (we don't care if multiple seedings are equally good)
        return seedings[0][0]
