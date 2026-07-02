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

import unittest
from string import ascii_uppercase

from tournament.game_seeder import (GameSeeder, ImpossibleToSeed,
                                    InvalidPlayer, InvalidPlayerCount,
                                    InvalidPlayerPairing, InvalidWeight,
                                    PowersNotUnique, SeedMethod)


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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_player, 'A')

    # add_played_game()
    def test_add_played_game(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
        for p in ['A', 'B']:
            seeder.add_player(p)
        self.assertRaises(InvalidWeight, seeder._add_bias, 'A', 'B', 0)

    def test_add_bias_same_player(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayerPairing, seeder.add_bias, 'A', 'A')

    def test_add_bias_unknown_player1(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_bias, 'B', 'A')

    def test_add_bias_unknown_player2(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_bias, 'A', 'B')

    def test_add_bias_twice(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
        for p in ['A', 'B']:
            seeder.add_player(p)
        seeder.add_bias('A', 'B')
        seeder.add_bias('B', 'A')
        # Result should be the sum
        self.assertEqual(seeder.games_played_matrix['A']['B'],
                         2 * seeder._BIAS_WEIGHT)

    def test_add_bias(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        seeder.add_bias('A', 'B')
        self.assertEqual(2 * seeder._BIAS_WEIGHT ** 2,
                         seeder._fitness_score({'A', 'B', 'C', 'D', 'E', 'F', 'G'}))

    # _power_fitness()
    def test_power_fitness_no_games(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        games = seeder._assign_some_powers(['A', 'B', 'C', 'D', 'E', 'F', 'G'],
                                           self.powers)
        self.assertEqual(len(games), 7*6*5*4*3*2)
        # Ideally, we'd also check for duplicate seedings

    # _assign_powers()
    def test_assign_powers(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        self.assertEqual(0, seeder._fitness_score({'A', 'B', 'C', 'D', 'E', 'F', 'G'}))

    def test_fitness_score_one_pair_played(self):
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
                            SeedMethod.EXHAUSTIVE)
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
                            SeedMethod.EXHAUSTIVE)
        for p in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            seeder.add_player(p)
        self.assertRaises(ImpossibleToSeed, seeder.seed_games, {'E'}, {'E'})

    def test_seed_games_impossible(self):
        """
        6 players, with one playing two games

        So we have 7 players, but still can't form a valid game
        """
        seeder = GameSeeder(self.powers,
                            SeedMethod.EXHAUSTIVE)
        for p in ['A', 'B', 'C', 'D', 'E', 'F']:
            seeder.add_player(p)
        self.assertRaises(ImpossibleToSeed, seeder.seed_games, set(), {'E'})

    def test_seed_games_impossible_round_2(self):
        """
        7 players, with one playing two games and one sitting out

        So we have 7 players, but still can't form a valid game
        """
        seeder = GameSeeder(self.powers,
                            SeedMethod.EXHAUSTIVE)
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
        seeder = GameSeeder(self.powers, SeedMethod.RANDOM)
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
    return set(zip(list(game), ['1', '2', '3', '4', '5', '6', '7']))


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
                            self.seed_method)
        games = seeder.seed_games()
        self.assertEqual(len(games), 0)

    def _create_method_seeder(self, num_players, starts=1, iterations=1000):
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                            seed_method=self.seed_method,
                            starts=starts,
                            iterations=iterations)
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
                            seed_method=self.seed_method)
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
                            seed_method=self.seed_method)
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
                            seed_method=self.seed_method)
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
                            seed_method=self.seed_method)
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
                            seed_method=self.seed_method)
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
    Validate the meat of GameSeeder - actually seeding games
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
                                    seed_method=self.seed_method)
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


class BoardGameSeederTest(_SharedSeederAlgorithmCasesMixin,
                          _SharedRandomBoardSeederCasesMixin,
                          _GameSetAssertionsMixin,
                          unittest.TestCase):
    """Validate board-based seeding."""

    seed_method = SeedMethod.BOARD
