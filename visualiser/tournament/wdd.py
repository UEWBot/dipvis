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

"""
WDD primitives for the Diplomacy Tournament Visualiser.
"""

import re
import requests

from django_countries.fields import Country

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

WDD_NETLOC = 'world-diplomacy-database.com'
WDD_BASE_RESULTS_PATH = 'php/results/'
WDD_BASE_RANKING_PATH = 'php/ranking/'
WDD_BASE_RESULTS_URL = 'https://' + WDD_NETLOC + '/' + WDD_BASE_RESULTS_PATH
WDD_BASE_RANKING_URL = 'https://' + WDD_NETLOC + '/' + WDD_BASE_RANKING_PATH

WDD_MAX_ROUNDS = 8
WDD_MAX_AWARDS = 12
WDD_MAX_YEAR = 20


# WDD uses a mix of 3-letter abbreviations of the French names for countries and 2-letter ISO codes.
# These are the country codes used by the WDD.
# Scraped 21 Feb 2024 from https://world-diplomacy-database.com/php/admin/affiche_drapeaux_dispo.php
WDD_COUNTRY_NAME = {'ALG': 'Algeria', 'AD': 'Andorra', 'AO': 'Angola', 'ARG': 'Argentina', 'AUS': 'Australia', 'AUT': 'Austria', 'BLR': 'Belarus', 'BEL': 'Belgium', 'BEN': 'Benin', 'BOT': 'Botswana', 'BRE': 'Brazil', 'BF': 'Burkina Faso', 'BI': 'Burundi', 'CAM': 'Cameroon', 'CAN': 'Canada', 'CV': 'Cape Verde', 'CF': 'Central African Republic', 'TD': 'Chad', 'CHI': 'China', 'COM': 'Comoros', 'CZE': 'Czech republic', 'RDC': 'Democratic Republic of Congo', 'DAN': 'Denmark', 'DJI': 'Djibouti', 'EGY': 'Egypt', 'GQ': 'Equatorial Guinea', 'ER': 'Eritrea', 'ETH': 'Ethiopia', 'FIN': 'Finland', 'FRA': 'France', 'GAB': 'Gabon', 'GM': 'Gambia', 'GEO': 'Georgia', 'ALL': 'Germany', 'GH': 'Ghana', 'GRE': 'Greece', 'GU': 'Guinea', 'GW': 'Guinea-Bissau', 'HON': 'Hungary', 'ISL': 'Iceland', 'IN': 'India', 'IRN': 'Iran', 'IRL': 'Ireland', 'ISR': 'Israel', 'ITA': 'Italy', 'CI': 'Ivory Coast', 'JAP': 'Japan', 'KAZ': 'Kazakhstan', 'KEN': 'Kenya', 'LB': 'Lebanon', 'LS': 'Lesotho', 'LR': 'Liberia', 'LY': 'Libya', 'LI': 'Liechtenstein', 'LUX': 'Luxembourg', 'MG': 'Madagascar', 'MW': 'Malawi', 'ML': 'Mali', 'MT': 'Malta', 'MR': 'Mauritania', 'MU': 'Mauritius', 'MEX': 'Mexico', 'MOL': 'Moldova', 'MON': 'Monaco', 'MAR': 'Morocco', 'MZ': 'Mozambique', 'NA': 'Namibia', 'HOL': 'Netherlands', 'NZE': 'New Zealand', 'NE': 'Niger', 'NG': 'Nigeria', 'NGE': 'Norway', 'PAK': 'Pakistan', 'PHI': 'Philippines', 'POL': 'Poland', 'POR': 'Portugal', 'CG': 'Republic of Congo', 'ROU': 'Romania', 'RUS': 'Russia', 'RW': 'Rwanda', 'SM': 'San Marino', 'ST': 'Sao Tome and Principe', 'SN': 'Senegal', 'SEY': 'Seychelles', 'SL': 'Sierra Leone', 'SG': 'Singapore', 'SO': 'Somalia', 'SA': 'South Africa', 'COR': 'South Korea', 'ESP': 'Spain', 'SD': 'Sudan', 'SZ': 'Swaziland', 'SUE': 'Sweden', 'SUI': 'Switzerland', 'SY': 'Syria', 'TJ': 'Tajikistan', 'TZ': 'Tanzania', 'THA': 'Thailand', 'TG': 'Togo', 'TUN': 'Tunisia', 'TUR': 'Turkey', 'UG': 'Uganda', 'UKR': 'Ukraine', 'ANG': 'United Kingdom', 'USA': 'United States', 'VN': 'Vietnam', 'YOU': 'Yugoslavia', 'ZM': 'Zambia', 'ZW': 'Zimbabwe'}
WDD_BLANK_COUNTRY = 'YYY' # displays as an all-white flag
WDD_UNKNOWN_COUNTRY = 'ZZZ' # displays as "n.c."

# Map the country codes used by WDD to ISO 366 alpha-2 codes. Derived from the above
WDD_COUNTRY_TO_ISO_CODE = {
    'ALG': 'DZ',
    'AD': 'AD',
    'AO': 'AO',
    'ARG': 'AR',
    'AUS': 'AU',
    'AUT': 'AT',
    'BLR': 'BY',
    'BEL': 'BE',
    'BEN': 'BJ',
    'BOT': 'BW',
    'BRE': 'BR',
    'BF': 'BF',
    'BI': 'BI',
    'CAM': 'CM',
    'CAN': 'CA',
    'CV': 'CV',
    'CF': 'CF',
    'TD': 'TD',
    'CHI': 'CN',
    'COM': 'KM',
    'CZE': 'CZ',
    'RDC': 'CD',
    'DAN': 'DK',
    'DJI': 'DJ',
    'EGY': 'EG',
    'GQ': 'GQ',
    'ER': 'ER',
    'ETH': 'ET',
    'FIN': 'FI',
    'FRA': 'FR',
    'GAB': 'GA',
    'GM': 'GM',
    'GEO': 'GE',
    'ALL': 'DE',
    'GH': 'GH',
    'GRE': 'GR',
    'GU': 'GN',
    'GW': 'GW',
    'HON': 'HU',
    'ISL': 'IS',
    'IN': 'IN',
    'IRN': 'IR',
    'IRL': 'IE',
    'ISR': 'IL',
    'ITA': 'IT',
    'CI': 'CI',
    'JAP': 'JP',
    'KAZ': 'KZ',
    'KEN': 'KE',
    'LB': 'LB',
    'LS': 'LS',
    'LR': 'LR',
    'LY': 'LY',
    'LI': 'LI',
    'LUX': 'LU',
    'MG': 'MG',
    'MW': 'MW',
    'ML': 'ML',
    'MT': 'MT',
    'MR': 'MR',
    'MU': 'MU',
    'MEX': 'MX',
    'MOL': 'MD',
    'MON': 'MC',
    'MAR': 'MA',
    'MZ': 'MZ',
    'NA': 'NA',
    'HOL': 'NL',
    'NZE': 'NZ',
    'NE': 'NE',
    'NG': 'NG',
    'NGE': 'NO',
    'PAK': 'PK',
    'PHI': 'PH',
    'POL': 'PL',
    'POR': 'PT',
    'CG': 'CG',
    'ROU': 'RO',
    'RUS': 'RU',
    'RW': 'RW',
    'SM': 'SM',
    'ST': 'ST',
    'SN': 'SN',
    'SEY': 'SC',
    'SL': 'SL',
    'SG': 'SG',
    'SO': 'SO',
    'SA': 'ZA',
    'COR': 'KR',
    'ESP': 'ES',
    'SD': 'SD',
    'SZ': 'SZ',
    'SUE': 'SE',
    'SUI': 'CH',
    'SY': 'SY',
    'TJ': 'TJ',
    'TZ': 'TZ',
    'THA': 'TH',
    'TG': 'TG',
    'TUN': 'TN',
    'TUR': 'TR',
    'UG': 'UG',
    'UKR': 'UA',
    'ANG': 'GB',
    'USA': 'US',
    'VN': 'VN',
#    'YOU': 'Yugoslavia',
    'ZM': 'ZM',
    'ZW': 'ZW',
}


def _validate_wdd_id(url, param, value):
    """
    Checks the validity of a WDD id
    """
    try:
        r = requests.head(url,
                          params={param: value},
                          allow_redirects=False,
                          timeout=1.0)
    except requests.exceptions.Timeout:
        # Assume the id is ok
        return
    if r.status_code != requests.codes.ok:
        raise ValidationError(_(u'%(value)d is not a valid WDD %(param)s'),
                              params={'value': value,
                                      'param': param})


def validate_wdd_player_id(value):
    """
    Checks a WDD player id
    """
    url = WDD_BASE_RESULTS_URL + 'player_fiche.php'
    _validate_wdd_id(url, 'id_player', value)


def validate_wdd_tournament_id(value):
    """
    Checks a WDD tournament id
    """
    url = WDD_BASE_RESULTS_URL + 'tournament_class.php'
    _validate_wdd_id(url, 'id_tournament', value)


def wdd_url_to_tournament_id(url):
    """
    Extracts the tournament id from a WDD tournament URL
    """
    # The numbers at the end of the string
    m = re.search(r'(\d+)$', url)
    if m:
        return int(m.group(1))
    return 0


class UnrecognisedCountry(Exception):
    """The specified country is not recognised"""
    pass


def wdd_img_to_country(img):
    """
    Convert a WDD flag image name to a WDD country code (key to WDD_COUNTRY_NAME)
    """
    filename = img.rpartition('/')[2]
    return filename[:-4]


def power_name_to_wdd(name):
    """Map a power name to a WDD country code"""
    # 0 for variant (standard), plus first two letters of the country name (in English)
    return f'0{name[0:2].upper()}'


def wdd_nation_to_country(country_code):
    """
    Map a (real world) country code from the WDD to a django_countries.Country.

    Can raise UnrecognisedCountry.
    """
    try:
        c = Country(WDD_COUNTRY_TO_ISO_CODE[country_code])
    except KeyError as e:
        raise UnrecognisedCountry(country_code) from e
    assert len(c) > 0
    return c


def country_name_to_wdd(name):
    """
    Map a country name to a WDD (real world) country code.

    Returns WDD_UNKNOWN_COUNTRY is the country is not recognised by the WDD.
    """
    try:
        key = next(key for key, value in WDD_COUNTRY_NAME.items() if value == name)
    except StopIteration:
        # Not a country recognised by the WDD
        return WDD_UNKNOWN_COUNTRY
    # Return the 2- or 3-letter code used by the WDD for this country
    return key


def country_to_wdd(country):
    """
    Map a Country to a WDD (real world) country code.

    Returns WDD_UNKNOWN_COUNTRY is the country is not recognised by the WDD.
    """
    try:
        key = next(key for key, value in WDD_COUNTRY_TO_ISO_CODE.items() if country.code.startswith(value))
    except StopIteration:
        # Not a country recognised by the WDD
        return WDD_UNKNOWN_COUNTRY
    # Return the 2- or 3-letter code used by the WDD for this country
    return key
