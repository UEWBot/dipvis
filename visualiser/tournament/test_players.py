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

from django.test import TestCase, tag
from django.core.exceptions import ValidationError

from tournament.diplomacy import GreatPower
from tournament.players import Player, PlayerRanking
from tournament.players import validate_wdd_player_id, add_player_bg

CHRIS_BRAND_WDD_ID = 4173
MATT_SHIELDS_WDD_ID = 588
MATT_SUNDSTROM_WDD_ID = 8355
NATE_COCKERILL_WDD_ID = 5009
SPIROS_BOBETSIS_WDD_ID = 12304

class PlayerTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

    # validate_wdd_player_id()
    @tag('wdd')
    def test_validate_wdd_player_id_me(self):
        self.assertIsNone(validate_wdd_player_id(CHRIS_BRAND_WDD_ID))

    @tag('wdd')
    def test_validate_wdd_player_id_1(self):
        # 1 is known to be unused
        # Note that this test will fail if the WDD can't be reached
        # (in that case, we assume the id is valid)
        self.assertRaises(ValidationError, validate_wdd_player_id, 1)

    # TODO validate_wdd_tournament_id()

    @tag('wdd')
    # Player.wdd_name()
    def test_player_wdd_name(self):
        p = Player.objects.get(pk=1)
        # TODO Validate results
        p.wdd_name()

    def test_player_wdd_name_no_id(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        # TODO Validate results
        p.wdd_name()

    # Player.wdd_url()
    def test_player_wdd_url(self):
        p = Player.objects.get(pk=1)
        # TODO Validate results
        p.wdd_url()

    def test_player_wdd_url_no_id(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        # TODO Validate results
        p.wdd_url()

    @tag('slow', 'wdd')
    # Player.background()
    def test_player_background(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        add_player_bg(p)
        # TODO Validate results
        p.background()

    @tag('slow', 'wdd')
    def test_player_background_no_wins(self):
        # Spiros has yet to win a tournament
        p, created = Player.objects.get_or_create(first_name='Spiros',
                                                  last_name='Bobetsis',
                                                  wdd_player_id=SPIROS_BOBETSIS_WDD_ID)
        p.save()
        # TODO Validate results
        p.background()
        p.delete()

    @tag('slow', 'wdd')
    def test_player_background_mask(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        add_player_bg(p)
        self.assertEqual([], p.background(mask=0))

    @tag('slow', 'wdd')
    def test_player_background_with_power(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        add_player_bg(p)
        # TODO Validate results
        p.background(power=self.germany)

    @tag('slow', 'wdd')
    def test_player_background_td(self):
        # Matt has tournaments listings for tournaments when he was TD
        p, created = Player.objects.get_or_create(first_name='Matt',
                                                  last_name='Shields',
                                                  wdd_player_id=MATT_SHIELDS_WDD_ID)
        p.save()
        # TODO Validate results
        # WAC 10 he played Germany
        p.background(power=self.germany)
        p.delete()

    @tag('slow', 'wdd')
    def test_player_background_non_std(self):
        # Matt has tournaments listings for non-Standard games
        p, created = Player.objects.get_or_create(first_name='Matt',
                                                  last_name='Sundstrom',
                                                  wdd_player_id=MATT_SUNDSTROM_WDD_ID)
        p.save()
        # TODO Validate results
        # Windy City Weasels 2012 he played United Kingdom
        p.background()
        p.delete()

    @tag('slow', 'wdd')
    def test_player_background_non_std_2(self):
        # Nate has tournaments listings for non-Standard games,
        # where power names match Standard powers (France)
        p, created = Player.objects.get_or_create(first_name='Nate',
                                                  last_name='Cockerill',
                                                  wdd_player_id=NATE_COCKERILL_WDD_ID)
        p.save()
        # TODO Validate results
        # Windy City Weasels 2012 he played France
        p.background(power=self.france)
        p.delete()

    def test_player_background_unknown(self):
        p, created = Player.objects.get_or_create(first_name='Unknown', last_name='Player')
        add_player_bg(p)
        # TODO Validate results
        p.background()

    # TODO Player.save()

    @tag('slow', 'wdd')
    # PlayerRanking.national_str()
    def test_playerranking_national_str(self):
        p = Player.objects.first()
        add_player_bg(p)
        pr = PlayerRanking.objects.get(pk=1)
        # TODO Validate results
        pr.national_str()
