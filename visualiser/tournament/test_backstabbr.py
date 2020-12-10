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

from django.test import TestCase, tag

from tournament.backstabbr import Game, InvalidGameId, POWERS, SPRING, FALL, WINTER

INVALID_GAME_NUMBER = 1
SOLO_GAME_NUMBER = 5128998112198656
#DRAW_2_GAME_NUMBER = 5127188186136576
DRAW_3_GAME_NUMBER = 4917371326693376
DRAW_4_GAME_NUMBER = 5127188186136576
DRAW_5_GAME_NUMBER = 4745603911778304
DRAW_6_GAME_NUMBER = 4902987233755136
DRAW_7_GAME_NUMBER = 4662834623938560


@tag('backstabbr')
class BackstabbrTests(TestCase):
    @tag('backstabbr')
    def test_backstabbr_game_invalid(self):
        """Invalid game number."""
        self.assertRaises(InvalidGameId, Game, INVALID_GAME_NUMBER)

    def check_results(self, g, results):
        """Check that the players and centrecounts are as expected"""
        for k, v in results.items():
            with self.subTest(power=k):
                self.assertEqual(g.powers[k][0], v[0])
                self.assertEqual(g.powers[k][1], v[1])

    @tag('backstabbr')
    def test_backstabbr_game_solo(self):
        """Solo victory. Also validates WINTER"""
        g = Game(SOLO_GAME_NUMBER)
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
        self.assertEqual(g.url, 'https://www.backstabbr.com/game/5128998112198656')
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, 'Solo')
        self.assertEqual(g.soloer, 'Chris Brand#8810')
        self.assertEqual(g.soloing_power, POWERS[6])
        self.assertEqual(g.season, WINTER)
        self.assertEqual(g.year, 1914)
        self.assertEqual(g.gm, 'dance.scholar#1423')
        self.check_results(g, RESULTS)

    #@tag('backstabbr')
    #def test_backstabbr_game_2way(self):
    #    g = Game(DRAW_2_GAME_NUMBER)

    @tag('backstabbr')
    def test_backstabbr_game_3way(self):
        """3-way draw. Also validates FALL"""
        g = Game(DRAW_3_GAME_NUMBER)
        RESULTS = {POWERS[0]: (0, 'edwardzachary#5878'),
                   POWERS[1]: (0, 'RobertTheRousse#5998'),
                   POWERS[2]: (7, 'zhammond527#4601'),
                   POWERS[3]: (0, 'Mike Moore#5938'),
                   POWERS[4]: (0, 'Chris Brand#8810'),
                   POWERS[5]: (12, 'Riaz #6696'),
                   POWERS[6]: (15, 'fulhamCF#279'),
                  }
        self.assertEqual(g.number, DRAW_3_GAME_NUMBER)
        self.assertEqual(g.name, '233: Fibonacci prime')
        self.assertEqual(g.url, 'https://www.backstabbr.com/game/4917371326693376')
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, '3-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, FALL)
        self.assertEqual(g.year, 1913)
        self.assertEqual(g.gm, 'Jason Mastbaum#8314')
        self.check_results(g, RESULTS)

    @tag('backstabbr')
    def test_backstabbr_game_4way(self):
        """4-way draw. Also validates SPRING and long game name."""
        g = Game(DRAW_4_GAME_NUMBER)
        RESULTS = {POWERS[0]: (0, 'sjmauris#7661'),
                   POWERS[1]: (15, 'buffalo#8170'),
                   POWERS[2]: (3, 'Mitch M. #5936'),
                   POWERS[3]: (0, 'Lex Luthor#8328'),
                   POWERS[4]: (7, 'RobertTheRousse#5998'),
                   POWERS[5]: (0, 'Chris Brand#8810'),
                   POWERS[6]: (9, 'David Hood#141'),
                  }
        self.assertEqual(g.number, DRAW_4_GAME_NUMBER)
        self.assertEqual(g.name, 'VHGunboat 84 - Double-plus ungood')
        self.assertEqual(g.url, 'https://www.backstabbr.com/game/5127188186136576')
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, '4-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1912)
        self.assertEqual(g.gm, 'sloth.dc#9873')
        self.check_results(g, RESULTS)

    @tag('backstabbr')
    def test_backstabbr_game_5way(self):
        """5-way draw."""
        g = Game(DRAW_5_GAME_NUMBER)
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
        self.assertEqual(g.url, 'https://www.backstabbr.com/game/4745603911778304')
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, '5-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1911)
        self.assertEqual(g.gm, 'OB_GYN_Kenobi#4766')
        self.check_results(g, RESULTS)

    @tag('backstabbr')
    def test_backstabbr_game_6way(self):
        """6-way draw."""
        g = Game(DRAW_6_GAME_NUMBER)
        RESULTS = {POWERS[0]: (13, 'David Hood#141'),
                   POWERS[1]: (1, 'Jason Mastbaum#8314'),
                   POWERS[2]: (5, 'Chris Brand#8810'),
                   POWERS[3]: (8, 'sionolen#8599'),
                   POWERS[4]: (5, 'adam.silverman#5954'),
                   POWERS[5]: (2, 'Grant Steel#4368'),
                   POWERS[6]: (0, 'maddotter#1574'),
                  }
        self.assertEqual(g.number, DRAW_6_GAME_NUMBER)
        self.assertEqual(g.name, '299 The seventh seal')
        self.assertEqual(g.url, 'https://www.backstabbr.com/game/4902987233755136')
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, '6-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1917)
        self.assertEqual(g.gm, 'esilverman#6601')
        self.check_results(g, RESULTS)

    @tag('backstabbr')
    def test_backstabbr_game_7way(self):
        """7-way draw. Also validates short game name with description."""
        g = Game(DRAW_7_GAME_NUMBER)
        RESULTS = {POWERS[0]: (6, 'Medusa#None'),
                   POWERS[1]: (7, 'JamB#None'),
                   POWERS[2]: (5, 'Melissa#7577'),
                   POWERS[3]: (7, 'ASig#9921'),
                   POWERS[4]: (3, 'bwtcf#None'),
                   POWERS[5]: (2, 'Chris Brand#8810'),
                   POWERS[6]: (4, 'Maya K2#9400'),
                  }
        self.assertEqual(g.number, DRAW_7_GAME_NUMBER)
        #self.assertEqual(g.name, 'West End Girls')
        self.assertEqual(g.url, 'https://www.backstabbr.com/game/4662834623938560')
        self.assertFalse(g.ongoing)
        self.assertEqual(g.result, '7-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1908)
        self.assertEqual(g.gm, 'Andrew Goff#None')
        self.check_results(g, RESULTS)

    # TODO Would be nice test in-progress games, both anonymous and not

    # TODO Test games where power(s) survive but vote themselves out of a draw
