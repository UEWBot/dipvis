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
from operator import itemgetter
#No auto until python 3.6
#from enum import Enum, auto
from enum import Enum

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

class _AssignmentFailed(Exception):
    """Internal exception used when we end up with an invalid assignment of players to games."""
    pass

class SeedMethod(Enum):
    """
    Method to use to seed games
    RANDOM - try a number of random seedings plus modifications and pick the best
    EXHAUSTIVE - try every possible seeding and pick the best (slow)
    """
    #RANDOM = auto()
    #EXHAUSTIVE = auto()
    RANDOM = 1
    EXHAUSTIVE = 2

class GameSeeder:
    """
    Assigns Diplomacy players to games to minimise the number of people they play again.
    Two algorithms are supported:
    EXHAUSTIVE
        Try every possible seeding. This will take a long time with many players.
        It may also exhaust memory. Definitely not recommended for 28 players, and may well
        not work with 21.
    RANDOM
        Initially assigns players at random to games, then tries swapping players at random between games.
        The number of candidate seedings and the number of iterations can both be specified.
    In both cases, a fitness measure is used to determine the best candidate seeding.
    """
    def __init__(self, starts=1, iterations=1000, seed_method=SeedMethod.RANDOM):
        """
        seed_method specifies the algorithm used to find a candidate seeding:
            RANDOM - pick sets of players at random
            EXHAUSTIVE - try every possible seeding
        starts is the number of initial seedings to generate. Not used with EXHAUSTIVE seed_method.
        iterations is the number of times to modify each initial seeding in an attempt to improve it. Not used with EXHAUSTIVE seed_method.
        """
        self.games_played = False
        self.seed_method = seed_method
        if seed_method == SeedMethod.RANDOM:
            self.starts = starts
            self.iterations = iterations
        # List of players to use to seed games
        self.players = []
        # Dict, keyed by player, of dicts, keyed by (other) player, of integer counts of shared games
        self.games_played_matrix = {}

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

    def add_played_game(self, game):
        """
        Add a previously-played game to take into account.
        game is a set of 7 players (player can be any type as long as it's the same in all calls to this object).
        Can raise InvalidPlayer if any player is unknown.
        Raises InvalidPlayerCount if the games doesn't have seven players.
        """
        if len(game) != 7:
            raise InvalidPlayerCount(str(len(game)))
        for p in game:
            if p not in self.games_played_matrix:
                raise InvalidPlayer(str(p))
            for q in game:
                if p != q:
                    try:
                        self.games_played_matrix[p][q] += 1
                    except KeyError:
                        if q not in self.games_played_matrix:
                            raise InvalidPlayer(str(q))
                        self.games_played_matrix[p][q] = 1
        self.games_played = True

    def add_bias(self, player1, player2, weight):
        """
        Add a bias to take into account.
        This effectively says "treat player1 and player2 as if they have already played weight games together".
        It is intended to be used to keep pairs of players apart, e.g. family members.
        Could also be used to make pairs of players more likely to play together if weight is negative.
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
            self.games_played_matrix[player2][player1] += weight
        except KeyError:
            self.games_played_matrix[player1][player2] = weight
            self.games_played_matrix[player2][player1] = weight
        # fitness is now meaningful
        self.games_played = True

    def _fitness_score(self, game):
        """
        Returns a fitness score (0-42) for a game. Lower is better.
        The value returned is twice the number of times each pair of players has played together already.
        game is a set of 7 players (player can be any type as long as it's the same in all calls to this object).
        """
        f = 0
        # Sum the number of times each pair of players has played together already
        for p in game:
            for q in game:
                if p != q:
                    try:
                        f += self.games_played_matrix[p][q]
                    except KeyError:
                        # These players have not played each other
                        pass
        return f

    def _assign_players_to_games_randomly(self, players):
        """
        Assign all the players provided to games completely at random, with no weighting.
        Returns a list of sets of 7 players.
        len(players) must be a multiple of 7.
        Raises _AssignmentFailed if the algorithm messes up.
        """
        res = []
        game = set()
        while players:
            if (len(players)) == 7 and (len(set(players)) < 7):
                # We have just seven players left, but not seven unique players
                raise _AssignmentFailed
            # Pick a random player to add to the current game
            p = random.choice(list(players))
            if p in game:
                # This player is no good
                continue
            players.remove(p)
            game.add(p)
            if len(game) == 7:
                # Done with this game. Start a new one
                res.append(game)
                game = set()
        return res

    def _set_fitness(self, games):
        """
        Calculate a total fitness score for this list of games.
        Range is 0-(42 * len(games)). Lower is better.
        """
        fitness = 0
        for g in games:
            fitness += self._fitness_score(g)
        return fitness

    def _improve_fitness(self, games):
        """
        Try swapping random players between games to see if we can improve the overall fitness score.
        Returns the best set of games it finds and the fitness score for that set.
        """
        best_set = copy.deepcopy(games)
        best_fitness = self._set_fitness(games)
        # The more iterations, the better the result, but the longer it takes
        for t in range(self.iterations):
            # Try swapping a random player between two random games
            g1 = random.choice(games)
            g2 = random.choice(games)
            p1 = g1.pop()
            p2 = g2.pop()
            if (p1 in g2) or (p2 in g1):
                # Don't try to create games with players playing themselves
                g1.add(p1)
                g2.add(p2)
                continue
            g1.add(p2)
            g2.add(p1)
            fitness = self._set_fitness(games)
            if fitness < best_fitness:
                #print("Improving fitness from %d to %d" % (best_fitness, fitness))
                #print(games)
                best_fitness = fitness
                best_set = copy.deepcopy(games)
        return best_set, best_fitness

    def _assign_players_wrapper(self, players):
        """
        Wrapper that just keeps calling __assign_players_to_game() until it succeeds.
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
        Returns a list of all possible seedings (each being a list of sets of 7 players).
        It will also include seedings with the same games in different orders.
        Note that this will take a long time for large numbers of players.
        Raises _AssignmentFailed if no valid games can be formed from the specified players.
        """
        if len(players) % 7 != 0:
            raise InvalidPlayerCount("%d is not an exact multiple of 7" % len(players))
        if len(set(players)) < 7:
            # We've ended up with a group of players that we can't make a valid game from
            raise _AssignmentFailed
        if len(players) == 7:
            # With 7 players, there is exactly one possible game,
            # and therefore exactly one possible seeding
            return [[set(players)]]
        res = []
        # Go through all possible combinations for the first game:
        for t in itertools.combinations(players, 7):
            game = set(t)
            if len(game) != 7:
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
        Returns a list of players containing every known player and every player doubling up,
        but excluding any players in omitting_players.
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
        Returns a list of games, where each game is a set of 7 players, and the fitness score for the set.
        omitting_players is a set of previously-added players not to assign to games.
        players_doubling_up is an optional set of previously-added players to assign to two games each.
        Can raise InvalidPlayer if any player in omitting_players or players_doubling_up is unknown.
        Can raise InvalidPlayerCount if the resulting number of players isn't an exact multiple of 7.
        """
        players = self._player_pool(omitting_players, players_doubling_up)
        # Check that we have a multiple of seven players
        if len(players) % 7 != 0:
            raise InvalidPlayerCount("%d total plus %d duplicated minus %d omitted"
                                     % (len(self.games_played_matrix),
                                        len(players_doubling_up),
                                        len(omitting_players)))
        res = self._assign_players_wrapper(players)
        # There's no point iterating if all solutions have a fitness of zero
        if self.games_played:
            res, fitness = self._improve_fitness(res)
        else:
            fitness = 0
        # Return the resulting list of games
        return res, fitness

    def seed_games(self, omitting_players=set(), players_doubling_up=set()):
        """
        Returns a list of games, where each game is a set of 7 players.
        omitting_players is an optional set of previously-added players not to assign to games.
        players_doubling_up is an optional set of previously-added players to assign to two games each.
        Internally, this will generate the number of sets specified when the class was instantiated,
        and return the best one.
        Can raise InvalidPlayer if any player in omitting_players is unknown.
        Can raise InvalidPlayerCount if the resulting number of players isn't an exact multiple of 7.
        """
        # Generate the specified number of seedings
        # Use the random method if no games have been played yet, because any seeding is fine
        if (not self.games_played) or (self.seed_method == SeedMethod.RANDOM):
            seedings = []
            # No point generating multiples if they're all equally good
            starts = 1
            if self.games_played:
                starts = self.starts
            for i in range(starts):
                # This gives us a list of 2-tuples with (seeding, fitness)
                seedings.append(self._seed_games(omitting_players, players_doubling_up))
        elif self.seed_method == SeedMethod.EXHAUSTIVE:
            players = self._player_pool(omitting_players, players_doubling_up)
            seedings = []
            for s in self._all_possible_seedings(players):
                fitness = self._set_fitness(s)
                seedings.append((s, fitness))
        # Sort them by fitness
        seedings.sort(key=itemgetter(1))
        if self.seed_method == SeedMethod.RANDOM:
            bg_str = "With starts=%d and iterations=%d" % (self.starts, self.iterations)
        else:
            bg_str = "With Exhaustive seeding"
        print("%s, best fitness score is %d in %d seedings" % (bg_str,
                                                               seedings[0][1],
                                                               len(seedings)))
        # Return the best (we don't care if multiple seedings are equally good)
        return seedings[0][0]
