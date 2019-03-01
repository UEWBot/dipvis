# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016 Chris Brand
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

from django.core.exceptions import ValidationError
from django.test import TestCase

from tournament.diplomacy import validate_year, validate_year_including_start
from tournament.diplomacy import validate_ranking
from tournament.diplomacy import GreatPower, GameSet, SetPower, SupplyCentre
from tournament.diplomacy import TOTAL_SCS, WINNING_SCS

class DiplomacyTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    # TOTAL_SCS
    def test_total_scs(self):
        self.assertEqual(TOTAL_SCS, 34)

    # WINNING_SCS
    def test_total_scs(self):
        self.assertEqual(WINNING_SCS, 18)

    # validate_year()
    def test_validate_year_negative(self):
        self.assertRaises(ValidationError, validate_year, -1)

    def test_validate_year_1899(self):
        self.assertRaises(ValidationError, validate_year, 1899)

    def test_validate_year_1900(self):
        self.assertRaises(ValidationError, validate_year, 1900)

    def test_validate_year_1901(self):
        self.assertIsNone(validate_year(1901))

    # validate_year_including_start()
    def test_validate_year_inc_start_negative(self):
        self.assertRaises(ValidationError, validate_year_including_start, -1)

    def test_validate_year_inc_start_1899(self):
        self.assertRaises(ValidationError, validate_year_including_start, 1899)

    def test_validate_year_inc_start_1900(self):
        self.assertIsNone(validate_year_including_start(1900))

    def test_validate_year_inc_start_1901(self):
        self.assertIsNone(validate_year_including_start(1901))

    # validate_ranking()
    def test_validate_ranking_negative(self):
        self.assertRaises(ValidationError, validate_ranking, -1)

    def test_validate_ranking_zero(self):
        self.assertRaises(ValidationError, validate_ranking, 0)

    def test_validate_ranking_one(self):
        self.assertIsNone(validate_ranking(1))

    def test_validate_ranking_seven(self):
        self.assertIsNone(validate_ranking(7))

    def test_validate_ranking_eight(self):
        self.assertRaises(ValidationError, validate_ranking, 8)

    # TODO validate_preference_string()

    # TODO game_image_location()

    # GreatPower
    # GreatPower.starting_centres
    def test_greatpower_starting_centres(self):
        for gp in GreatPower.objects.all():
            if gp.abbreviation == 'R':
                self.assertEqual(gp.starting_centres, 4)
            else:
                self.assertEqual(gp.starting_centres, 3)

    # GreatPower.__str__()
    def test_greatpower_str(self):
        for gp in GreatPower.objects.all():
            self.assertEqual(gp.name, str(gp))

    # GameSet
    # GameSet.__str__()
    def test_gameset_str(self):
        for gs in GameSet.objects.all():
            self.assertEqual(gs.name, str(gs))

    # SetPower
    # SetPower.__str__()
    def test_setpower_str(self):
        for sp in SetPower.objects.all():
            self.assertIn(sp.the_set.name, str(sp))
            self.assertIn(sp.power.name, str(sp))

    # SupplyCentre
    # SupplyCentre.__str__()
    def test_supplycentre_str(self):
        for sc in SupplyCentre.objects.all():
            self.assertEqual(sc.name, str(sc))
