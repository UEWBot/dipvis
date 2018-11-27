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
from tournament.game_seeder import *

class GameSeederSetupTest(unittest.TestCase):
    """
    Validate the setup of GameSeeder - adding players, games, etc.
    """

    # Our players will be strings (names)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # add_player()
    def test_add_player_twice(self):
        seeder = GameSeeder()
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_player, 'A')

    # add_played_game()
    def test_add_played_game(self):
        seeder = GameSeeder()
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_player('H')
        seeder.add_played_game(set(['A', 'B', 'C', 'D', 'E', 'F', 'G']))

    def test_add_played_game_invalid_player(self):
        seeder = GameSeeder()
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        self.assertRaises(InvalidPlayer, seeder.add_played_game, set(['A', 'B', 'C', 'D', 'E', 'F', 'G']))

    def test_add_played_game_player_too_few_players(self):
        seeder = GameSeeder()
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        self.assertRaises(InvalidPlayerCount, seeder.add_played_game, set(['A', 'B', 'C', 'D', 'E', 'F']))

    def test_add_played_game_player_too_many_players(self):
        seeder = GameSeeder()
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_player('H')
        self.assertRaises(InvalidPlayerCount, seeder.add_played_game, set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']))

    # add_bias()
    def test_add_bias_same_player(self):
        seeder = GameSeeder()
        seeder.add_player('A')
        self.assertRaises(InvalidPlayerPairing, seeder.add_bias, 'A', 'A', 1)

    def test_add_bias_invalid_weight(self):
        seeder = GameSeeder()
        seeder.add_player('A')
        seeder.add_player('B')
        self.assertRaises(InvalidWeight, seeder.add_bias, 'A', 'B', 0)

    def test_add_bias_unknown_player1(self):
        seeder = GameSeeder()
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_bias, 'B', 'A', 1)

    def test_add_bias_unknown_player2(self):
        seeder = GameSeeder()
        seeder.add_player('A')
        self.assertRaises(InvalidPlayer, seeder.add_bias, 'A', 'B', 1)

    def test_add_bias(self):
        seeder = GameSeeder()
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
        seeder.add_bias('A', 'B', 1)
        # That should suffice to keep those players apart
        r = seeder.seed_games()
        for g in r:
            if 'A' in g:
                self.assertNotIn('B', g)
            if 'B' in g:
                self.assertNotIn('A', g)

    # _fitness_score()
    def test_fitness_score_no_games(self):
        seeder = GameSeeder()
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        self.assertEqual(0, seeder._fitness_score(set(['A', 'B', 'C', 'D', 'E', 'F', 'G'])))

    def test_fitness_score_one_pair_played(self):
        seeder = GameSeeder()
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
        seeder.add_played_game(set(['A', 'B', 'C', 'D', 'E', 'F', 'G']))
        self.assertEqual(2, seeder._fitness_score(set(['A', 'B', 'H', 'I', 'J', 'K', 'L'])))

    def test_fitness_score_worst_case(self):
        seeder = GameSeeder()
        seeder.add_player('A')
        seeder.add_player('B')
        seeder.add_player('C')
        seeder.add_player('D')
        seeder.add_player('E')
        seeder.add_player('F')
        seeder.add_player('G')
        seeder.add_played_game(set(['A', 'B', 'C', 'D', 'E', 'F', 'G']))
        self.assertEqual(42, seeder._fitness_score(set(['A', 'B', 'C', 'D', 'E', 'F', 'G'])))

    def test_fitness_score_two_pairs(self):
        seeder = GameSeeder()
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
        seeder.add_played_game(set(['A', 'B', 'C', 'D', 'E', 'F', 'G']))
        seeder.add_played_game(set(['H', 'I', 'J', 'K', 'L', 'M', 'N']))
        # Game with two pairs from each earlier game
        game = set(['A', 'B', 'M', 'N', 'O', 'P', 'Q'])
        self.assertEqual(4, seeder._fitness_score(game))

    def test_fitness_score_one_triple(self):
        seeder = GameSeeder()
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
        seeder.add_played_game(set(['A', 'B', 'C', 'D', 'E', 'F', 'G']))
        # Game with two pairs from each earlier game
        game = set(['A', 'C', 'D', 'H', 'I', 'J', 'K'])
        self.assertEqual(6, seeder._fitness_score(game))

    def test_fitness_score_third_round(self):
        seeder = GameSeeder()
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
        seeder.add_played_game(set(['A', 'B', 'C', 'D', 'E', 'F', 'G']))
        seeder.add_played_game(set(['A', 'B', 'H', 'I', 'J', 'K', 'L']))
        game = set(['A', 'B', 'M', 'N', 'O', 'P', 'Q'])
        self.assertEqual(8, seeder._fitness_score(game))

def create_seeder(starts=1, iterations=1000):
    # As there's no way to remove players or duplicates, we'll re-create the seeder in each test
    seeder = GameSeeder(starts, iterations)
    # 20 players to start with
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
    seeder.add_player('R')
    seeder.add_player('S')
    seeder.add_player('T')
    return seeder

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

    def check_game_set(self, game_set, players, omissions = set(), duplicates = set()):
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

    # seed_games()
    def test_seed_games_initial(self):
        s = create_seeder()
        s.add_player('U')
        r = s.seed_games()
        self.check_game_set(r, 21)

    def test_seed_games_second_round(self):
        s = create_seeder()
        s.add_player('U')
        # Add some previously-played games
        s.add_played_game(set(['A', 'B', 'C', 'D', 'E', 'F', 'G']))
        s.add_played_game(set(['H', 'I', 'J', 'K', 'L', 'M', 'N']))
        s.add_played_game(set(['O', 'P', 'Q', 'R', 'S', 'T', 'U']))
        r = s.seed_games()
        self.check_game_set(r, 21)
        # Check that game_set has a "good" fitness score
        # With 21 players, we should end up with games with 2 pairs and a triplet,
        # which gives each game a fitness of 2+2+6=10, and the set a fitness of 10*3=30
        self.assertEqual(s._set_fitness(r), 30)

    def seed_bigger_tournament(self, starts, iterations):
        # Two rounds of a 49-player tournament
        seeder = GameSeeder(starts, iterations)
        for i in range(49):
            seeder.add_player('%dp' % i)
        r = seeder.seed_games()
        self.check_game_set(r, 49)
        # First round by definition should have a fitness of zero
        self.assertEqual(seeder._set_fitness(r), 0)
        # Add the first round games as played
        for g in r:
            seeder.add_played_game(g)
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
        s = create_seeder()
        s.add_player('U')
        s.add_player('V')
        self.assertRaises(InvalidPlayerCount, s.seed_games)

    def test_seed_games_wrong_number_of_players_2(self):
        # Multiple of 7 players, minus one not playing
        s = create_seeder()
        s.add_player('U')
        self.assertRaises(InvalidPlayerCount, s.seed_games, set(['U']))

    def test_seed_games_wrong_number_of_players_3(self):
        # Multiple of 7 players, plus one playing two games
        s = create_seeder()
        s.add_player('U')
        self.assertRaises(InvalidPlayerCount, s.seed_games, set(), set(['U']))

    def test_seed_games_with_omission(self):
        # Multiple of 7 players plus one, minus one not playing
        s = create_seeder()
        s.add_player('U')
        s.add_player('V')
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
                seeder = GameSeeder(seed_method=SeedMethod.EXHAUSTIVE)
                for i in range(count):
                    seeder.add_player('%dp' % i)
                r = seeder.seed_games()
                self.check_game_set(r, count)
                # First round by definition should have a fitness of zero
                self.assertEqual(seeder._set_fitness(r), 0)
                # Add the first round games as played
                for g in r:
                    seeder.add_played_game(g)
                r = seeder.seed_games()
                self.check_game_set(r, count)
                # Check that game_set has the expected fitness score
                self.assertEqual(seeder._set_fitness(r), fitness)

    def test_exhaustive_with_dups(self):
        seeder = GameSeeder(seed_method=SeedMethod.EXHAUSTIVE)
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
            seeder.add_played_game(g)
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
        seeder = GameSeeder(seed_method=SeedMethod.EXHAUSTIVE)
        for i in range(13):
            seeder.add_player('%dp' %i)
        self.assertRaises(InvalidPlayerCount, seeder.seed_games)

if __name__ == '__main__':
    unittest.main()
