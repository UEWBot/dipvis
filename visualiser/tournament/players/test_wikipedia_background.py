# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2026 Chris Brand
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

from django.test import TestCase

from . import WikipediaBackground


class WikipediaBackgroundTests(TestCase):

    def test_wikipedia_background_titles(self):
        name = 'Cyrille Sevin'
        flags = ['France']
        bg = WikipediaBackground(name)
        titles = bg.titles()
        self.assertEqual(len(titles), 8)
        for t in titles:
            with self.subTest(title=t):
                if t['Year'] == 1997:
                    if t['Tournament'] == 'EuroDipCon':
                        self.assertEqual(t['European Champion'], name)
                        self.assertEqual(t['European Champion Flags'], flags)
                    else:
                        self.assertEqual(t['World Champion'], name)
                        self.assertEqual(t['World Champion Flags'], flags)
                elif t['Year'] == 2001:
                    self.assertEqual(t['World Champion'], name)
                    self.assertEqual(t['World Champion Flags'], flags)
                elif t['Year'] == 2004:
                    self.assertEqual(t['Third'], name)
                    self.assertEqual(t['Third Flags'], flags)
                elif t['Year'] == 2006:
                    self.assertEqual(t['Second'], name)
                    self.assertEqual(t['Second Flags'], flags)
                elif t['Year'] == 2008:
                    self.assertEqual(t['Second'], name)
                    self.assertEqual(t['Second Flags'], flags)
                elif t['Year'] == 2013:
                    self.assertEqual(t['World Champion'], name)
                    self.assertEqual(t['World Champion Flags'], flags)
                else:
                    # 2015
                    self.assertEqual(t['European Champion'], name)
                    self.assertEqual(t['European Champion Flags'], flags)

    def test_wikipedia_background_nationalities(self):
        """Check that multi-nationals get parsed correctly"""
        name = 'Antonio Ribeiro da Silva'
        flags = ['France', 'Portugal']
        bg = WikipediaBackground(name)
        titles = bg.titles()
        self.assertEqual(len(titles), 1)
        for t in titles:
            with self.subTest(title=t):
                self.assertEqual(t['Second'], name)
                self.assertEqual(t['Second Flags'], flags)
