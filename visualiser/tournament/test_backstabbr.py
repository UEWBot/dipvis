# Diplomacy Tournament Visualiser
# Copyright (C) 2020 Chris Brand
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

from urllib.parse import urlunparse

from django.test import TestCase, tag

from tournament.backstabbr import Game, InvalidGameUrl
from tournament.backstabbr import BACKSTABBR_NETLOC
from tournament.backstabbr import POWERS, SPRING, FALL, WINTER


INVALID_GAME_NUMBER = 1
SOLO_GAME_NUMBER = 5128998112198656
#DRAW_2_GAME_NUMBER = 5127188186136576
DRAW_3_GAME_NUMBER = 4917371326693376
DRAW_4_GAME_NUMBER = 5127188186136576
DRAW_5_GAME_NUMBER = 4745603911778304
DRAW_6_GAME_NUMBER = 4902987233755136
DRAW_7_GAME_NUMBER = 4662834623938560
SANDBOX_GAME_NUMBER = 5766492401172480


@tag('backstabbr')
class BackstabbrTests(TestCase):
    @tag('backstabbr')
    def test_backstabbr_game_non_bs_url(self):
        """Not a backstabbr URL."""
        path = 'game/%s' % INVALID_GAME_NUMBER
        url = urlunparse(('https', 'google.com', path, '', '', ''))
        self.assertRaises(InvalidGameUrl, Game, url)

    def test_backstabbr_game_invalid_game_number(self):
        """Invalid game number."""
        path = 'game/%s' % INVALID_GAME_NUMBER
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        self.assertRaises(InvalidGameUrl, Game, url)

    def test_backstabbr_game_not_sandbox_or_game(self):
        """Neither a sandbox nor a regular game."""
        path = 'member/jHm3Y12XTZGeoRd2kl_cWw'
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        self.assertRaises(InvalidGameUrl, Game, url)

    def test_backstabbr_game_turn_url(self):
        """URL inside the game (would be nice to support this some day)."""
        path = 'game/%s/1902/spring' % DRAW_3_GAME_NUMBER
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        self.assertRaises(InvalidGameUrl, Game, url)

    def check_results(self, sc_counts, results):
        """Check that the centrecounts are as expected"""
        for k, v in results.items():
            with self.subTest(power=k):
                self.assertEqual(sc_counts[k], v[0])

    def check_game_results(self, g, results):
        """Check that the players and current centrecounts are as expected"""
        for k, v in results.items():
            with self.subTest(power=k):
                # The "Display name" can be changed, but the number should still match
                self.assertEqual(g.players[k][0].split('#')[-1], v[1].split('#')[-1])
        self.check_results(g.sc_counts, results)

    @tag('backstabbr')
    def test_backstabbr_game_solo(self):
        """Solo victory. Also validates WINTER"""
        path = 'game/%s' % SOLO_GAME_NUMBER
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (0, 'KodaHack#1592'),
                   POWERS[1]: (11, 'RobertTheRousse#5998'),
                   POWERS[2]: (0, 'buffalo#8170'),
                   POWERS[3]: (0, 'Mitch M. #5936'),
                   POWERS[4]: (4, 'Jesus.Saviouras#9498'),
                   POWERS[5]: (0, 'sloth.dc#9873'),
                   POWERS[6]: (19, 'Chris Brand#8810'),
                  }
        self.assertEqual(g.number, SOLO_GAME_NUMBER)
        self.assertEqual(g.name, 'VHGunboat 93: Neptunium')
        self.assertEqual(g.url, url)
        self.assertTrue(g.regular_game)
        self.assertFalse(g.sandbox_game)
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, 'Solo')
        self.assertEqual(g.soloer, 'Chris Brand#8810')
        self.assertEqual(g.soloing_power, POWERS[6])
        self.assertEqual(g.season, WINTER)
        self.assertEqual(g.year, 1914)
        self.assertEqual(g.gm, 'dance.scholar#1423')
        self.check_game_results(g, RESULTS)

    #@tag('backstabbr')
    #def test_backstabbr_game_2way(self):
    #    g = Game(DRAW_2_GAME_NUMBER)

    @tag('backstabbr')
    def test_backstabbr_game_3way(self):
        """3-way draw. Also validates FALL"""
        path = 'game/%s' % DRAW_3_GAME_NUMBER
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (0, 'edwardzachary#5878'),
                   POWERS[1]: (0, 'RobertTheRousse#5998'),
                   POWERS[2]: (7, 'zhammond527#4601'),
                   POWERS[3]: (0, 'Mike Moore#5938'),
                   POWERS[4]: (0, 'Chris Brand#8810'),
                   POWERS[5]: (12, 'Riaz #6696'),
                   POWERS[6]: (15, 'fulhamCF#5591'),
                  }
        self.assertEqual(g.number, DRAW_3_GAME_NUMBER)
        self.assertEqual(g.name, '233: Fibonacci prime')
        self.assertEqual(g.url, url)
        self.assertTrue(g.regular_game)
        self.assertFalse(g.sandbox_game)
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, '3-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, FALL)
        self.assertEqual(g.year, 1913)
        self.assertEqual(g.gm, 'Jason Mastbaum#8314')
        self.check_game_results(g, RESULTS)

    @tag('backstabbr')
    def test_backstabbr_game_4way(self):
        """4-way draw. Also validates SPRING and long game name."""
        path = 'game/%s' % DRAW_4_GAME_NUMBER
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (0, 'sjmauris#7661'),
                   POWERS[1]: (15, 'buffalo#8170'),
                   POWERS[2]: (3, 'Mitch M. #5936'),
                   POWERS[3]: (0, 'Lex Luthor#8328'),
                   POWERS[4]: (7, 'RobertTheRousse#5998'),
                   POWERS[5]: (0, 'Chris Brand#8810'),
                   POWERS[6]: (9, 'David Hood#2887'),
                  }
        self.assertEqual(g.number, DRAW_4_GAME_NUMBER)
        self.assertEqual(g.name, 'VHGunboat 84 - Double-plus ungood')
        self.assertEqual(g.url, url)
        self.assertTrue(g.regular_game)
        self.assertFalse(g.sandbox_game)
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, '4-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1912)
        self.assertEqual(g.gm, 'sloth.dc#9873')
        self.check_game_results(g, RESULTS)

    @tag('backstabbr')
    def test_backstabbr_game_5way(self):
        """5-way draw. Also validates trailing / in game URL"""
        path = 'game/%s/' % DRAW_5_GAME_NUMBER
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (10, 'Mike Moore#5938'),
                   POWERS[1]: (0, 'arielmendezp#1663'),
                   POWERS[2]: (11, 'Riaz #6696'),
                   POWERS[3]: (7, 'Chris Brand#8810'),
                   POWERS[4]: (0, 'RobertTheRousse#5998'),
                   POWERS[5]: (3, 'Jay#2780'),
                   POWERS[6]: (3, 'corib#2857'),
                  }
        self.assertEqual(g.number, DRAW_5_GAME_NUMBER)
        self.assertEqual(g.name, "343 we're already dead")
        self.assertEqual(g.url, url)
        self.assertTrue(g.regular_game)
        self.assertFalse(g.sandbox_game)
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, '5-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1911)
        self.assertEqual(g.gm, 'OB_GYN_Kenobi#4766')
        self.check_game_results(g, RESULTS)

    @tag('backstabbr')
    def test_backstabbr_game_6way(self):
        """6-way draw."""
        path = 'game/%s' % DRAW_6_GAME_NUMBER
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (13, 'David Hood#2887'),
                   POWERS[1]: (1, 'Jason Mastbaum#8314'),
                   POWERS[2]: (5, 'Chris Brand#8810'),
                   POWERS[3]: (8, 'sionolen#8599'),
                   POWERS[4]: (5, 'adam.silverman#5954'),
                   POWERS[5]: (2, 'Grant Steel#4368'),
                   POWERS[6]: (0, 'maddotter#1574'),
                  }
        self.assertEqual(g.number, DRAW_6_GAME_NUMBER)
        self.assertEqual(g.name, '299 The seventh seal')
        self.assertEqual(g.url, url)
        self.assertTrue(g.regular_game)
        self.assertFalse(g.sandbox_game)
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, '6-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1917)
        self.assertEqual(g.gm, 'esilverman#6601')
        self.check_game_results(g, RESULTS)

    @tag('backstabbr')
    def test_backstabbr_game_7way(self):
        """7-way draw. Also validates short game name with description."""
        path = 'game/%s' % DRAW_7_GAME_NUMBER
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (6, 'Medusa#4960'),
                   POWERS[1]: (7, 'JamB#4071'),
                   POWERS[2]: (5, 'Melissa#7577'),
                   POWERS[3]: (7, 'ASig#9921'),
                   POWERS[4]: (3, 'bwtcf#4734'),
                   POWERS[5]: (2, 'Chris Brand#8810'),
                   POWERS[6]: (4, 'Maya K2#9400'),
                  }
        self.assertEqual(g.number, DRAW_7_GAME_NUMBER)
        self.assertEqual(g.name, 'West End Girls')
        self.assertEqual(g.url, url)
        self.assertTrue(g.regular_game)
        self.assertFalse(g.sandbox_game)
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, '7-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1908)
        self.assertEqual(g.gm, 'Andrew Goff#None')
        self.check_game_results(g, RESULTS)

    @tag('backstabbr')
    def test_backstabbr_sandbox(self):
        """Sandbox game"""
        path = 'sandbox/%s' % SANDBOX_GAME_NUMBER
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (0, 'Unknown'),
                   POWERS[1]: (1, 'Unknown'),
                   POWERS[2]: (6, 'Unknown'),
                   POWERS[3]: (6, 'Unknown'),
                   POWERS[4]: (4, 'Unknown'),
                   POWERS[5]: (11, 'Unknown'),
                   POWERS[6]: (6, 'Unknown'),
                  }
        self.assertEqual(g.number, SANDBOX_GAME_NUMBER)
        self.assertEqual(g.name, '#R2 FB Game')
        self.assertEqual(g.url, url)
        self.assertFalse(g.regular_game)
        self.assertTrue(g.sandbox_game)
        self.assertTrue(g.ongoing)
        self.assertEqual(g.result, '6 powers still alive')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, FALL)
        self.assertEqual(g.year, 1905)
        self.assertEqual(g.gm, 'Unknown')
        self.check_game_results(g, RESULTS)

    @tag('backstabbr')
    def test_backstabbr_turn_details(self):
        """Game.turn_details()"""
        path = 'game/%s' % DRAW_6_GAME_NUMBER
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        g = Game(url)
        sc_counts, soloing_power, sc_ownership, position, orders = g.turn_details(FALL, 1912)
        RESULTS = {POWERS[0]: (10, 'David Hood#2887'),
                   POWERS[1]: (1, 'Jason Mastbaum#8314'),
                   POWERS[2]: (4, 'Chris Brand#8810'),
                   POWERS[3]: (8, 'sionolen#8599'),
                   POWERS[4]: (8, 'adam.silverman#5954'),
                   POWERS[5]: (3, 'Grant Steel#4368'),
                   POWERS[6]: (0, 'maddotter#1574'),
                  }
        self.assertIs(soloing_power, None)
        self.check_results(sc_counts, RESULTS)

    # TODO Would be nice test in-progress games, both anonymous and not

    # TODO Test games where power(s) survive but vote themselves out of a draw
