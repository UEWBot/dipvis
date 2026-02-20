# Diplomacy Tournament Visualiser
# Copyright (C) 2022 Chris Brand
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

from unittest import skip
from urllib.parse import urlencode, urlunparse

from django.test import TestCase, tag

from tournament.webdip import (FALL, POWERS, SPRING, WEBDIPLOMACY_NETLOC, Game,
                               InvalidGameUrl, UnsupportedVariant)


INVALID_GAME_ID = 1
VARIANT_GAME_ID = 457652
SOLO_GAME_ID = 334382
#DRAW_2_GAME_ID = 5127188186136576
DRAW_3_GAME_ID = 13
DRAW_4_GAME_ID = 340030
DRAW_5_GAME_ID = 21
DRAW_6_GAME_ID = 404806
DRAW_7_GAME_ID = 19
#SANDBOX_GAME_ID = 5766492401172480


@skip('WebDip parsing is broken')
class WebDiplomacyTests(TestCase):
    @tag('webdip')
    def test_webdip_game_non_wd_url(self):
        """Not a webdip URL."""
        path = 'board.php'
        url = urlunparse(('https', 'google.com', path, '', '', ''))
        self.assertRaises(InvalidGameUrl, Game, url)

    def test_webdip_game_invalid_game_id(self):
        """Invalid game id."""
        path = 'board.php'
        query = {'gameID': f'{INVALID_GAME_ID}'}
        url = urlunparse(('https', WEBDIPLOMACY_NETLOC, path, '', urlencode(query), ''))
        self.assertRaises(InvalidGameUrl, Game, url)

    def test_webdip_variant_game(self):
        """Variant game id."""
        path = 'board.php'
        query = {'gameID': f'{VARIANT_GAME_ID}'}
        url = urlunparse(('https', WEBDIPLOMACY_NETLOC, path, '', urlencode(query), ''))
        self.assertRaises(UnsupportedVariant, Game, url)

    def test_webdip_not_game(self):
        """Valid WebDip URL that is not a game."""
        path = 'userprofile.php'
        query = {'userID': '108284'}
        url = urlunparse(('https', WEBDIPLOMACY_NETLOC, path, '', urlencode(query), ''))
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

    @tag('webdip')
    def test_webdip_game_solo(self):
        """Solo victory. Also validates FALL"""
        path = 'board.php'
        query = {'gameID': f'{SOLO_GAME_ID}'}
        url = urlunparse(('https', WEBDIPLOMACY_NETLOC, path, '', urlencode(query), ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (4, 'FreedomPanda'),
                   POWERS[1]: (0, 'danikine74'),
                   POWERS[2]: (2, 'wansiuhay'),
                   POWERS[3]: (18, 'Balki Bartokomous'),
                   POWERS[4]: (5, 'pyxxy'),
                   POWERS[5]: (0, 'FxFocus'),
                   POWERS[6]: (5, 'Bam47'),
                  }
        self.assertEqual(g.id, SOLO_GAME_ID)
        self.assertEqual(g.name, 'Mid-tier gunboat at an affordable price-19')
        self.assertEqual(g.url, url)
        self.assertIs(False, g.ongoing)
        self.assertEqual(g.result, 'Solo')
        self.assertEqual(g.soloer, 'Balki Bartokomous')
        self.assertEqual(g.soloing_power, POWERS[3])
        self.assertEqual(g.season, FALL)
        self.assertEqual(g.year, 1909)
        self.check_game_results(g, RESULTS)

    #@tag('webdip')
    #def test_webdip_game_2way(self):
    #    g = Game(DRAW_2_GAME_ID)

    @tag('webdip')
    def test_webdip_game_3way(self):
        """3-way draw. Also validates SPRING"""
        path = 'board.php'
        query = {'gameID': f'{DRAW_3_GAME_ID}'}
        url = urlunparse(('https', WEBDIPLOMACY_NETLOC, path, '', urlencode(query), ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (17, 'Thrawn369'),
                   POWERS[1]: (8, 'jed'),
                   POWERS[2]: (6, 'wlievens'),
                   POWERS[3]: (0, 'Mikhail'),
                   POWERS[4]: (0, 'DDSnake'),
                   POWERS[5]: (0, 'sadun'),
                   POWERS[6]: (0, 'Nirrey'),
                  }
        self.assertEqual(g.id, DRAW_3_GAME_ID)
        self.assertEqual(g.name, 'hero')
        self.assertEqual(g.url, url)
        self.assertIs(False, g.ongoing)
        self.assertEqual(g.result, '3-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1910)
        self.check_game_results(g, RESULTS)

    @tag('webdip')
    def test_webdip_game_4way(self):
        """4-way draw. Also validates URL with trailing garbage"""
        path = 'board.php'
        query = {'gameID': f'{DRAW_4_GAME_ID}garbage'}
        url = urlunparse(('https', WEBDIPLOMACY_NETLOC, path, '', urlencode(query), ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (9, 'Talby2'),
                   POWERS[1]: (11, 'lpl1977'),
                   POWERS[2]: (6, 'pyxxy'),
                   POWERS[3]: (0, 'Balki Bartokomous'),
                   POWERS[4]: (0, 'teccles'),
                   POWERS[5]: (8, 'Pinecone333'),
                   POWERS[6]: (0, 'KalelChase'),
                  }
        self.assertEqual(g.id, DRAW_4_GAME_ID)
        self.assertEqual(g.name, 'gunboat with EOG expectation 4')
        self.assertEqual(g.url, url)
        self.assertIs(False, g.ongoing)
        self.assertEqual(g.result, '4-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1912)
        self.check_game_results(g, RESULTS)

    @tag('webdip')
    def test_webdip_game_5way(self):
        """5-way draw. Also validates game with resigned player"""
        path = 'board.php'
        query = {'gameID': f'{DRAW_5_GAME_ID}'}
        url = urlunparse(('https', WEBDIPLOMACY_NETLOC, path, '', urlencode(query), ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (0, 'clanger165'),
                   POWERS[1]: (7, 'rasteroid'),
                   POWERS[2]: (5, 'Salmaneser'),
                   POWERS[3]: (0, 'bugbuster'),
                   POWERS[4]: (2, 'everycom'),
                   POWERS[5]: (16, 'wlievens'),
                   POWERS[6]: (1, 'sadun'),
                  }
        self.assertEqual(g.id, DRAW_5_GAME_ID)
        self.assertEqual(g.name, 'Newbie')
        self.assertEqual(g.url, url)
        self.assertIs(False, g.ongoing)
        self.assertEqual(g.result, '5-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1905)
        self.check_game_results(g, RESULTS)

    @tag('webdip')
    def test_webdip_game_6way(self):
        """6-way draw. Also validates games with CD"""
        path = 'board.php'
        query = {'gameID': f'{DRAW_6_GAME_ID}'}
        url = urlunparse(('https', WEBDIPLOMACY_NETLOC, path, '', urlencode(query), ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (0, 'Sploack'),
                   POWERS[1]: (2, 'jon15'),
                   POWERS[2]: (1, 'Bismarck70'),
                   POWERS[3]: (11, 'pyxxy'),
                   POWERS[4]: (5, 'Chatnoir'),
                   POWERS[5]: (7, 'Rymeorsk'),
                   POWERS[6]: (8, 'SpaceDip'),
                  }
        self.assertEqual(g.id, DRAW_6_GAME_ID)
        self.assertEqual(g.name, 'Meta Speedboat Tournament-149')
        self.assertEqual(g.url, url)
        self.assertIs(False, g.ongoing)
        self.assertEqual(g.result, '6-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1911)
        self.check_game_results(g, RESULTS)

    @tag('webdip')
    def test_webdip_game_7way(self):
        """7-way draw."""
        path = 'board.php'
        query = {'gameID': f'{DRAW_7_GAME_ID}'}
        url = urlunparse(('https', WEBDIPLOMACY_NETLOC, path, '', urlencode(query), ''))
        g = Game(url)
        RESULTS = {POWERS[0]: (2, 'Mikhail'),
                   POWERS[1]: (2, 'Salmaneser'),
                   POWERS[2]: (5, 'rasteroid'),
                   POWERS[3]: (3, 'Fabio'),
                   POWERS[4]: (3, 'sadun'),
                   POWERS[5]: (14, 'Tobermory'),
                   POWERS[6]: (1, 'vuurdraak'),
                  }
        self.assertEqual(g.id, DRAW_7_GAME_ID)
        self.assertEqual(g.name, 'newbz')
        self.assertEqual(g.url, url)
        self.assertIs(False, g.ongoing)
        self.assertEqual(g.result, '7-way draw')
        self.assertIs(g.soloer, None)
        self.assertIs(g.soloing_power, None)
        self.assertEqual(g.season, SPRING)
        self.assertEqual(g.year, 1909)
        self.check_game_results(g, RESULTS)

    # TODO Would be nice test in-progress games, both anonymous and not
