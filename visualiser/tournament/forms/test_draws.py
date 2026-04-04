# Diplomacy Tournament Visualiser
# Copyright (C) 2019-2026 Chris Brand
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
Draw Forms Tests for the Diplomacy Tournament Visualiser.
"""
from django.test import TestCase

from tournament.diplomacy import GreatPower
from tournament.forms import DrawForm
from tournament.models import DrawSecrecy, Seasons


class DrawFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

    # Common validation method
    def check_common_fields(self, form):
        for field in ('year', 'season', 'proposer'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)

    def test_init_missing_dias(self):
        with self.assertRaises(KeyError):
            DrawForm(secrecy=DrawSecrecy.SECRET,
                     concession=False)

    def test_init_missing_concession(self):
        with self.assertRaises(KeyError):
            DrawForm(dias=True,
                     secrecy=DrawSecrecy.SECRET)

    def test_init_missing_secrecy(self):
        with self.assertRaises(KeyError):
            DrawForm(dias=True,
                     concession=False)

    def test_init_invalid_secrecy(self):
        with self.assertRaises(AssertionError):
            DrawForm(dias=True,
                     secrecy='Q',
                     concession=False)

    def test_dias_secret(self):
        form = DrawForm(dias=True,
                        secrecy=DrawSecrecy.SECRET,
                        concession=False)
        # Form should have year, season, proposer, and passed
        self.check_common_fields(form)
        self.assertIn('passed', form.fields)
        for field in ('powers', 'votes_in_favour'):
            with self.subTest(field=field):
                self.assertNotIn(field, form.fields)

    def test_non_dias_secret(self):
        form = DrawForm(dias=False,
                        secrecy=DrawSecrecy.SECRET,
                        concession=False)
        # Form should have year, season, proposer, powers, and passed
        self.check_common_fields(form)
        for field in ('powers', 'passed'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)
        self.assertNotIn('votes_in_favour', form.fields)

    def test_dias_counts(self):
        form = DrawForm(dias=True,
                        secrecy=DrawSecrecy.COUNTS,
                        concession=False)
        # Form should have year, season, proposer, and votes_in_favour
        self.check_common_fields(form)
        self.assertIn('votes_in_favour', form.fields)
        for field in ('powers', 'passed'):
            with self.subTest(field=field):
                self.assertNotIn(field, form.fields)

    def test_non_dias_counts(self):
        form = DrawForm(dias=False,
                        secrecy=DrawSecrecy.COUNTS,
                        concession=False)
        # Form should have year, season, proposer, powers, and votes_in_favour
        self.check_common_fields(form)
        for field in ('powers', 'votes_in_favour'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)
        self.assertNotIn('passed', form.fields)

    def test_concession_secret(self):
        form = DrawForm(dias=True,
                        secrecy=DrawSecrecy.SECRET,
                        concession=True)
        # Form should have year, season, proposer, powers, and passed
        self.check_common_fields(form)
        for field in ('powers', 'passed'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)
        for field in ('votes_in_favour'):
            with self.subTest(field=field):
                self.assertNotIn(field, form.fields)

    def test_concession_counts(self):
        form = DrawForm(dias=True,
                        secrecy=DrawSecrecy.COUNTS,
                        concession=True)
        # Form should have year, season, proposer, powers, and votes_in_favour
        self.check_common_fields(form)
        for field in ('powers', 'votes_in_favour'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)
        for field in ('passed'):
            with self.subTest(field=field):
                self.assertNotIn(field, form.fields)

    def test_proposer_optional(self):
        form = DrawForm(dias=False,
                        secrecy=DrawSecrecy.COUNTS,
                        concession=False)
        self.assertIs(False, form.fields['proposer'].required)

    def test_concession_secret_has_changed(self):
        form = DrawForm(dias=False,
                        secrecy=DrawSecrecy.SECRET,
                        concession=True,
                        initial={'year': 1902,
                                 'season': Seasons.FALL,
                                 'powers': self.england,
                                 'passed': True},
                        data={'year': '1902',
                              'season': 'F',
                              'powers': str(self.england.name),
                              'passed': 'ok'})
        self.assertIs(False, form.has_changed())

    def test_concession_counts_has_changed(self):
        form = DrawForm(dias=False,
                        secrecy=DrawSecrecy.COUNTS,
                        concession=True,
                        initial={'year': 1902,
                                 'season': Seasons.FALL,
                                 'powers': self.england,
                                 'votes_in_favour': 3},
                        data={'year': '1902',
                              'season': 'F',
                              'powers': str(self.england.name),
                              'votes_in_favour': '3'})
        self.assertIs(False, form.has_changed())

    def test_dias_secret_has_changed(self):
        form = DrawForm(dias=True,
                        secrecy=DrawSecrecy.SECRET,
                        concession=False,
                        initial={'year': 1902,
                                 'season': Seasons.FALL,
                                 'passed': True},
                        data={'year': '1902',
                              'season': 'F',
                              'passed': 'ok'})
        self.assertIs(False, form.has_changed())

    def test_dias_counts_has_changed(self):
        form = DrawForm(dias=True,
                        secrecy=DrawSecrecy.COUNTS,
                        concession=False,
                        initial={'year': 1902,
                                 'season': Seasons.FALL,
                                 'votes_in_favour': 3},
                        data={'year': '1902',
                              'season': 'F',
                              'votes_in_favour': '3'})
        self.assertIs(False, form.has_changed())

    def test_non_dias_secret_has_changed(self):
        form = DrawForm(dias=False,
                        secrecy=DrawSecrecy.SECRET,
                        concession=False,
                        initial={'year': 1902,
                                 'season': Seasons.FALL,
                                 'powers': [self.england, self.turkey],
                                 'passed': True},
                        data={'year': '1902',
                              'season': 'F',
                              'powers': [str(self.england.name), str(self.turkey.name)],
                              'passed': 'ok'})
        self.assertIs(False, form.has_changed())

    def test_non_dias_counts_has_changed(self):
        form = DrawForm(dias=False,
                        secrecy=DrawSecrecy.COUNTS,
                        concession=False,
                        initial={'year': 1902,
                                 'season': Seasons.FALL,
                                 'powers': [self.england, self.turkey],
                                 'votes_in_favour': 3},
                        data={'year': '1902',
                              'season': 'F',
                              'powers': [str(self.england.name), str(self.turkey.name)],
                              'votes_in_favour': '3'})
        self.assertIs(False, form.has_changed())
