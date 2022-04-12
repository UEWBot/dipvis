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

from tournament.game_seeder import GameSeeder
from tournament.game_seeder import InvalidPlayer
from tournament.game_seeder import InvalidPlayerCount
from tournament.game_seeder import InvalidPlayerPairing
from tournament.game_seeder import InvalidWeight
from tournament.game_seeder import PowersNotUnique
from tournament.game_seeder import ImpossibleToSeed
from tournament.game_seeder import SeedMethod


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
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_player, 'A')

    # add_played_game()
    def test_add_played_game(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_player('H')
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('C', '3'),
                                    ('D', '4'),
                                    ('E', '5'),
                                    ('F', '6'),
                                    ('G', '7')]))

    def test_add_played_game_invalid_player(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        self.assertRaises(InvalidPlayer,
                          seeder.add_played_game,
                          set([('A', '1'),
                               ('B', '2'),
                               ('C', '3'),
                               ('D', '4'),
                               ('E', '5'),
                               ('F', '6'),
                               ('G', '7')]))

    def test_add_played_game_player_too_few_players(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        self.assertRaises(InvalidPlayerCount,
                          seeder.add_played_game,
                          set([('A', '1'),
                               ('B', '2'),
                               ('C', '3'),
                               ('D', '4'),
                               ('E', '5'),
                               ('F', '6')]))

    def test_add_played_game_player_too_many_players(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_player('H')
        self.assertRaises(InvalidPlayerCount,
                          seeder.add_played_game,
                          set([('A', '1'),
                               ('B', '2'),
                               ('C', '3'),
                               ('D', '4'),
                               ('E', '5'),
                               ('F', '6'),
                               ('G', '7'),
                               ('H', '1')]))

    def test_add_played_game_bad_powers(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        self.assertRaises(PowersNotUnique,
                          seeder.add_played_game,
                          set([('A', '1'),
                               ('B', '2'),
                               ('C', '3'),
                               ('D', '4'),
                               ('E', '2'),
                               ('F', '6'),
                               ('G', '7')]))

    # _add_bias()
    def test_add_bias_invalid_weight(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        self.assertRaises(InvalidWeight, seeder._add_bias, 'A', 'B', 0)

    # add_bias()
    def test_add_bias_same_player(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayerPairing, seeder.add_bias, 'A', 'A')

    def test_add_bias_unknown_player1(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_bias, 'B', 'A')

    def test_add_bias_unknown_player2(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_bias, 'A', 'B')

    def test_add_bias_twice(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_bias('A', 'B')
        seeder.add_bias('B', 'A')
        # Result should be the sum
        self.assertEqual(seeder.games_played_matrix['A']['B'],
                         2 * seeder._BIAS_WEIGHT)

    def test_add_bias(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_player('H')
        seeder.add_player('I')
        seeder.add_player('J')
        seeder.add_player('K')
        seeder.add_player('L')
        seeder.add_player('M')
        seeder.add_player('N')
        seeder.add_bias('A', 'B')
        # That should suffice to keep those players apart
        r = seeder.seed_games()
        for g in r:
            if 'A' in g:
                self.assertNotIn('B', g)
            if 'B' in g:
                self.assertNotIn('A', g)

    def test_add_bias_fitness(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_bias('A', 'B')
        self.assertEqual(2 * seeder._BIAS_WEIGHT ** 2,
                         seeder._fitness_score(set(['A', 'B', 'C', 'D', 'E', 'F', 'G'])))

    # _power_fitness()
    def test_power_fitness_no_games(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        self.assertEqual(0, seeder._power_fitness(set([('A', '1'),
                                                       ('B', '2'),
                                                       ('C', '3'),
                                                       ('D', '4'),
                                                       ('E', '5'),
                                                       ('F', '6'),
                                                       ('G', '7')])))

    def test_power_fitness_exact_match(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('C', '3'),
                                    ('D', '4'),
                                    ('E', '5'),
                                    ('F', '6'),
                                    ('G', '7')]))
        self.assertEqual(7, seeder._power_fitness(set([('A', '1'),
                                                       ('B', '2'),
                                                       ('C', '3'),
                                                       ('D', '4'),
                                                       ('E', '5'),
                                                       ('F', '6'),
                                                       ('G', '7')])))

    # _assign_some_powers()
    def test_assign_some_powers(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        games = seeder._assign_some_powers(['A', 'B', 'C', 'D', 'E', 'F', 'G'],
                                           self.powers)
        self.assertEqual(len(games), 7*6*5*4*3*2)
        # Ideally, we'd also check for duplicate seedings

    # _assign_powers()
    def test_assign_powers(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        # Add games so that every player has played six powers once each,
        # leaving just one ideal game where they each play the unplayed power
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('C', '3'),
                                    ('D', '4'),
                                    ('E', '5'),
                                    ('F', '6'),
                                    ('G', '7')]))
        seeder.add_played_game(set([('A', '2'),
                                    ('B', '3'),
                                    ('C', '4'),
                                    ('D', '5'),
                                    ('E', '6'),
                                    ('F', '7'),
                                    ('G', '1')]))
        seeder.add_played_game(set([('A', '3'),
                                    ('B', '4'),
                                    ('C', '5'),
                                    ('D', '6'),
                                    ('E', '7'),
                                    ('F', '1'),
                                    ('G', '2')]))
        seeder.add_played_game(set([('A', '4'),
                                    ('B', '5'),
                                    ('C', '6'),
                                    ('D', '7'),
                                    ('E', '1'),
                                    ('F', '2'),
                                    ('G', '3')]))
        seeder.add_played_game(set([('A', '5'),
                                    ('B', '6'),
                                    ('C', '7'),
                                    ('D', '1'),
                                    ('E', '2'),
                                    ('F', '3'),
                                    ('G', '4')]))
        seeder.add_played_game(set([('A', '6'),
                                    ('B', '7'),
                                    ('C', '1'),
                                    ('D', '2'),
                                    ('E', '3'),
                                    ('F', '4'),
                                    ('G', '5')]))
        game, issues = seeder._assign_powers(set(['A', 'B', 'C', 'D', 'E', 'F', 'G']))
        self.assertTrue(('A', '7') in game)
        self.assertTrue(('B', '1') in game)
        self.assertTrue(('C', '2') in game)
        self.assertTrue(('D', '3') in game)
        self.assertTrue(('E', '4') in game)
        self.assertTrue(('F', '5') in game)
        self.assertTrue(('G', '6') in game)
        self.assertEqual(0, len(issues))

    # _fitness_score()
    def test_fitness_score_no_games(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        self.assertEqual(0, seeder._fitness_score(set(['A', 'B', 'C', 'D', 'E', 'F', 'G'])))

    def test_fitness_score_one_pair_played(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_player('H')
        seeder.add_player('I')
        seeder.add_player('J')
        seeder.add_player('K')
        seeder.add_player('L')
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('C', '3'),
                                    ('D', '4'),
                                    ('E', '5'),
                                    ('F', '6'),
                                    ('G', '7')]))
        self.assertEqual(2, seeder._fitness_score(set(['A', 'B', 'H', 'I', 'J', 'K', 'L'])))

    def test_fitness_score_worst_case(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('C', '3'),
                                    ('D', '4'),
                                    ('E', '5'),
                                    ('F', '6'),
                                    ('G', '7')]))
        self.assertEqual(42, seeder._fitness_score(set(['A', 'B', 'C', 'D', 'E', 'F', 'G'])))

    def test_fitness_score_two_pairs(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_player('H')
        seeder.add_player('I')
        seeder.add_player('J')
        seeder.add_player('K')
        seeder.add_player('L')
        seeder.add_player('M')
        seeder.add_player('N')
        seeder.add_player('O')
        seeder.add_player('P')
        seeder.add_player('Q')
        # Two previous non-overlapping games
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('C', '3'),
                                    ('D', '4'),
                                    ('E', '5'),
                                    ('F', '6'),
                                    ('G', '7')]))
        seeder.add_played_game(set([('H', '1'),
                                    ('I', '2'),
                                    ('J', '3'),
                                    ('K', '4'),
                                    ('L', '5'),
                                    ('M', '6'),
                                    ('N', '7')]))
        # Game with two pairs from each earlier game
        game = set(['A', 'B', 'M', 'N', 'O', 'P', 'Q'])
        self.assertEqual(4, seeder._fitness_score(game))

    def test_fitness_score_one_triple(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_player('H')
        seeder.add_player('I')
        seeder.add_player('J')
        seeder.add_player('K')
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('C', '3'),
                                    ('D', '4'),
                                    ('E', '5'),
                                    ('F', '6'),
                                    ('G', '7')]))
        # Game with two pairs from each earlier game
        game = set(['A', 'C', 'D', 'H', 'I', 'J', 'K'])
        self.assertEqual(6, seeder._fitness_score(game))

    def test_fitness_score_third_round(self):
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_player('H')
        seeder.add_player('I')
        seeder.add_player('J')
        seeder.add_player('K')
        seeder.add_player('L')
        seeder.add_player('M')
        seeder.add_player('N')
        seeder.add_player('O')
        seeder.add_player('P')
        seeder.add_player('Q')
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('C', '3'),
                                    ('D', '4'),
                                    ('E', '5'),
                                    ('F', '6'),
                                    ('G', '7')]))
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('H', '3'),
                                    ('I', '4'),
                                    ('J', '5'),
                                    ('K', '6'),
                                    ('L', '7')]))
        game = set(['A', 'B', 'M', 'N', 'O', 'P', 'Q'])
        self.assertEqual(8, seeder._fitness_score(game))

    # seed_games() errors
    def test_seed_games_no_players(self):
        seeder = GameSeeder(self.powers)
        games = seeder.seed_games()
        self.assertEqual(len(games), 0)

    def test_seed_games_exhaustive_bad_count(self):
        # Exhaustive seeding with only 6 players in the second round
        seeder = GameSeeder(self.powers,
                            seed_method=SeedMethod.EXHAUSTIVE)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('C', '3'),
                                    ('D', '4'),
                                    ('E', '5'),
                                    ('F', '6'),
                                    ('G', '7')]))
        self.assertRaises(InvalidPlayerCount, seeder.seed_games, set(['E']))

    def test_seed_games_impossible(self):
        # 6 players, with one playing two games
        # So we have 7 players, but still can't form a valid game
        seeder = GameSeeder(self.powers,
                            seed_method=SeedMethod.EXHAUSTIVE)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        self.assertRaises(ImpossibleToSeed, seeder.seed_games, set(), set(['E']))

    def test_seed_games_impossible_round_2(self):
        # 7 players, with one playing two games and one sitting out
        # So we have 7 players, but still can't form a valid game
        seeder = GameSeeder(self.powers,
                            seed_method=SeedMethod.EXHAUSTIVE)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('C', '3'),
                                    ('D', '4'),
                                    ('E', '5'),
                                    ('F', '6'),
                                    ('G', '7')]))
        self.assertRaises(ImpossibleToSeed, seeder.seed_games, set(['E']), set(['B']))

    # seed_games_and_powers() issues
    def test_seed_games_and_powers_issues(self):
        # Check that the issues list is properly populated
        seeder = GameSeeder(self.powers)
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '2'),
                                    ('C', '3'),
                                    ('D', '4'),
                                    ('E', '5'),
                                    ('F', '6'),
                                    ('G', '7')]))
        seeder.add_played_game(set([('A', '2'),
                                    ('B', '3'),
                                    ('C', '4'),
                                    ('D', '5'),
                                    ('E', '6'),
                                    ('F', '7'),
                                    ('G', '1')]))
        seeder.add_played_game(set([('A', '3'),
                                    ('B', '4'),
                                    ('C', '5'),
                                    ('D', '6'),
                                    ('E', '7'),
                                    ('F', '1'),
                                    ('G', '2')]))
        seeder.add_played_game(set([('A', '4'),
                                    ('B', '5'),
                                    ('C', '6'),
                                    ('D', '7'),
                                    ('E', '1'),
                                    ('F', '2'),
                                    ('G', '3')]))
        seeder.add_played_game(set([('A', '5'),
                                    ('B', '6'),
                                    ('C', '7'),
                                    ('D', '1'),
                                    ('E', '2'),
                                    ('F', '3'),
                                    ('G', '4')]))
        seeder.add_played_game(set([('A', '6'),
                                    ('B', '7'),
                                    ('C', '1'),
                                    ('D', '2'),
                                    ('E', '3'),
                                    ('F', '4'),
                                    ('G', '5')]))
        # Note that two of these are powers they have already played
        seeder.add_played_game(set([('A', '1'),
                                    ('B', '7'),
                                    ('C', '2'),
                                    ('D', '3'),
                                    ('E', '4'),
                                    ('F', '5'),
                                    ('G', '6')]))
        r = seeder.seed_games_and_powers()
        self.assertEqual(1, len(r))
        g, i = r[0]
        self.assertEqual(1, len(i))
        self.assertIn('5 player', i[0])

    # TODO more tests of seed_games_and_powers() power assignment

def create_seeder(starts=1, iterations=1000, num_players=20):
    # As there's no way to remove players, we'll re-create the seeder in each test
    seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'], starts, iterations)
    # Add players
    # Note that the upper limit for num_players is 26
    for p in range(num_players):
        seeder.add_player(ascii_uppercase[p])
    return seeder

def with_powers(game):
    # Convert a set of seven players to a set of seven (player, power) 2-tuples
    return set(zip(list(game), ['1', '2', '3', '4', '5', '6', '7']))


class GameSeederSeedingTest(unittest.TestCase):
    """
    Validate the meat of GameSeeder - actually seeding games
    """

    # Our players will be strings (names)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def check_game(self, game):
        # Game should have exactly 7 players
        self.assertEqual(len(game), 7)
        # Games should always be sets (and hence have no duplicate players)
        self.assertTrue(isinstance(game, set))

    def check_game_set(self, game_set, players, omissions=set(), duplicates=set()):
        game_count = len(game_set)
        self.assertEqual(game_count, players / 7)
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
            self.assertEqual(count, 2, "Player %s should be playing 2 games but is actually playing %d" % (p, count))

    def check_no_games_played(self, seeder):
        for p1 in seeder.games_played_matrix.values():
            for p2 in p1.values():
                self.assertEqual(p2, 0)

    # seed_games()
    def test_seed_games_initial(self):
        s = create_seeder(num_players=21)
        r = s.seed_games()
        self.check_game_set(r, 21)

    def test_seed_games_second_round(self):
        s = create_seeder(num_players=21)
        # Add some previously-played games
        s.add_played_game(set([('A', '1'),
                               ('B', '2'),
                               ('C', '3'),
                               ('D', '4'),
                               ('E', '5'),
                               ('F', '6'),
                               ('G', '7')]))
        s.add_played_game(set([('H', '1'),
                               ('I', '2'),
                               ('J', '3'),
                               ('K', '4'),
                               ('L', '5'),
                               ('M', '6'),
                               ('N', '7')]))
        s.add_played_game(set([('O', '1'),
                               ('P', '2'),
                               ('Q', '3'),
                               ('R', '4'),
                               ('S', '5'),
                               ('T', '6'),
                               ('U', '7')]))
        r = s.seed_games()
        self.check_game_set(r, 21)
        # Check that game_set has a "good" fitness score
        # With 21 players, we should end up with games with 2 pairs and a triplet,
        # which gives each game a fitness of 2+2+6=10, and the set a fitness of 10*3=30
        self.assertEqual(s._set_fitness(r), 30)

    def seed_bigger_tournament(self, starts, iterations):
        # Two rounds of a 49-player tournament
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'], starts, iterations)
        for i in range(49):
            seeder.add_player('%dp' % i)
        r = seeder.seed_games()
        self.check_game_set(r, 49)
        # First round by definition should have a fitness of zero
        self.assertEqual(seeder._set_fitness(r), 0)
        # Add the first round games as played
        for g in r:
            seeder.add_played_game(with_powers(g))
        r = seeder.seed_games()
        self.check_game_set(r, 49)
        # Check that game_set has a "good" fitness score
        # TODO What number works here?
        # With 49 players, there is a solution with a fitness of zero.
        # In practice, with 1000 iterations I see 14..22
        # In practice, with 10000 iterations I see 12..16
        self.assertTrue(seeder._set_fitness(r) < 24)
        print(seeder._set_fitness(r))

    def test_seed_games_bigger_tournament(self):
        the_cases = [(1, 1000), (100, 100), (1000, 1)]
        for (starts, iterations) in the_cases:
            with self.subTest(starts=starts, iterations=iterations):
                self.seed_bigger_tournament(starts, iterations)

    def test_seed_games_wrong_number_of_players(self):
        # Total player count not a multiple of 7
        s = create_seeder(num_players=22)
        self.assertRaises(InvalidPlayerCount, s.seed_games)

    def test_seed_games_wrong_number_of_players_2(self):
        # Multiple of 7 players, minus one not playing
        s = create_seeder(num_players=21)
        self.assertRaises(InvalidPlayerCount, s.seed_games, set(['U']))

    def test_seed_games_wrong_number_of_players_3(self):
        # Multiple of 7 players, plus one playing two games
        s = create_seeder(num_players=21)
        self.assertRaises(InvalidPlayerCount, s.seed_games, set(), set(['U']))

    def test_seed_games_wrong_number_of_players_4(self):
        # Multiple of 7 players, plus two playing two games
        s = create_seeder(num_players=21)
        self.assertRaises(InvalidPlayerCount, s.seed_games, set(), set(['T', 'U']))
        self.check_no_games_played(s)

    def test_seed_games_with_omission(self):
        # Multiple of 7 players plus one, minus one not playing
        s = create_seeder(num_players=22)
        omits = set(['U'])
        r = s.seed_games(omits)
        self.check_game_set(r, 21, omits)

    def test_seed_games_with_multiples(self):
        # Multiple of 7 players minus one, minus one playing two games
        s = create_seeder()
        dups = set(['T'])
        r = s.seed_games(players_doubling_up=dups)
        self.check_game_set(r, 21, duplicates=dups)

    def test_seed_games_invalid_dup(self):
        s = create_seeder()
        dups = set(['X'])
        self.assertRaises(InvalidPlayer, s.seed_games, players_doubling_up=dups)

    def test_seed_games_invalid_sit(self):
        s = create_seeder()
        sits = set(['X'])
        self.assertRaises(InvalidPlayer, s.seed_games, omitting_players=sits)

    def test_seed_games_separate_dups_1(self):
        s = create_seeder(num_players=26)
        dups = set(['A', 'B'])
        r = s.seed_games(players_doubling_up=dups)
        self.check_game_set(r, 28, duplicates=dups)
        # Check that no game has both the players playing two games
        for g in r:
            self.assertNotEqual('A' in g, 'B' in g)
        self.check_no_games_played(s)

    def test_seed_games_separate_dups_2(self):
        s = create_seeder(num_players=18)
        dups = set(['A', 'B', 'C'])
        r = s.seed_games(players_doubling_up=dups)
        self.check_game_set(r, 21, duplicates=dups)
        # Check that no game has all the players playing two games
        for g in r:
            if ('A' in g) and ('B' in g):
                self.assertNotIn('C', g)
        self.check_no_games_played(s)


class ExhaustiveGameSeederTest(unittest.TestCase):
    """
    Validate an exhaustive GameSeeder seeding games
    """

    # Our players will be strings (names)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # TODO This is a copy-paste from the class above. Should share code
    def check_game(self, game):
        # Game should have exactly 7 players
        self.assertEqual(len(game), 7)
        # Games should always be sets (and hence have no duplicate players)
        self.assertTrue(isinstance(game, set))

    # TODO This is a copy-paste from the class above, then modified. Should share code
    def check_game_set(self, game_set, players):
        game_count = len(game_set)
        self.assertEqual(game_count, players // 7)
        # Every game should be valid by itself
        for g in game_set:
            self.check_game(g)
        # Each player should be present exactly once
        players = set()
        for g in game_set:
            players |= g
        self.assertEqual(len(players), 7 * game_count, "One or more players is playing multiple games")

    def test_exhaustive_seeding(self):
        players = [(7, 42), (14, 36)]
        for count, fitness in players:
            with self.subTest(player_count=count):
                seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                                    seed_method=SeedMethod.EXHAUSTIVE)
                for i in range(count):
                    seeder.add_player('%dp' % i)
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

    def test_exhaustive_with_dups(self):
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                            seed_method=SeedMethod.EXHAUSTIVE)
        for i in range(13):
            seeder.add_player('%dp' %i)
        dup = '%dp' % 2
        r = seeder.seed_games(players_doubling_up=set([dup]))
        # We should have two valid games, with player <dup> in both
        self.assertEqual(len(r), 2)
        for g in r:
            self.check_game(g)
            self.assertIn(dup, g)
        self.assertEqual(seeder._set_fitness(r), 0)
        # Add those games as played
        for g in r:
            seeder.add_played_game(with_powers(g))
        dup = '%dp' % 3
        r = seeder.seed_games(players_doubling_up=set([dup]))
        # We should again have two valid games, again with (different) player <dup> in both
        self.assertEqual(len(r), 2)
        for g in r:
            self.check_game(g)
            self.assertIn(dup, g)
        # Check that game_set has the expected fitness score
        self.assertEqual(seeder._set_fitness(r), 42)

    def test_exhaustive_wrong_count(self):
        seeder = GameSeeder(['1', '2', '3', '4', '5', '6', '7'],
                            seed_method=SeedMethod.EXHAUSTIVE)
        for i in range(13):
            seeder.add_player('%dp' %i)
        self.assertRaises(InvalidPlayerCount, seeder.seed_games)


if __name__ == '__main__':
    unittest.main()
