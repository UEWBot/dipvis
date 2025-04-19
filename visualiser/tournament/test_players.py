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

from datetime import date, datetime, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase, tag
from django.utils import timezone

from django_countries.fields import Country

from tournament.diplomacy.models.great_power import GreatPower
from tournament.models import DrawSecrecy
from tournament.models import Tournament, TournamentPlayer
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.players import Player, PlayerRanking, PlayerAward, PlayerTitle
from tournament.players import PlayerGameResult, PlayerTournamentRanking
from tournament.players import add_player_bg, position_str
from tournament.players import MASK_ALL_BG

CHRIS_BRAND_WDD_ID = 4173
MATT_SHIELDS_WDD_ID = 588
MATT_SUNDSTROM_WDD_ID = 8355
NATE_COCKERILL_WDD_ID = 5009
SPIROS_BOBETSIS_WDD_ID = 12304
CLAESAR_WEBDIP_WDD_ID = 13317
MELINDA_HOLLEY_WDD_ID = 5185

CHRIS_BRAND_WDR_ID = 7164


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

    # TODO player_picture_location()

    # TODO add_player_bg()
    def test_add_player_bg_wiki1(self):
        """Test adding PlayerTitles based on Wikipedia"""
        p = Player.objects.create(first_name = 'Brandon', last_name='Fogel')
        add_player_bg(p)
        pts = p.playertitle_set.all()
        self.assertEqual(len(pts), 2)
        for pt in pts:
            if pt.year == 2022:
                self.assertEqual(pt.title, 'Virtual Diplomacy League (VDL) Champion')
            elif pt.year == 2023:
                self.assertEqual(pt.title, 'DBNI Diplomat of the Year')
        # Cleanup
        p.delete()

    def test_add_player_bg_wiki2(self):
        """Test adding PlayerTitles based on Wikipedia"""
        p = Player.objects.create(first_name = 'Graham', last_name='Woodring')
        add_player_bg(p)
        pts = p.playertitle_set.all()
        self.assertEqual(len(pts), 1)
        for pt in pts:
            if pt.year == 2013:
                self.assertEqual(pt.title, 'North American Grand Prix Winner')
        # Cleanup
        p.delete()

    def test_add_player_bg_wiki3(self):
        """Test adding PlayerTitles based on Wikipedia"""
        p = Player.objects.create(first_name = 'Richard', last_name='Ackerlay')
        add_player_bg(p)
        pts = p.playertitle_set.all()
        self.assertEqual(len(pts), 1)
        for pt in pts:
            if pt.year == 1972:
                self.assertEqual(pt.title, 'North American Champion')
        # Cleanup
        p.delete()

    @tag('slow', 'wdd')
    def test_add_player_bg_wpe(self):
        """add_player_bg(include_wpe=True)"""
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        add_player_bg(p, include_wpe=True)
        ptrs = p.playertournamentranking_set.all()
        # TODO check results

    @tag('slow', 'wdd')
    def test_add_player_bg_wdd_places(self):
        """add_player_bg() with existing nationalities and location"""
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        self.assertEqual(p.location, '')
        self.assertEqual(len(p.nationalities), 0)
        p.nationalities = Country('CA')
        p.location = "The moon"
        p.save()
        add_player_bg(p)
        ptrs = p.playertournamentranking_set.all()
        # TODO check results
        # Cleanup
        p.location = ''
        p.nationalities = []
        p.save()

    @tag('slow', 'wdr')
    def test_add_player_bg_wdr_places(self):
        """add_player_bg() with existing nationalities and location"""
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        self.assertEqual(p.location, '')
        self.assertEqual(len(p.nationalities), 0)
        p.wdd_player_id = None
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.nationalities = Country('CA')
        p.location = "The moon"
        p.save()
        add_player_bg(p)
        ptrs = p.playertournamentranking_set.all()
        # TODO check results
        # Cleanup
        p.wdd_player_id = CHRIS_BRAND_WDD_ID
        p.wdr_player_id = None
        p.location = ''
        p.nationalities = []
        p.save()

    # position_str()
    def test_position_str_first(self):
        tests = {1: '1st',
                 2: '2nd',
                 3: '3rd',
                 4: '4th',
                 5: '5th',
                 6: '6th',
                 7: '7th',
                 8: '8th',
                 9: '9th',
                 10: '10th',
                 11: '11th',
                 12: '12th',
                 13: '13th',
                 14: '14th',
                 21: '21st',
                 22: '22nd',
                 23: '23rd',
                 24: '24th',
                 99: '99th',
                 100: '100th',
                 101: '101st',
                }
        for k,v in tests.items():
            with self.subTest(k):
                self.assertEqual(position_str(k), v)

    # TODO Player.sortable_str()

    # Player.background_updated()
    @tag('slow', 'wdd')
    def test_player_background_updated(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        start = datetime.now(timezone.utc)
        add_player_bg(p)
        end = datetime.now(timezone.utc)
        updated = p.background_updated()
        self.assertLess(start, updated)
        self.assertLess(updated, end)

    def test_player_background_updated_none(self):
        p, created = Player.objects.get_or_create(first_name='Unknown', last_name='Player')
        self.assertEqual(None, p.background_updated())

    # Player.wdd_url()
    def test_player_wdd_url(self):
        p = Player.objects.first()
        # TODO Validate results
        p.wdd_url()

    def test_player_wdd_url_no_id(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        # TODO Validate results
        p.wdd_url()

    # Player.wdr_url()
    def test_player_wdr_url(self):
        p = Player.objects.create(first_name='John', last_name='Smith', wdr_player_id=69)
        # TODO Validate results
        p.wdr_url()

    def test_player_wdr_url_no_id(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        # TODO Validate results
        p.wdr_url()

    # Player.wdd_firstname_lastname()
    @tag('slow', 'wdd')
    def test_player_wdd_firstname_lastname(self):
        p = Player.objects.first()
        # TODO Validate results
        p.wdd_firstname_lastname()

    def test_player_wdd_firstname_lastname_no_id(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        name = p.wdd_firstname_lastname()
        self.assertEqual(name[0], 'John')
        self.assertEqual(name[1], 'Smith')

    # Player.wdr_name()
    @tag('wdr')
    def test_player_wdr_name(self):
        p = Player.objects.create(first_name='John', last_name='Smith', wdr_player_id=CHRIS_BRAND_WDR_ID)
        self.assertEqual(p.wdr_name(), 'Chris Brand')

    # Player.tournamentplayers()
    def test_player_tournamentplayers(self):
        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + timedelta(hours=24),
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET,
                                       is_published=True)
        t1.save()
        t2 = Tournament.objects.create(name='t2',
                                       start_date=today,
                                       end_date=today + timedelta(hours=24),
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET,
                                       is_published=False)
        t2.save()
        # Now we need a player that played in both tournaments
        p = Player.objects.create(first_name='Joe',
                                  last_name='Schmoe')
        p.save()
        tp1 = TournamentPlayer.objects.create(tournament=t1,
                                              player=p)
        tp1.save()
        tp2 = TournamentPlayer.objects.create(tournament=t2,
                                              player=p)
        tp2.save()
        self.assertEqual(1, p.tournamentplayers(including_unpublished=False).count())
        self.assertEqual(2, p.tournamentplayers(including_unpublished=True).count())
        tp2.delete()
        tp1.delete()
        p.delete()
        t2.delete()
        t1.delete()

    # Player.background()
    @tag('slow', 'wdd')
    def test_player_background_wdd(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        self.assertIsNone(p.wdr_player_id)
        add_player_bg(p)
        # TODO Validate results
        p.background()

    @tag('wdr')
    def test_player_background_wdr(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        self.assertIsNone(p.wdr_player_id)
        p.wdd_player_id = None
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        add_player_bg(p)
        # TODO Validate results
        p.background()
        p.background()
        # Cleanup
        p.wdr_player_id = None
        p.save()

    @tag('slow', 'wdr', 'wdd')
    def test_player_background_wdd_and_wdr(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        self.assertIsNone(p.wdr_player_id)
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        add_player_bg(p)
        # TODO Validate results
        p.background()
        # Cleanup
        p.wdr_player_id = None
        p.save()

    @tag('slow', 'wdd')
    def test_player_background_no_wins(self):
        # Spiros has yet to win a tournament
        p, created = Player.objects.get_or_create(first_name='Spiros',
                                                  last_name='Bobetsis',
                                                  wdd_player_id=SPIROS_BOBETSIS_WDD_ID)
        # TODO Validate results
        p.background()

    @tag('slow', 'wdd')
    def test_player_background_invalid_date(self):
        p, created = Player.objects.get_or_create(first_name='Claesar',
                                                  last_name='Webdip',
                                                  wdd_player_id=CLAESAR_WEBDIP_WDD_ID)
        # TODO Validate results
        p.background()

    @tag('slow', 'wdd')
    def test_player_background_mask(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        add_player_bg(p)
        self.assertEqual([], p.background(mask=0))

    @tag('slow', 'wdd')
    def test_player_background_mask_2(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        add_player_bg(p)
        # Test each mask bit individually
        mask = 1
        while mask <= MASK_ALL_BG:
            with self.subTest(mask=mask):
                # TODO Validate results
                p.background(mask=mask)
            mask *= 2

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
        # TODO Validate results
        # WAC 10 he played Germany
        p.background(power=self.germany)

    @tag('slow', 'wdd')
    def test_player_background_non_std(self):
        # Matt has tournaments listings for non-Standard games
        p, created = Player.objects.get_or_create(first_name='Matt',
                                                  last_name='Sundstrom',
                                                  wdd_player_id=MATT_SUNDSTROM_WDD_ID)
        # TODO Validate results
        # Windy City Weasels 2012 he played United Kingdom
        p.background()

    @tag('slow', 'wdd')
    def test_player_background_non_std_2(self):
        # Nate has tournaments listings for non-Standard games,
        # where power names match Standard powers (France)
        p, created = Player.objects.get_or_create(first_name='Nate',
                                                  last_name='Cockerill',
                                                  wdd_player_id=NATE_COCKERILL_WDD_ID)
        # TODO Validate results
        # Windy City Weasels 2012 he played France
        p.background(power=self.france)

    @tag('slow', 'wdd')
    def test_player_background_non_std_3(self):
        # Melinda has games listed with no ranking (n.c)
        p, created = Player.objects.get_or_create(first_name='Melinda',
                                                  last_name='Holley',
                                                  wdd_player_id=MELINDA_HOLLEY_WDD_ID)
        # TODO Validate results
        p.background()

    def test_player_background_unknown(self):
        p, created = Player.objects.get_or_create(first_name='Unknown', last_name='Player')
        add_player_bg(p)
        # TODO Validate results
        p.background()

    def test_player_background_no_sc_count(self):
        p = Player(first_name='Joe',
                   last_name='Bloggs')
        p.save()
        # No final_sc_count (or other optional fields)
        pgr = PlayerGameResult(tournament_name='Best Tournament',
                               round_number=1,
                               game_number=1,
                               player=p,
                               power=self.austria,
                               date=date.today(),
                               position=2)
        pgr.save()
        # TODO validate results
        p.background()
        pgr.delete()
        p.delete()

    def test_player_background_game_count(self):
        p = Player(first_name='Joe',
                   last_name='Bloggs')
        p.save()
        # No final_sc_count (or other optional fields)
        pgr = PlayerGameResult(tournament_name='Best Tournament',
                               round_number=1,
                               game_number=1,
                               player=p,
                               power=self.austria,
                               date=date.today(),
                               position=2)
        pgr.save()
        bg = p.background()
        self.assertIn('Joe Bloggs has played 1 tournament game.', bg)
        pgr.delete()
        p.delete()

    # Player.save()
    @tag('slow', 'wdd')
    def test_player_save(self):
        p = Player.objects.first()
        wdd_id = p.wdd_player_id
        add_player_bg(p)
        self.assertEqual(53, p.playertournamentranking_set.count())
        p.wdd_player_id = MELINDA_HOLLEY_WDD_ID
        p.save(update_fields=['wdd_player_id'])
        # Change in wdd_player_id should trigger clearing of background
        self.assertEqual(0, p.playertournamentranking_set.count())
        # Clean up
        p.wdd_player_id = wdd_id
        p.save(update_fields=['wdd_player_id'])

    # Player.get_absolute_url()
    def test_player_get_absolute_url(self):
        p = Player.objects.first()
        p.get_absolute_url()

    # PlayerTournamentRanking
    # PlayerTournamentRanking.wdd_url()
    @tag('slow', 'wdd')
    def test_playertournamentranking_wdd_url(self):
        p = Player.objects.first()
        add_player_bg(p)
        ptr = PlayerTournamentRanking.objects.first()
        url = ptr.wdd_url()
        # TODO verify result

    # PlayerTournamentRanking.wdr_url()
    @tag('slow', 'wdr')
    def test_playertournamentranking_wdr_url(self):
        p = Player.objects.first()
        wdd_id = p.wdd_player_id
        p.wdd_player_id = None
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        add_player_bg(p)
        ptr = PlayerTournamentRanking.objects.first()
        url = ptr.wdr_url()
        # TODO verify result
        # Cleanup
        p.wdd_player_id = wdd_id
        p.wdr_player_id = None
        p.save()

    # PlayerTournamentRanking.__str__()
    @tag('slow', 'wdd')
    def test_playertournamentranking_str(self):
        p = Player.objects.first()
        add_player_bg(p)
        ptr = PlayerTournamentRanking.objects.first()
        p_str = str(ptr)
        # We expect to find player name and tournament name
        self.assertIn(ptr.player.first_name, p_str)
        self.assertIn(ptr.player.last_name, p_str)
        self.assertIn(ptr.tournament, p_str)

    # PlayerTitle
    # PlayerTitle.__str__()
    def test_playertitle_str(self):
        pt = PlayerTitle(player=Player.objects.first(),
                         title='Dogwasher of the Year',
                         year=1900)
        p_str = str(pt)
        # We expect to find player name, title, and year
        self.assertIn(pt.player.first_name, p_str)
        self.assertIn(pt.player.last_name, p_str)
        self.assertIn(pt.title, p_str)
        self.assertIn(str(pt.year), p_str)

    # PlayerGameResult
    # PlayerGameResult.for_same_game()
    def test_playergameresult_same(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(tournament_name='Best Tournament',
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                date=date.today(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name=pgr1.tournament_name,
                                round_number=pgr1.round_number,
                                game_number=pgr1.game_number,
                                player=p2,
                                power=self.russia,
                                date=pgr1.date,
                                position=4)
        self.assertTrue(pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_tournament(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(tournament_name='Best Tournament',
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                date=date.today(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name='Worst Tournament',
                                round_number=pgr1.round_number,
                                game_number=pgr1.game_number,
                                player=p2,
                                power=self.russia,
                                date=pgr1.date,
                                position=4)
        self.assertFalse(pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_round(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(tournament_name='Best Tournament',
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                date=date.today(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name=pgr1.tournament_name,
                                round_number=2,
                                game_number=1,
                                player=p2,
                                power=self.russia,
                                date=pgr1.date,
                                position=4)
        self.assertFalse(pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_game(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(tournament_name='Best Tournament',
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                date=date.today(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name=pgr1.tournament_name,
                                round_number=1,
                                game_number=2,
                                player=p2,
                                power=self.russia,
                                date=pgr1.date,
                                position=4)
        self.assertFalse(pgr1.for_same_game(pgr2))

    def test_playergameresult_same_wrong_date(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(tournament_name='Best Tournament',
                                round_number=1,
                                game_number=1,
                                player=p1,
                                power=self.austria,
                                date=date.today(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name=pgr1.tournament_name,
                                round_number=pgr1.round_number,
                                game_number=pgr1.game_number,
                                player=p2,
                                power=self.russia,
                                date=date.today() + timedelta(hours=24),
                                position=4)
        self.assertFalse(pgr1.for_same_game(pgr2))

    # PlayerGameResult.wdd_url()
    @tag('slow', 'wdd')
    def test_playergameresult_wdd_url(self):
        p = Player.objects.first()
        add_player_bg(p)
        pgr = PlayerGameResult.objects.first()
        url = pgr.wdd_url()
        # TODO verify result

    # PlayerGameResult.wdr_url()
    @tag('slow', 'wdr')
    def test_playergameresult_wdr_url(self):
        p = Player.objects.first()
        wdd_id = p.wdd_player_id
        p.wdd_player_id = None
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        add_player_bg(p)
        pgr = PlayerGameResult.objects.first()
        url = pgr.wdr_url()
        # TODO verify result
        # Cleanup
        p.wdd_player_id = wdd_id
        p.wdr_player_id = None
        p.save()

    # PlayerGameResult.__str__()
    @tag('slow', 'wdd')
    def test_playergameresult_str(self):
        p = Player.objects.first()
        add_player_bg(p)
        pgr = PlayerGameResult.objects.first()
        p_str = str(pgr)
        # We expect to find player name and power name
        self.assertIn(pgr.player.first_name, p_str)
        self.assertIn(pgr.player.last_name, p_str)
        self.assertIn(pgr.power.name, p_str)

    # PlayerAward
    # PlayerAward.wdd_url()
    @tag('slow', 'wdd')
    def test_playeraward_wdd_url_power(self):
        p = Player.objects.first()
        add_player_bg(p)
        pa = PlayerAward.objects.exclude(power=None).first()
        url = pa.wdd_url()
        # TODO verify result

    @tag('slow', 'wdd')
    def test_playeraward_wdd_url_no_power(self):
        p = Player.objects.first()
        add_player_bg(p)
        pa = PlayerAward.objects.filter(power=None).first()
        url = pa.wdd_url()
        # TODO verify result

    # PlayerAward.wdr_url()
    @tag('slow', 'wdr')
    def test_playeraward_wdr_url(self):
        p = Player.objects.first()
        wdd_id = p.wdd_player_id
        p.wdd_player_id = None
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        add_player_bg(p)
        pa = PlayerAward.objects.exclude(power=None).first()
        url = pa.wdr_url()
        # TODO verify result
        # Cleanup
        p.wdd_player_id = wdd_id
        p.wdr_player_id = None
        p.save()

    # PlayerAward.__str__()
    @tag('slow', 'wdd')
    def test_playeraward_str(self):
        p = Player.objects.first()
        add_player_bg(p)
        pa = PlayerAward.objects.first()
        p_str = str(pa)
        # We expect to find player name, award name, and tournament name
        self.assertIn(pa.player.first_name, p_str)
        self.assertIn(pa.player.last_name, p_str)
        self.assertIn(pa.name, p_str)
        self.assertIn(pa.tournament, p_str)

    # PlayerRanking

    # PlayerRanking.wdd_url()
    @tag('slow', 'wdd')
    def test_playerranking_wdd_url_wpe(self):
        p = Player.objects.first()
        add_player_bg(p)
        pr = PlayerRanking.objects.filter(system__contains='World').first()
        url = pr.wdd_url()
        # TODO Validate results

    @tag('slow', 'wdd')
    def test_playerranking_wdd_url_dip_pouch(self):
        p = Player.objects.first()
        add_player_bg(p)
        pr = PlayerRanking.objects.filter(system__contains='Pouch').first()
        url = pr.wdd_url()
        # TODO Validate results

    @tag('slow', 'wdd')
    def test_playerranking_wdd_url_sdr(self):
        # Not many players have SDR ratings
        p = Player.objects.create(first_name='Per',
                                  last_name='Norman',
                                  wdd_player_id=2199)
        add_player_bg(p)
        pr = PlayerRanking.objects.filter(system__contains='SDR').first()
        url = pr.wdd_url()
        # TODO Validate results

    # PlayerRanking.wdr_url()
    @tag('slow', 'wdr')
    def test_playerranking_wdr_url_wpe(self):
        p = Player.objects.first()
        wdd_id = p.wdd_player_id
        p.wdd_player_id = None
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        add_player_bg(p)
        pr = PlayerRanking.objects.filter(system='WPE7').first()
        url = pr.wdr_url()
        # TODO Validate results
        # Cleanup
        p.wdd_player_id = wdd_id
        p.wdr_player_id = None
        p.save()

    # PlayerRanking.national_str()
    @tag('slow', 'wdd')
    def test_playerranking_national_str(self):
        p = Player.objects.first()
        add_player_bg(p)
        pr = PlayerRanking.objects.first()
        # TODO Validate results
        pr.national_str()

    # PlayerRanking.__str__()
    @tag('slow', 'wdd')
    def test_playerranking_str(self):
        p = Player.objects.first()
        add_player_bg(p)
        pr = PlayerRanking.objects.first()
        # TODO Validate results
        str(pr)
