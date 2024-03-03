# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2024 Chris Brand
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

from django_countries.fields import Country

from django.core.exceptions import ValidationError
from django.test import TestCase, tag

from tournament.diplomacy.models.great_power import GreatPower
from tournament.wdd import country_to_wdd, country_name_to_wdd, power_name_to_wdd
from tournament.wdd import wdd_img_to_country
from tournament.wdd import wdd_nation_to_country, wdd_url_to_tournament_id
from tournament.wdd import validate_wdd_player_id, validate_wdd_tournament_id
from tournament.wdd import WDD_UNKNOWN_COUNTRY, UnrecognisedCountry


class WDDTests(TestCase):
    fixtures = ['game_sets.json']

    # validate_wdd_player_id()
    @tag('wdd')
    def test_validate_wdd_player_id_me(self):
        self.assertIsNone(validate_wdd_player_id(4173))

    @tag('wdd')
    def test_validate_wdd_player_id_1(self):
        # 1 is known to be unused
        # Note that this test will fail if the WDD can't be reached
        # (in that case, we assume the id is valid)
        self.assertRaises(ValidationError, validate_wdd_player_id, 1)

    # validate_wdd_tournament_id()
    @tag('wdd')
    def test_validate_wdd_tournament_id_cascadia(self):
        self.assertIsNone(validate_wdd_tournament_id(1545))

    @tag('wdd')
    def test_validate_wdd_tournament_id_0(self):
        # 0 is known to be unused
        # Note that this test will fail if the WDD can't be reached
        # (in that case, we assume the id is valid)
        self.assertRaises(ValidationError, validate_wdd_tournament_id, 0)

    # wdd_url_to_tournament_id()
    def test_wdd_url_to_tournament_id_valid(self):
        self.assertEqual(wdd_url_to_tournament_id('https://world-diplomacy-database.com/php/results/tournament_class.php?id_tournament=1766'), 1766)

    def test_wdd_url_to_tournament_id_invalid(self):
        self.assertEqual(wdd_url_to_tournament_id('https://world-diplomacy-database.com/php/results/tournament_list.php'), 0)

    # wdd_img_to_country()
    def test_wdd_img_to_country(self):
        TEST_CASES = {
            '../../image/drapeau/ANG.GIF': 'ANG',
            '../../image/drapeau/USA.GIF': 'USA',
        }
        for img, country in TEST_CASES.items():
            with self.subTest(image=img):
                self.assertEqual(wdd_img_to_country(img), country)

    # power_name_to_wdd()
    def test_power_name_to_wdd(self):
        TEST_CASES = {
            GreatPower.objects.get(abbreviation='A'): '0AU',
            GreatPower.objects.get(abbreviation='E'): '0EN',
            GreatPower.objects.get(abbreviation='F'): '0FR',
            GreatPower.objects.get(abbreviation='G'): '0GE',
            GreatPower.objects.get(abbreviation='I'): '0IT',
            GreatPower.objects.get(abbreviation='R'): '0RU',
            GreatPower.objects.get(abbreviation='T'): '0TU',
        }
        for power, wdd in TEST_CASES.items():
            with self.subTest(power=power):
                self.assertEqual(power_name_to_wdd(power.name), wdd)

    # wdd_nation_to_country()
    def test_wdd_nation_to_country(self):
        TEST_CASES = {
            'ANG': 'GB',
            'CAN': 'CA',
            'ZW': 'ZW',
        }
        for wdd, code in TEST_CASES.items():
            with self.subTest(wdd_country_code=wdd):
                c = wdd_nation_to_country(wdd)
                self.assertEqual(c.code, code)

    def test_wdd_nation_to_country_yugoslavia(self):
        # WDD still has Yugoslavia as a country
        self.assertRaises(UnrecognisedCountry, wdd_nation_to_country, 'YOU')

    def test_wdd_nation_to_country_unknown(self):
        self.assertRaises(UnrecognisedCountry, wdd_nation_to_country, WDD_UNKNOWN_COUNTRY)

    # country_name_to_wdd()
    def test_country_name_to_wdd(self):
        TEST_CASES = {
            'Algeria': 'ALG',
            'Canada': 'CAN',
            'United Kingdom': 'ANG',
            'UK': WDD_UNKNOWN_COUNTRY,
            'Scotland': WDD_UNKNOWN_COUNTRY,
            'United States': 'USA',
            'USA': WDD_UNKNOWN_COUNTRY,
            'Zimbabwe': 'ZW',
        }
        for name, wdd in TEST_CASES.items():
            with self.subTest(country=name):
                self.assertEqual(country_name_to_wdd(name), wdd)

    # country_to_wdd()
    def test_country_to_wdd(self):
        TEST_CASES = {
            'AF': WDD_UNKNOWN_COUNTRY,
            'DZ': 'ALG',
            'CA': 'CAN',
            'GB': 'ANG',
            'GB-SCO': 'ANG',
            'US': 'USA',
            'ZW': 'ZW',
        }
        for code, wdd in TEST_CASES.items():
            c = Country(code)
            with self.subTest(country=c.name):
                self.assertEqual(country_to_wdd(c), wdd)
