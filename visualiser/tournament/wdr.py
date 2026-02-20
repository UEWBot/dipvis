# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2025 Chris Brand
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
WDR primitives for the Diplomacy Tournament Visualiser.
"""

import requests

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from tournament.diplomacy.models.great_power import GreatPower


WDR_NETLOC = 'www.world-diplomacy-reference.com'
WDR_BASE_URL = 'https://' + WDR_NETLOC + '/'


def _validate_wdr_id(path, param, value):
    """
    Checks the validity of a WDR id
    """
    url = f'{WDR_BASE_URL}{path}/{value}'
    try:
        r = requests.head(url,
                          headers={'User-Agent': settings.USER_AGENT},
                          allow_redirects=False,
                          timeout=1.0)
    except requests.exceptions.Timeout:
        # Assume the id is ok
        return
    if r.status_code != requests.codes.ok:
        raise ValidationError(_(u'%(value)d is not a valid WDR %(param)s'),
                              params={'value': value,
                                      'param': param})


def validate_wdr_player_id(value):
    """
    Checks a WDR player id
    """
    _validate_wdr_id('players', 'player', value)


def validate_wdr_tournament_id(value):
    """
    Checks a WDR tournament id
    """
    _validate_wdr_id('tournaments', 'tournament', value)


def wdr_tournament_as_json(wdr_tournament_id):
    """
    Uses the WDR API to read the details of the specified tournament as JSON
    """
    url = WDR_BASE_URL + f'api/v1/tournaments/{wdr_tournament_id}'
    page = requests.get(url,
                        headers={'User-Agent': settings.USER_AGENT,
                                 'Accept': 'application/json',
                                 'Accept-Encoding': 'gzip'},
                        timeout=4.0)
    return page.json()


_GPCache = {}


def wdr_power_name_to_greatpower(name):
    """Map a WDR power name to a GreatPower object"""
    if len(_GPCache) == 0:
        _GPCache["Austria"] = GreatPower.objects.get(abbreviation="A")
        _GPCache["England"] = GreatPower.objects.get(abbreviation="E")
        _GPCache["France"] = GreatPower.objects.get(abbreviation="F")
        _GPCache["Germany"] = GreatPower.objects.get(abbreviation="G")
        _GPCache["Italy"] = GreatPower.objects.get(abbreviation="I")
        _GPCache["Russia"] = GreatPower.objects.get(abbreviation="R")
        _GPCache["Turkey"] = GreatPower.objects.get(abbreviation="T")
    return _GPCache[name]
