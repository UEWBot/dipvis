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
Assign powers to players in a Diplomacy game.
"""

import itertools
import json
import unittest
from collections import Counter
from string import ascii_uppercase
from unittest import mock

from django.test import override_settings

from tournament.game_seeder import (GameSeeder, ImpossibleToSeed,
                                    InvalidPlayer, InvalidPlayerCount,
                                    InvalidPlayerPairing, InvalidWeight,
                                    PowersNotUnique, SeedMethod,
                                    _AssignmentFailed)

# Seed the random number generator so that results are repeatable
RANDOM_SEED = 0


class GameSeederSetupTest(unittest.TestCase):
    """
    Validate the setup of GameSeeder - adding players, games, etc.
    """

    # Our players will be strings (names)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.powers = ['1', '2', '3', '4', '5', '6', '7']

    # add_player()
    def test_add_player_twice(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_player, 'A')

    # add_played_game()
    def test_add_played_game(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            seeder.add_player(p)
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})

    def test_add_played_game_invalid_player1(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F']:
            seeder.add_player(p)
        self.assertRaises(InvalidPlayer,
                          seeder.add_played_game,
                          {('G', '1'),
                           ('H', '2'),
                           ('I', '3'),
                           ('J', '4'),
                           ('K', '5'),
                           ('L', '6'),
                           ('M', '7')})

    def test_add_played_game_invalid_player2(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F']:
            seeder.add_player(p)
        self.assertRaises(InvalidPlayer,
                          seeder.add_played_game,
                          {('A', '1'),
                           ('B', '2'),
                           ('C', '3'),
                           ('D', '4'),
                           ('E', '5'),
                           ('F', '6'),
                           ('G', '7')})

    def test_add_played_game_player_too_few_players(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F']:
            seeder.add_player(p)
        self.assertRaises(InvalidPlayerCount,
                          seeder.add_played_game,
                          {('A', '1'),
                           ('B', '2'),
                           ('C', '3'),
                           ('D', '4'),
                           ('E', '5'),
                           ('F', '6')})

    def test_add_played_game_player_too_many_players(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            seeder.add_player(p)
        self.assertRaises(InvalidPlayerCount,
                          seeder.add_played_game,
                          {('A', '1'),
                           ('B', '2'),
                           ('C', '3'),
                           ('D', '4'),
                           ('E', '5'),
                           ('F', '6'),
                           ('G', '7'),
                           ('H', '1')})

    def test_add_played_game_bad_powers(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        self.assertRaises(PowersNotUnique,
                          seeder.add_played_game,
                          {('A', '1'),
                           ('B', '2'),
                           ('C', '3'),
                           ('D', '4'),
                           ('E', '2'),
                           ('F', '6'),
                           ('G', '7')})

    # _add_bias()
    def test_add_bias_invalid_weight(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B']:
            seeder.add_player(p)
        self.assertRaises(InvalidWeight, seeder._add_bias, 'A', 'B', 0)

    def test_add_bias_same_player(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayerPairing, seeder.add_bias, 'A', 'A')

    def test_add_bias_unknown_player1(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_bias, 'B', 'A')

    def test_add_bias_unknown_player2(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_bias, 'A', 'B')

    def test_add_bias_twice(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B']:
            seeder.add_player(p)
        seeder.add_bias('A', 'B')
        seeder.add_bias('B', 'A')
        # Result should be the sum
        self.assertEqual(seeder.games_played_matrix['A']['B'],
                         2 * seeder._BIAS_WEIGHT)

    def test_add_bias(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']:
            seeder.add_player(p)
        seeder.add_bias('A', 'B')
        # That should suffice to keep those players apart
        r = seeder.seed_games()
        for g in r:
            if 'A' in g:
                self.assertNotIn('B', g)
            if 'B' in g:
                self.assertNotIn('A', g)

    def test_add_bias_fitness(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        seeder.add_bias('A', 'B')
        self.assertEqual(2 * seeder._BIAS_WEIGHT ** 2,
                         seeder._fitness_score({'A', 'B', 'C', 'D', 'E', 'F', 'G'}))

    # _power_fitness()
    def test_power_fitness_no_games(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        self.assertEqual(0, seeder._power_fitness({('A', '1'),
                                                   ('B', '2'),
                                                   ('C', '3'),
                                                   ('D', '4'),
                                                   ('E', '5'),
                                                   ('F', '6'),
                                                   ('G', '7')}))

    def test_power_fitness_exact_match(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})
        self.assertEqual(7, seeder._power_fitness({('A', '1'),
                                                   ('B', '2'),
                                                   ('C', '3'),
                                                   ('D', '4'),
                                                   ('E', '5'),
                                                   ('F', '6'),
                                                   ('G', '7')}))

    # _assign_some_powers()
    def test_assign_some_powers(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        games = seeder._assign_some_powers(['A', 'B', 'C', 'D', 'E', 'F', 'G'],
                                           self.powers)
        self.assertEqual(len(games), 7*6*5*4*3*2)
        # Ideally, we'd also check for duplicate seedings

    # _assign_powers()
    def test_assign_powers(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        # Add games so that every player has played six powers once each,
        # leaving just one ideal game where they each play the unplayed power
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})
        seeder.add_played_game({('A', '2'),
                                ('B', '3'),
                                ('C', '4'),
                                ('D', '5'),
                                ('E', '6'),
                                ('F', '7'),
                                ('G', '1')})
        seeder.add_played_game({('A', '3'),
                                ('B', '4'),
                                ('C', '5'),
                                ('D', '6'),
                                ('E', '7'),
                                ('F', '1'),
                                ('G', '2')})
        seeder.add_played_game({('A', '4'),
                                ('B', '5'),
                                ('C', '6'),
                                ('D', '7'),
                                ('E', '1'),
                                ('F', '2'),
                                ('G', '3')})
        seeder.add_played_game({('A', '5'),
                                ('B', '6'),
                                ('C', '7'),
                                ('D', '1'),
                                ('E', '2'),
                                ('F', '3'),
                                ('G', '4')})
        seeder.add_played_game({('A', '6'),
                                ('B', '7'),
                                ('C', '1'),
                                ('D', '2'),
                                ('E', '3'),
                                ('F', '4'),
                                ('G', '5')})
        game, issues = seeder._assign_powers({'A', 'B', 'C', 'D', 'E', 'F', 'G'})
        self.assertIn(('A', '7'), game)
        self.assertIn(('B', '1'), game)
        self.assertIn(('C', '2'), game)
        self.assertIn(('D', '3'), game)
        self.assertIn(('E', '4'), game)
        self.assertIn(('F', '5'), game)
        self.assertIn(('G', '6'), game)
        self.assertEqual(0, len(issues))

    # _fitness_score()
    def test_fitness_score_no_games(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        self.assertEqual(0, seeder._fitness_score({'A', 'B', 'C', 'D', 'E', 'F', 'G'}))

    def test_fitness_score_one_pair_played(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']:
            seeder.add_player(p)
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})
        self.assertEqual(2, seeder._fitness_score({'A', 'B', 'H', 'I', 'J', 'K', 'L'}))

    def test_fitness_score_worst_case(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})
        self.assertEqual(42, seeder._fitness_score({'A', 'B', 'C', 'D', 'E', 'F', 'G'}))

    def test_fitness_score_two_pairs(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q']:
            seeder.add_player(p)
        # Two previous non-overlapping games
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})
        seeder.add_played_game({('H', '1'),
                                ('I', '2'),
                                ('J', '3'),
                                ('K', '4'),
                                ('L', '5'),
                                ('M', '6'),
                                ('N', '7')})
        # Game with two pairs from each earlier game
        game = {'A', 'B', 'M', 'N', 'O', 'P', 'Q'}
        self.assertEqual(4, seeder._fitness_score(game))

    def test_fitness_score_one_triple(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']:
            seeder.add_player(p)
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})
        # Game with two pairs from each earlier game
        game = {'A', 'C', 'D', 'H', 'I', 'J', 'K'}
        self.assertEqual(6, seeder._fitness_score(game))

    def test_fitness_score_third_round(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q']:
            seeder.add_player(p)
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('H', '3'),
                                ('I', '4'),
                                ('J', '5'),
                                ('K', '6'),
                                ('L', '7')})
        game = {'A', 'B', 'M', 'N', 'O', 'P', 'Q'}
        self.assertEqual(8, seeder._fitness_score(game))

    # seed_games() errors
    def test_seed_games_exhaustive_bad_count(self):
        """Exhaustive seeding with only 6 players in the second round"""
        seeder = GameSeeder(self.powers,
                            SeedMethod.EXHAUSTIVE,
                            random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})
        self.assertRaises(InvalidPlayerCount, seeder.seed_games, {'E'})

    def test_seed_games_doubler_not_playing(self):
        seeder = GameSeeder(self.powers,
                            SeedMethod.EXHAUSTIVE,
                            random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        self.assertRaises(ImpossibleToSeed, seeder.seed_games, {'E'}, {'E'})

    def test_seed_games_impossible(self):
        """
        6 players, with one playing two games

        So we have 7 players, but still can't form a valid game
        """
        seeder = GameSeeder(self.powers,
                            SeedMethod.EXHAUSTIVE,
                            random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F']:
            seeder.add_player(p)
        self.assertRaises(ImpossibleToSeed, seeder.seed_games, set(), {'E'})

    def test_seed_games_impossible_round_2(self):
        """
        7 players, with one playing two games and one sitting out

        So we have 7 players, but still can't form a valid game
        """
        seeder = GameSeeder(self.powers,
                            SeedMethod.EXHAUSTIVE,
                            random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})
        self.assertRaises(ImpossibleToSeed, seeder.seed_games, {'E'}, {'B'})

    # seed_games_and_powers() issues
    def test_seed_games_and_powers_issues(self):
        """Check that the issues list is properly populated"""
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})
        seeder.add_played_game({('A', '2'),
                                ('B', '3'),
                                ('C', '4'),
                                ('D', '5'),
                                ('E', '6'),
                                ('F', '7'),
                                ('G', '1')})
        seeder.add_played_game({('A', '3'),
                                ('B', '4'),
                                ('C', '5'),
                                ('D', '6'),
                                ('E', '7'),
                                ('F', '1'),
                                ('G', '2')})
        seeder.add_played_game({('A', '4'),
                                ('B', '5'),
                                ('C', '6'),
                                ('D', '7'),
                                ('E', '1'),
                                ('F', '2'),
                                ('G', '3')})
        seeder.add_played_game({('A', '5'),
                                ('B', '6'),
                                ('C', '7'),
                                ('D', '1'),
                                ('E', '2'),
                                ('F', '3'),
                                ('G', '4')})
        seeder.add_played_game({('A', '6'),
                                ('B', '7'),
                                ('C', '1'),
                                ('D', '2'),
                                ('E', '3'),
                                ('F', '4'),
                                ('G', '5')})
        # Note that two of these are powers they have already played
        seeder.add_played_game({('A', '1'),
                                ('B', '7'),
                                ('C', '2'),
                                ('D', '3'),
                                ('E', '4'),
                                ('F', '5'),
                                ('G', '6')})
        r = seeder.seed_games_and_powers()
        self.assertEqual(1, len(r))
        g, i = r[0]
        self.assertEqual(1, len(i))
        self.assertIn('5 player', i[0])

    # TODO more tests of seed_games_and_powers() power assignment


def with_powers(game):
    """Convert a set of seven players to a set of seven (player, power) 2-tuples"""
    return set(zip(sorted(game), ['1', '2', '3', '4', '5', '6', '7']))


class _GameSetAssertionsMixin:
    """Shared helpers for validating seeded games."""

    def check_game(self, game):
        # Game should have exactly 7 players
        self.assertEqual(len(game), 7)
        # Games should always be sets (and hence have no duplicate players)
        self.assertIsInstance(game, set)

    def check_game_set(self, game_set, players, omissions=None, duplicates=None):
        if omissions is None:
            omissions = set()
        if duplicates is None:
            duplicates = set()
        game_count = len(game_set)
        self.assertEqual(game_count, players // 7)
        # Every game should be valid by itself
        for g in game_set:
            self.check_game(g)
        # Each player should be present exactly once, except for duplicates
        unique_players = set()
        for g in game_set:
            unique_players |= g
        self.assertEqual(len(unique_players) + len(duplicates), 7 * game_count, "One or more players is playing multiple games")
        # No omitted players should be present
        self.assertEqual(len(unique_players & omissions), 0, "One or more omitted players is in a game")
        # Duplicate players should be playing exactly two games
        for p in duplicates:
            count = 0
            for g in game_set:
                if p in g:
                    count += 1
            self.assertEqual(count, 2, f'Player {p} should be playing 2 games but is actually playing {count}')

    def check_no_games_played(self, seeder):
        for p1 in seeder.games_played_matrix.values():
            for p2 in p1.values():
                self.assertEqual(p2, 0)


class _SharedSeederAlgorithmCasesMixin:
    """
    Shared seeding test cases that should pass for all algorithms.

    No more than 2 boards per round.
    """

    seed_method = None

    def test_seed_games_no_players(self):
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                            self.seed_method,
                            random_seed=RANDOM_SEED)
        games = seeder.seed_games()
        self.assertEqual(len(games), 0)

    def _create_method_seeder(self, num_players, starts=1, iterations=1000):
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                            seed_method=self.seed_method,
                            starts=starts,
                            iterations=iterations,
                            random_seed=RANDOM_SEED)
        for i in range(num_players):
            seeder.add_player(f'{i}p')
        return seeder

    def expected_second_round_single_doubler_fitness(self):
        """Override in subclasses that can assert an exact second-round fitness."""
        return None

    def test_shared_seed_games_initial(self):
        seeder = self._create_method_seeder(num_players=14)
        games = seeder.seed_games()
        self.check_game_set(games, 14)

    def test_shared_seed_games_second_round(self):
        seeder = self._create_method_seeder(num_players=14)
        first_round = seeder.seed_games()
        for g in first_round:
            seeder.add_played_game(with_powers(g))
        second_round = seeder.seed_games()
        self.check_game_set(second_round, 14)

    def test_shared_seed_games_wrong_count(self):
        seeder = self._create_method_seeder(num_players=13)
        self.assertRaises(InvalidPlayerCount, seeder.seed_games)

    def test_shared_seed_games_wrong_count_with_omission(self):
        seeder = self._create_method_seeder(num_players=14)
        self.assertRaises(InvalidPlayerCount, seeder.seed_games, {'0p'})

    def test_shared_seed_games_wrong_count_with_single_doubler(self):
        seeder = self._create_method_seeder(num_players=14)
        self.assertRaises(InvalidPlayerCount, seeder.seed_games, set(), {'0p'})

    def test_shared_seed_games_wrong_count_with_two_doublers(self):
        seeder = self._create_method_seeder(num_players=14)
        self.assertRaises(InvalidPlayerCount, seeder.seed_games, set(), {'0p', '1p'})
        self.check_no_games_played(seeder)

    def test_shared_seed_games_with_omission(self):
        seeder = self._create_method_seeder(num_players=15)
        omit = {'14p'}
        games = seeder.seed_games(omitting_players=omit)
        self.check_game_set(games, 14, omissions=omit)

    def test_shared_seed_games_invalid_dup(self):
        seeder = self._create_method_seeder(num_players=14)
        self.assertRaises(InvalidPlayer, seeder.seed_games, players_doubling_up={'X'})

    def test_shared_seed_games_invalid_sit(self):
        seeder = self._create_method_seeder(num_players=14)
        self.assertRaises(InvalidPlayer, seeder.seed_games, omitting_players={'X'})

    def test_shared_seed_games_with_single_doubler(self):
        seeder = self._create_method_seeder(num_players=13)
        first_dup = '2p'
        games = seeder.seed_games(players_doubling_up={first_dup})
        self.check_game_set(games, 14, duplicates={first_dup})

        first_round_fitness = seeder._set_fitness(games)
        self.assertGreaterEqual(first_round_fitness, 0)

        for g in games:
            seeder.add_played_game(with_powers(g))

        second_dup = '3p'
        games = seeder.seed_games(players_doubling_up={second_dup})
        self.check_game_set(games, 14, duplicates={second_dup})

        second_round_fitness = seeder._set_fitness(games)
        self.assertGreaterEqual(second_round_fitness, 0)
        expected = self.expected_second_round_single_doubler_fitness()
        if expected is not None:
            self.assertEqual(second_round_fitness, expected)

class _SharedRandomBoardSeederCasesMixin:
    """Shared larger-scale behavior tests for RANDOM and BOARD methods."""

    def assert_second_round_21_fitness(self, fitness):
        """Override for algorithm-specific quality assertion on 21-player round 2."""
        self.assertLessEqual(fitness, 30)

    def bigger_tournament_cases(self):
        return [(1, 1000), (100, 100), (1000, 1)]

    def assert_bigger_tournament_second_round_fitness(self, fitness):
        """Override for algorithm-specific quality assertion on 49-player round 2."""
        self.assertLess(fitness, 24)

    def _seed_bigger_tournament(self, starts, iterations):
        """Two rounds of a 49-player tournament."""
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                            starts=starts,
                            iterations=iterations,
                            seed_method=self.seed_method,
                            random_seed=RANDOM_SEED)
        for i in range(49):
            seeder.add_player(f'{i}p')
        games = seeder.seed_games()
        self.check_game_set(games, 49)
        self.assertEqual(seeder._set_fitness(games), 0)
        for g in games:
            seeder.add_played_game(with_powers(g))
        games = seeder.seed_games()
        self.check_game_set(games, 49)
        self.assert_bigger_tournament_second_round_fitness(seeder._set_fitness(games))

    def test_seed_games_second_round(self):
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                            seed_method=self.seed_method,
                            random_seed=RANDOM_SEED)
        for p in ascii_uppercase[:21]:
            seeder.add_player(p)
        # Add some previously-played games.
        seeder.add_played_game({('A', '1'),
                                ('B', '2'),
                                ('C', '3'),
                                ('D', '4'),
                                ('E', '5'),
                                ('F', '6'),
                                ('G', '7')})
        seeder.add_played_game({('H', '1'),
                                ('I', '2'),
                                ('J', '3'),
                                ('K', '4'),
                                ('L', '5'),
                                ('M', '6'),
                                ('N', '7')})
        seeder.add_played_game({('O', '1'),
                                ('P', '2'),
                                ('Q', '3'),
                                ('R', '4'),
                                ('S', '5'),
                                ('T', '6'),
                                ('U', '7')})
        games = seeder.seed_games()
        self.check_game_set(games, 21)
        self.assert_second_round_21_fitness(seeder._set_fitness(games))

    def test_seed_games_bigger_tournament(self):
        for starts, iterations in self.bigger_tournament_cases():
            with self.subTest(starts=starts, iterations=iterations):
                self._seed_bigger_tournament(starts, iterations)

    def test_seed_games_separate_dups_1(self):
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                            seed_method=self.seed_method,
                            random_seed=RANDOM_SEED)
        for p in ascii_uppercase[:26]:
            seeder.add_player(p)
        dups = {'A', 'B'}
        games = seeder.seed_games(players_doubling_up=dups)
        self.check_game_set(games, 28, duplicates=dups)
        for g in games:
            self.assertNotEqual('A' in g, 'B' in g)
        self.check_no_games_played(seeder)

    def test_seed_games_separate_dups_2(self):
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                            seed_method=self.seed_method,
                            random_seed=RANDOM_SEED)
        for p in ascii_uppercase[:18]:
            seeder.add_player(p)
        dups = {'A', 'B', 'C'}
        games = seeder.seed_games(players_doubling_up=dups)
        self.check_game_set(games, 21, duplicates=dups)
        for g in games:
            if ('A' in g) and ('B' in g):
                self.assertNotIn('C', g)
        self.check_no_games_played(seeder)

    def test_seed_games_three_rounds_rotating_omissions(self):
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                            seed_method=self.seed_method,
                            random_seed=RANDOM_SEED)
        for i in range(25):
            seeder.add_player(f'{i}p')

        all_players = {f'{i}p' for i in range(25)}
        rotating_omissions = [
            {'21p', '22p', '23p', '24p'},
            {'17p', '18p', '19p', '20p'},
            {'13p', '14p', '15p', '16p'},
        ]

        round_player_sets = []
        for omitted in rotating_omissions:
            games = seeder.seed_games(omitting_players=omitted)
            self.check_game_set(games, 21, omissions=omitted)

            playing = set()
            for game in games:
                playing |= game
            self.assertEqual(playing, all_players - omitted)
            round_player_sets.append(frozenset(playing))

            for game in games:
                seeder.add_played_game(with_powers(game))

        self.assertEqual(len(set(round_player_sets)), 3)


class RandomGameSeederTest(_SharedRandomBoardSeederCasesMixin,
                           _SharedSeederAlgorithmCasesMixin,
                           _GameSetAssertionsMixin,
                           unittest.TestCase):
    """
    Validate a random GameSeeder seeding games
    """

    # Our players will be strings (names)

    seed_method = SeedMethod.RANDOM

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def assert_second_round_21_fitness(self, fitness):
        # Random should hit the known optimum for this 21-player constructed case.
        self.assertEqual(fitness, 30)


class ExhaustiveGameSeederTest(_SharedSeederAlgorithmCasesMixin,
                               _GameSetAssertionsMixin,
                               unittest.TestCase):
    """
    Validate an exhaustive GameSeeder seeding games
    """

    # Our players will be strings (names)

    seed_method = SeedMethod.EXHAUSTIVE

    def expected_second_round_single_doubler_fitness(self):
        return 42

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_exhaustive_seeding(self):
        players = [(7, 42), (14, 36)]
        for count, fitness in players:
            with self.subTest(player_count=count):
                seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                                    seed_method=self.seed_method,
                                    random_seed=RANDOM_SEED)
                for i in range(count):
                    seeder.add_player(f'{i}p')
                r = seeder.seed_games()
                self.check_game_set(r, count)
                # First round by definition should have a fitness of zero
                self.assertEqual(seeder._set_fitness(r), 0)
                # Add the first round games as played
                for g in r:
                    seeder.add_played_game(with_powers(g))
                r = seeder.seed_games()
                self.check_game_set(r, count)
                # Check that game_set has the expected fitness score
                self.assertEqual(seeder._set_fitness(r), fitness)

    def _seeder_with_players(self, count):
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                            seed_method=self.seed_method,
                            random_seed=RANDOM_SEED)
        for i in range(count):
            seeder.add_player(f'{i}p')
        return seeder

    def test_too_many_players(self):
        seeder = self._seeder_with_players(21)
        with self.assertRaises(InvalidPlayerCount):
            seeder.seed_games()

    def test_too_many_players_with_doublers(self):
        seeder = self._seeder_with_players(14)
        with self.assertRaises(InvalidPlayerCount):
            seeder.seed_games(omitting_players={'0p'},
                              players_doubling_up={'1p', '2p', '3p', '4p', '5p', '6p', '7p', '8p'})

    @override_settings(GAME_SEEDER_MAX_EXHAUSTIVE_PLAYERS=7)
    def test_max_players_lowered(self):
        seeder = self._seeder_with_players(14)
        with self.assertRaises(InvalidPlayerCount):
            seeder.seed_games()
        self.check_game_set(seeder.seed_games(omitting_players={f'{i}p' for i in range(7)}), 7)

    @override_settings(GAME_SEEDER_MAX_EXHAUSTIVE_PLAYERS=21)
    def test_max_players_raised(self):
        # Before any games are played, seeding is random, so 21 is cheap
        self.check_game_set(self._seeder_with_players(21).seed_games(), 21)


class BoardGameSeederTest(_SharedSeederAlgorithmCasesMixin,
                          _SharedRandomBoardSeederCasesMixin,
                          _GameSetAssertionsMixin,
                          unittest.TestCase):
    """Validate board-based seeding."""

    seed_method = SeedMethod.BOARD

    def test_doubler_never_left_without_a_board(self):
        """Random seed 30 used to leave both copies of 3p needing the same board"""
        for seed in range(50):
            with self.subTest(random_seed=seed):
                seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                                    self.seed_method,
                                    random_seed=seed)
                for i in range(13):
                    seeder.add_player(f'{i}p')
                for rnd in range(3):
                    doubler = f'{rnd + 2}p'
                    r = seeder.seed_games(players_doubling_up={doubler})
                    self.check_game_set(r, 14, duplicates={doubler})
                    for g in r:
                        seeder.add_played_game(with_powers(g))


class DoublerPairingTest(unittest.TestCase):
    """Players doubling up shouldn't be put together on both their boards."""

    powers = ['1', '2', '3', '4', '5', '6', '7']
    doublers = ['A', 'B', 'C', 'D']

    def _seeder(self, random_seed=RANDOM_SEED):
        """24 players, where only some pairs of doublers have met before"""
        seeder = GameSeeder(self.powers, SeedMethod.BOARD, random_seed=random_seed)
        for p in self.doublers + [f'{i}p' for i in range(20)]:
            seeder.add_player(p)
        # A/D and B/C have never met, but the other doubler pairs except B/D have
        seeder._add_bias('A', 'B', 1)
        seeder._add_bias('A', 'C', 1)
        seeder._add_bias('C', 'D', 2)
        return seeder

    def _boards(self, doubler_pairs):
        """Four boards, each with the specified pair of doublers and five others"""
        others = [f'{i}p' for i in range(20)]
        return [set(pair) | set(others[5 * i:5 * i + 5]) for i, pair in enumerate(doubler_pairs)]

    def _repeated_pairs(self, games):
        meetings = Counter()
        for g in games:
            meetings.update(itertools.combinations(sorted(set(g) & set(self.doublers)), 2))
        return [pair for pair, n in meetings.items() if n > 1]

    def test_repeat_meeting_costs_more(self):
        """Two pairs meeting twice should score worse than meeting a previous opponent"""
        seeder = self._seeder()
        seeder._add_bias_for_doublers(self.doublers, add=True)
        repeated = self._boards([('A', 'D'), ('A', 'D'), ('B', 'C'), ('B', 'C')])
        # Each doubler meets two others once, including A who has met C before
        cycle = self._boards([('A', 'D'), ('D', 'B'), ('B', 'C'), ('C', 'A')])
        self.assertLess(seeder._set_fitness(cycle, include_these_games=True),
                        seeder._set_fitness(repeated, include_these_games=True))

    def test_board_seeding_avoids_repeated_pairs(self):
        for seed in range(5):
            with self.subTest(random_seed=seed):
                games = self._seeder(seed).seed_games(players_doubling_up=set(self.doublers))
                self.assertEqual(self._repeated_pairs(games), [])


class GameSeederStateTest(unittest.TestCase):
    """Validate recording a seeder's state, and replaying it to reproduce problems."""

    powers = ['1', '2', '3', '4', '5', '6', '7']

    def _round_trip(self, seeder):
        """The state, as it would be after being reported as JSON"""
        return json.loads(json.dumps(seeder.state()))

    def _note(self, exc):
        """The text added to an exception to report the seeder state"""
        return exc.__notes__[-1]

    def test_replay_reproduces_seeding(self):
        for method in SeedMethod:
            with self.subTest(method=method.name):
                seeder = GameSeeder(self.powers, method, starts=3, iterations=100, random_seed=RANDOM_SEED)
                # EXHAUSTIVE builds every possible seeding, so keep to 14 players per round
                for i in range(14):
                    seeder.add_player(f'{i}p')
                seeder.add_bias('0p', '1p')
                for g in seeder.seed_games(omitting_players={'13p'}, players_doubling_up={'0p'}):
                    seeder.add_played_game(with_powers(g))
                result = seeder.seed_games_and_powers(omitting_players={'12p'}, players_doubling_up={'5p'})
                self.assertEqual(GameSeeder.replay(self._round_trip(seeder)), result)

    def test_impossible_to_seed_can_be_reproduced(self):
        """A board seeding failure can be reproduced"""
        seeder = GameSeeder(self.powers, SeedMethod.BOARD, random_seed=RANDOM_SEED)
        for i in range(13):
            seeder.add_player(f'{i}p')
        for g in seeder.seed_games(players_doubling_up={'2p'}):
            seeder.add_played_game(with_powers(g))
        with mock.patch.object(GameSeeder, '_board_seed_games_once', side_effect=_AssignmentFailed):
            with self.assertRaises(ImpossibleToSeed) as cm:
                seeder.seed_games(players_doubling_up={'3p'})
            state = cm.exception.seeder_state
            self.assertEqual(state, seeder.state())
            # The state should be reported in the exception
            note = self._note(cm.exception)
            self.assertIn('GameSeeder.replay()', note)
            self.assertEqual(json.loads(note.split('\n', 1)[1]), state)
            # and replaying it should fail in the same way
            with self.assertRaises(ImpossibleToSeed):
                GameSeeder.replay(json.loads(json.dumps(state)))

    def test_too_few_unique_players_includes_state(self):
        """Valid arguments that can't be seeded should report the state"""
        seeder = GameSeeder(self.powers, SeedMethod.EXHAUSTIVE, random_seed=RANDOM_SEED)
        for p in ['A', 'B', 'C', 'D', 'E', 'F']:
            seeder.add_player(p)
        with self.assertRaises(ImpossibleToSeed) as cm:
            seeder.seed_games(players_doubling_up={'E'})
        self.assertEqual(cm.exception.seeder_state['operations'][-1], ['seed_games', [], [4]])
        with self.assertRaises(ImpossibleToSeed):
            GameSeeder.replay(self._round_trip(seeder))

    def test_random_assignment_gives_up(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for i in range(14):
            seeder.add_player(f'{i}p')
        with mock.patch.object(seeder,
                               '_assign_players_to_games_randomly',
                               side_effect=_AssignmentFailed) as assign:
            with self.assertRaises(ImpossibleToSeed) as cm:
                seeder.seed_games()
        self.assertEqual(assign.call_count, GameSeeder._MAX_RANDOM_ATTEMPTS)
        self.assertEqual(cm.exception.seeder_state, seeder.state())

    def test_invalid_arguments_have_no_state(self):
        """Exceptions caused by invalid arguments are the caller's problem"""
        seeder = GameSeeder(self.powers, SeedMethod.BOARD, random_seed=RANDOM_SEED)
        for p in ascii_uppercase[:14]:
            seeder.add_player(p)
        cases = [(InvalidPlayer, (set(), {'X'})),
                 (InvalidPlayer, ({'X'}, set())),
                 (InvalidPlayerCount, ({'A'}, set())),
                 (ImpossibleToSeed, ({'A'}, {'A'}))]
        for exc_class, args in cases:
            with self.subTest(exception=exc_class.__name__, args=args):
                with self.assertRaises(exc_class) as cm:
                    seeder.seed_games(*args)
                self.assertFalse(hasattr(cm.exception, 'seeder_state'))
                self.assertIsNone(getattr(cm.exception, '__notes__', None))
        # The failed calls shouldn't have been recorded
        self.assertEqual({op for op, *_ in seeder.state()['operations']}, {'add_player'})

    @override_settings(GAME_SEEDER_LOG_STATE=True)
    def test_state_logged(self):
        seeder = GameSeeder(self.powers, SeedMethod.BOARD, random_seed=RANDOM_SEED)
        for i in range(14):
            seeder.add_player(f'{i}p')
        with self.assertLogs('tournament.game_seeder', 'INFO') as cm:
            games = seeder.seed_games()
        self.assertEqual(len(cm.records), 1)
        state = json.loads(cm.records[0].getMessage().split('\n', 1)[1])
        self.assertEqual(state, seeder.state())
        with self.assertLogs('tournament.game_seeder', 'INFO'):
            self.assertEqual(GameSeeder.replay(state), games)

    @override_settings(GAME_SEEDER_LOG_STATE=False)
    def test_state_not_logged(self):
        seeder = GameSeeder(self.powers, SeedMethod.BOARD, random_seed=RANDOM_SEED)
        for i in range(14):
            seeder.add_player(f'{i}p')
        with self.assertNoLogs('tournament.game_seeder'):
            seeder.seed_games()

    def test_random_seed_chosen_and_recorded(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
        self.assertIsInstance(seeder.random_seed, int)
        self.assertEqual(seeder.state()['random_seed'], seeder.random_seed)

    def test_replay_with_duplicate_names(self):
        """Players are recorded by name, so duplicate names must still be distinct players"""

        class Player:
            def __str__(self):
                return 'Same Name'

        players = [Player() for _ in range(7)]
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM, random_seed=RANDOM_SEED)
        for p in players:
            seeder.add_player(p)
        seeder.add_bias(players[0], players[1])
        seeder.seed_games()
        state = self._round_trip(seeder)
        self.assertEqual(state['players'], ['Same Name'] * 7)
        games = GameSeeder.replay(state)
        self.assertEqual(games, [{f'Same Name #{n}' for n in range(1, 8)}])
