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
from tournament.players import Player, PlayerRanking, PlayerAward, PlayerTitle, WDDPlayer
from tournament.players import PlayerGameResult, PlayerTournamentRanking
from tournament.players import player_picture_location, add_player_bg, position_str
from tournament.players import MASK_ALL_BG

CHRIS_BRAND_WDD_ID = 4173
MATT_SHIELDS_WDD_ID = 588
MATT_SUNDSTROM_WDD_ID = 8355
NATE_COCKERILL_WDD_ID = 5009
SPIROS_BOBETSIS_WDD_ID = 12304
CLAESAR_WEBDIP_WDD_ID = 13317
MELINDA_HOLLEY_WDD_ID = 5185

CHRIS_BRAND_WDR_ID = 7164


class FunctionTests(TestCase):
    """Test functions that are not class methods"""
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

    # player_picture_location()
    def test_player_picture_location(self):
        res = player_picture_location(None, 'pretty_boy.jpg')
        # TODO validate result

    # add_player_bg()
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
    def test_add_player_bg_wdd(self):
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        add_player_bg(p)
        # TODO Validate results

    @tag('wdr', 'wdd')
    def test_add_player_bg_wdr(self):
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        wdd.delete()
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        add_player_bg(p)
        # TODO Validate results
        # Cleanup
        WDDPlayer.objects.create(wdd_player_id=CHRIS_BRAND_WDD_ID,
                                 player=p)
        p.wdr_player_id = None
        p.save()

    @tag('slow', 'wdr', 'wdd')
    def test_add_player_bg_wdd_and_wdr(self):
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        add_player_bg(p)
        # TODO Validate results
        # Cleanup
        p.wdr_player_id = None
        p.save()

    @tag('slow', 'wdd')
    def test_add_player_bg_no_podiums(self):
        # Spiros has no podium finishes
        p = Player.objects.create(first_name='Spiros',
                                  last_name='Bobetsis')
        wdd = WDDPlayer.objects.create(player=p,
                                       wdd_player_id=SPIROS_BOBETSIS_WDD_ID)
        add_player_bg(p)
        # Validate results
        ptrs = p.playertournamentranking_set.all()
        self.assertEqual(2, ptrs.count())
        # Cleanup
        p.delete()

    @tag('slow', 'wdd')
    def test_add_player_bg_with_podiums(self):
        # Matt has podium finishes in 2008
        p = Player.objects.create(first_name='Matt',
                                  last_name='Shields')
        wdd = WDDPlayer.objects.create(player=p,
                                       wdd_player_id=MATT_SHIELDS_WDD_ID)
        add_player_bg(p)
        # Validate results (mostly check that no tournaments get double-counted)
        ptrs = p.playertournamentranking_set.filter(year=2008)
        self.assertEqual(4, ptrs.count())
        # Cleanup
        p.delete()

    # TODO Test handling of invalid dates (PlayerTournamentRanking and PlayerAward)

    @tag('slow', 'wdd')
    def test_add_player_bg_td(self):
        # Matt has tournaments listings for tournaments when he was TD
        p = Player.objects.create(first_name='Matt',
                                  last_name='Shields')
        wdd = WDDPlayer.objects.create(player=p,
                                       wdd_player_id=MATT_SHIELDS_WDD_ID)
        add_player_bg(p)
        # Validate results
        # WAC 10 he played Germany and Turkey
        pgrs = p.playergameresult_set.filter(tournament_name='WAC 10 2013')
        self.assertNotEqual(0, pgrs.count())
        # Cleanup
        p.delete()

    # TODO Test filtering out variant games
    #      There is a variant game in the Windy City Weasels 2012 league,
    #      but we only look at tournament games

    @tag('slow', 'wdd')
    def test_add_player_bg_unranked(self):
        # Melinda has games listed with no ranking (n.c)
        p = Player.objects.create(first_name='Melinda',
                                  last_name='Holley')
        wdd = WDDPlayer.objects.create(player=p,
                                       wdd_player_id=MELINDA_HOLLEY_WDD_ID)
        add_player_bg(p)
        # Validate results
        pgrs = p.playergameresult_set.filter(tournament_name__contains='DipCon')
        self.assertNotEqual(0, pgrs.count())
        pgrs = pgrs.filter(tournament_name__contains='DipCon 27')
        self.assertEqual(0, pgrs.count())
        # Cleanup
        p.delete()

    def test_add_player_bg_unknown(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        add_player_bg(p)
        # Validate results
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        # Cleanup
        p.delete()

    @tag('slow', 'wdd')
    def test_add_player_bg_wpe(self):
        """add_player_bg(include_wpe=True)"""
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertEqual(0, p.playertournamentranking_set.count())
        add_player_bg(wdd.player, include_wpe=True)
        # check results
        ptrs = p.playertournamentranking_set.filter(wpe_score__isnull=False)
        self.assertNotEqual(0, ptrs.count())

    @tag('slow', 'wdd')
    def test_add_player_bg_wdd_places_nop(self):
        """add_player_bg() from WDD with existing nationalities and location"""
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        self.assertEqual(p.location, '')
        self.assertEqual(len(p.nationalities), 0)
        p.nationalities = Country('US')
        p.location = "The moon"
        p.save()
        add_player_bg(p)
        # check results - existing values should be left intact
        p.refresh_from_db()
        self.assertEqual(p.nationalities, [Country('US')])
        self.assertEqual(p.location, 'The moon')
        # Cleanup
        p.location = ''
        p.nationalities = []
        p.save()

    @tag('slow', 'wdd')
    def test_add_player_bg_wdd_nationality(self):
        """add_player_bg() from WDD without existing nationalities and location"""
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        self.assertEqual(p.location, '')
        self.assertEqual(len(p.nationalities), 0)
        add_player_bg(p)
        # check results - values from WDD should be used
        p.refresh_from_db()
        self.assertEqual(p.nationalities, [Country('CA')])
        # Note that WDDBackground.location() currently always returns ''
        self.assertEqual(p.location, '')
        # Cleanup
        p.location = ''
        p.nationalities = []
        p.save()

    @tag('slow', 'wdr', 'wdd')
    def test_add_player_bg_wdr_places_nop(self):
        """add_player_bg() from WDR with existing nationalities and location"""
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        self.assertEqual(p.location, '')
        self.assertEqual(len(p.nationalities), 0)
        wdd.delete()
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.nationalities = Country('US')
        p.location = "The moon"
        p.save()
        add_player_bg(p)
        # check results - existing values should be left intact
        p.refresh_from_db()
        self.assertEqual(p.nationalities, [Country('US')])
        self.assertEqual(p.location, 'The moon')
        # Cleanup
        WDDPlayer.objects.create(player=p,
                                 wdd_player_id=CHRIS_BRAND_WDD_ID)
        p.wdr_player_id = None
        p.location = ''
        p.nationalities = []
        p.save()

    @tag('slow', 'wdr', 'wdd')
    def test_add_player_bg_wdr_places(self):
        """add_player_bg() from WDR without existing nationalities and location"""
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertIsNone(p.wdr_player_id)
        self.assertEqual(p.location, '')
        self.assertEqual(len(p.nationalities), 0)
        wdd.delete()
        p.wdr_player_id = CHRIS_BRAND_WDR_ID
        p.save()
        add_player_bg(p)
        # check results - values from WDR should be stored
        p.refresh_from_db()
        self.assertEqual(p.nationalities, [Country('CA')])
        self.assertEqual(p.location, 'Canada')
        # Cleanup
        WDDPlayer.objects.create(player=p,
                                 wdd_player_id=CHRIS_BRAND_WDD_ID)
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


class PlayerTests(TestCase):
    """Test the Player class"""
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

    # Player.__str__()
    def test_wddplayer_str(self):
        p = Player.objects.first()
        string = str(p)
        # TODO Verify result

    # Player.sortable_str()
    def test_wddplayer_sortable_str(self):
        p = Player.objects.first()
        string = p.sortable_str()
        # TODO Verify result

    # Player._clear_background()
    def test_player_clear_background(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        # Create one of each type of background record
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(timezone.utc),
                                              position=2)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(timezone.utc),
                                        name='Nicest Person')
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        p._clear_background()
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        # Cleanup
        p.delete()

    # Player.background_updated()
    # TODO test when some background objects are missing
    def test_player_background_updated_playertournamentranking(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        start = datetime.now(timezone.utc)
        # Create one of each type of background record, with PlayerTournamentRanking last
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(timezone.utc),
                                              position=2)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(timezone.utc),
                                        name='Nicest Person')
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        end = datetime.now(timezone.utc)
        updated = p.background_updated()
        self.assertLess(start, updated)
        self.assertLess(updated, end)
        self.assertEqual(updated, ptr.updated)
        # Cleanup
        p.delete()

    def test_player_background_updated_playertitle(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        start = datetime.now(timezone.utc)
        # Create one of each type of background record, with PlayerTitle last
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(timezone.utc),
                                              position=2)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(timezone.utc),
                                        name='Nicest Person')
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        end = datetime.now(timezone.utc)
        updated = p.background_updated()
        self.assertLess(start, updated)
        self.assertLess(updated, end)
        self.assertEqual(updated, pt.updated)
        # Cleanup
        p.delete()

    def test_player_background_updated_playergameresult(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        start = datetime.now(timezone.utc)
        # Create one of each type of background record, with PlayerGameResult last
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(timezone.utc),
                                        name='Nicest Person')
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(timezone.utc),
                                              position=2)
        end = datetime.now(timezone.utc)
        updated = p.background_updated()
        self.assertLess(start, updated)
        self.assertLess(updated, end)
        self.assertEqual(updated, pgr.updated)
        # Cleanup
        p.delete()

    def test_player_background_updated_playeraward(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        start = datetime.now(timezone.utc)
        # Create one of each type of background record, with PlayerAward last
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(timezone.utc),
                                              position=2)
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(timezone.utc),
                                        name='Nicest Person')
        end = datetime.now(timezone.utc)
        updated = p.background_updated()
        self.assertLess(start, updated)
        self.assertLess(updated, end)
        self.assertEqual(updated, pa.updated)
        # Cleanup
        p.delete()

    def test_player_background_updated_playerranking(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        start = datetime.now(timezone.utc)
        # Create one of each type of background record, with PlayerRanking last
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(timezone.utc),
                                              position=2)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(timezone.utc),
                                        name='Nicest Person')
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        end = datetime.now(timezone.utc)
        updated = p.background_updated()
        self.assertLess(start, updated)
        self.assertLess(updated, end)
        self.assertEqual(updated, pr.updated)
        # Cleanup
        p.delete()

    def test_player_background_updated_none(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        self.assertEqual(None, p.background_updated())
        # Cleanup
        p.delete()

    # Player.wdr_url()
    def test_player_wdr_url(self):
        p = Player.objects.create(first_name='John', last_name='Smith', wdr_player_id=69)
        # TODO Validate results
        res = p.wdr_url()
        # Cleanup
        p.delete()

    def test_player_wdr_url_no_id(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        res = p.wdr_url()
        self.assertEqual(res, '')
        # Cleanup
        p.delete()

    # Player.wdd_firstname_lastname()
    @tag('slow', 'wdd')
    def test_player_wdd_firstname_lastname(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        player = wdd.player
        wdd.player = p
        wdd.save()
        res = p.wdd_firstname_lastname()
        self.assertEqual(res, ('Chris','BRAND'))
        # Cleanup
        wdd.player = player
        wdd.save()
        p.delete()

    def test_player_wdd_firstname_lastname_no_id(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        name = p.wdd_firstname_lastname()
        self.assertEqual(name[0], 'John')
        self.assertEqual(name[1], 'Smith')
        # Cleanup
        p.delete()

    # Player.wdr_name()
    @tag('wdr')
    def test_player_wdr_name(self):
        p = Player.objects.create(first_name='John', last_name='Smith', wdr_player_id=CHRIS_BRAND_WDR_ID)
        res = p.wdr_name()
        self.assertEqual(res, 'Chris Brand')
        # Cleanup
        p.delete()

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
        # Cleanup
        tp2.delete()
        tp1.delete()
        p.delete()
        t2.delete()
        t1.delete()

    # Player.background()
    def test_player_background_mask(self):
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        # Add one of each type of background object
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(timezone.utc),
                                              position=2)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(timezone.utc),
                                        name='Nicest Person')
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        self.assertEqual([], p.background(mask=0))
        # Cleanup
        p._clear_background()

    def test_player_background_mask_2(self):
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        # Add one of each type of background object
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(timezone.utc),
                                              position=2)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(timezone.utc),
                                        name='Nicest Person')
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        # Test each mask bit individually
        mask = 1
        while mask <= MASK_ALL_BG:
            with self.subTest(mask=mask):
                # TODO Validate results
                p.background(mask=mask)
            mask *= 2
        # Cleanup
        p._clear_background()

    def test_player_background_with_power_never_played(self):
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        # Add one of each type of background object
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(timezone.utc),
                                              position=2)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(timezone.utc),
                                        name='Nicest Person')
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        res = p.background(power=self.germany)
        self.assertEqual(2, len(res))
        self.assertIn('Chris Brand has never played as Germany in a tournament before.', res)
        self.assertIn('Chris Brand has never won Best Germany.', res)
        res = p.background(power=self.germany, mask=0)
        self.assertEqual([], res)
        # Cleanup
        p._clear_background()

    def test_player_background_with_power(self):
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        # Add one of each type of background object
        today = datetime.today()
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.germany,
                                              date=today,
                                              position=2)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=today,
                                        name='Best German',
                                        power=self.germany)
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        res = p.background(power=self.germany)
        # The Award and the GameResult should be included
        self.assertEqual(7, len(res))
        self.assertIn('Chris Brand has played 1 tournament game as Germany.', res)
        self.assertIn('Chris Brand has yet to solo as Germany at a tournament.', res)
        self.assertIn('Chris Brand has yet to be eliminated as Germany in a tournament.', res)
        self.assertIn('Chris Brand has yet to top the board as Germany at a tournament.', res)
        self.assertIn('Chris Brand has won Best Germany once.', res)
        self.assertIn(f'Chris Brand first won Best German in {today.year} at Some tournament.', res)
        self.assertIn(f'Chris Brand most recently won Best German in {today.year} at Some tournament.', res)
        # Cleanup
        p._clear_background()

    def test_player_background_no_sc_count(self):
        p = Player.objects.create(first_name='Joe',
                                  last_name='Bloggs')
        # No final_sc_count (or other optional fields)
        pgr = PlayerGameResult.objects.create(tournament_name='Best Tournament',
                                              round_number=1,
                                              game_number=1,
                                              player=p,
                                              power=self.austria,
                                              date=date.today(),
                                              position=2)
        bg = p.background()
        self.assertIn('Joe Bloggs has played 1 tournament game.', bg)
        # Cleanup
        p.delete()

    def test_player_background_game_count(self):
        p = Player.objects.create(first_name='Joe',
                                  last_name='Bloggs')
        pgr = PlayerGameResult.objects.create(tournament_name='Best Tournament',
                                              round_number=1,
                                              game_number=1,
                                              player=p,
                                              power=self.austria,
                                              date=date.today(),
                                              position=1,
                                              final_sc_count=19)
        pgr = PlayerGameResult.objects.create(tournament_name='Worst Tournament',
                                              round_number=1,
                                              game_number=1,
                                              player=p,
                                              power=self.germany,
                                              date=date.today(),
                                              position=6,
                                              final_sc_count=0)
        bg = p.background()
        self.assertIn('Joe Bloggs has played 2 tournament games.', bg)
        self.assertIn('Joe Bloggs has finished with as many as 19 centres in tournament games.', bg)
        self.assertIn('Joe Bloggs has soloed 1 of 2 tournament games played (50.00%).', bg)
        self.assertIn('Joe Bloggs was eliminated in 1 of 2 tournament games played (50.00%).', bg)
        self.assertIn('Joe Bloggs topped the board in 1 of 2 tournament games played (50.00%).', bg)
        # Cleanup
        p.delete()

    def test_player_background_award_repeat(self):
        p = Player.objects.create(first_name='Joe',
                                  last_name='Bloggs')
        today = datetime.today()
        yesterday = today - timedelta(days=1)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=yesterday,
                                        name='Best Germany',
                                        power=self.germany,
                                        final_sc_count=10)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Another tournament',
                                        date=today,
                                        name='Best Germany',
                                        power=self.germany,
                                        final_sc_count=12)
        bg = p.background()
        self.assertIn('Joe Bloggs has won Best Germany 2 times.', bg)
        self.assertIn(f'Joe Bloggs first won Best Germany in {yesterday.year} at Some tournament with 10 Supply Centres.', bg)
        self.assertIn(f'Joe Bloggs most recently won Best Germany in {today.year} at Another tournament with 12 Supply Centres.', bg)
        # Cleanup
        p.delete()

    def test_player_background_winner(self):
        wdd = WDDPlayer.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        p = wdd.player
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Alpha',
                                                     position=3,
                                                     year=1994)
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Bravo',
                                                     position=1,
                                                     year=2004)
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Charlie',
                                                     position=1,
                                                     year=2014)
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Delta',
                                                     position=5,
                                                     year=2024)
        res = p.background()
        self.assertIn('Chris Brand has won 2 of 4 tournaments (50.00%).', res)
        self.assertIn('Chris Brand won their first tournament (Bravo) in 2004.', res)
        self.assertIn('Chris Brand most recently won a tournament (Charlie) in 2014.', res)
        # Cleanup
        p._clear_background()

    # Player.get_absolute_url()
    def test_player_get_absolute_url(self):
        p = Player.objects.first()
        p.get_absolute_url()


class WDDPlayerTests(TestCase):
    """Test the WDDPlayer class"""
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

    # TODO WDDPlayer._clear_background()

    # WDDPlayer.wdd_url()
    def test_wddplayer_wdd_url(self):
        wdd = WDDPlayer.objects.first()
        url = wdd.wdd_url()
        # TODO verify result

    # WDDPlayer.wdd_firstname_lastname()
    @tag('wdd')
    def test_wddplayer_wdd_name1(self):
        wdd = WDDPlayer.objects.first()
        name = wdd.wdd_firstname_lastname()
        # TODO verify result

    @tag('wdd')
    def test_wddplayer_wdd_name2(self):
        """Fast path if already cached"""
        wdd = WDDPlayer.objects.first()
        wdd._wdd_firstname = 'Arthur'
        name = wdd.wdd_firstname_lastname()
        self.assertEqual(name[0], 'Arthur')

    # WDDPlayer.delete()
    def test_wddplayer_delete(self):
        wdd = WDDPlayer.objects.first()
        p = wdd.player
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        wdd_id = wdd.wdd_player_id
        # Create one of each type of background record
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(timezone.utc),
                                              position=2)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(timezone.utc),
                                        name='Nicest Person')
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        wdd.delete()
        # Deletion should trigger clearing of background
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        # Clean up
        WDDPlayer.objects.create(wdd_player_id = wdd_id,
                                 player=p)

    # Change of WDDPlayer.wdd_player_id
    # This mostly tests WDDPlayerIdField.pre_save()
    def test_wddplayer_save(self):
        wdd = WDDPlayer.objects.first()
        p = wdd.player
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        wdd_id = wdd.wdd_player_id
        # Create one of each type of background record
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(timezone.utc),
                                              position=2)
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(timezone.utc),
                                        name='Nicest Person')
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        wdd.wdd_player_id = MELINDA_HOLLEY_WDD_ID
        wdd.save(update_fields=['wdd_player_id'])
        # Change in wdd_player_id should trigger clearing of background
        self.assertEqual(0, p.playertournamentranking_set.count())
        self.assertEqual(0, p.playertitle_set.count())
        self.assertEqual(0, p.playergameresult_set.count())
        self.assertEqual(0, p.playeraward_set.count())
        self.assertEqual(0, p.playerranking_set.count())
        # Clean up
        wdd.wdd_player_id = wdd_id
        wdd.save(update_fields=['wdd_player_id'])

    # WDDPlayer.__str__()
    def test_wddplayer_str(self):
        wdd = WDDPlayer.objects.first()
        string = str(wdd)
        # TODO Verify result


class PlayerTournamentRankingTests(TestCase):
    """Test the PlayerTournamentRanking class"""
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

    # PlayerTournamentRanking.wdd_url()
    def test_playertournamentranking_wdd_url(self):
        p = Player.objects.first()
        ptr = PlayerTournamentRanking(player=p,
                                      tournament='Some tournament',
                                      position=3,
                                      year=1974,
                                      wdd_tournament_id=369)
        url = ptr.wdd_url()
        # TODO verify result
        # Also check wdr_url() for a PTR with no WDR id
        self.assertEqual('', ptr.wdr_url())

    # PlayerTournamentRanking.wdr_url()
    def test_playertournamentranking_wdr_url(self):
        p = Player.objects.first()
        ptr = PlayerTournamentRanking(player=p,
                                      tournament='Some tournament',
                                      position=3,
                                      year=1974,
                                      wdr_tournament_id=369)
        url = ptr.wdr_url()
        # TODO verify result
        # Also check wdd_url() for a PTR with no WDD id
        self.assertEqual('', ptr.wdd_url())

    # PlayerTournamentRanking.__str__()
    def test_playertournamentranking_str(self):
        p = Player.objects.first()
        ptr = PlayerTournamentRanking(player=p,
                                      tournament='Some tournament',
                                      position=3,
                                      year=1974)
        p_str = str(ptr)
        # We expect to find player name, tournament name, and year
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(ptr.tournament, p_str)
        self.assertIn(str(ptr.year), p_str)

    def test_playertournamentranking_str_with_year(self):
        p = Player.objects.first()
        ptr = PlayerTournamentRanking(player=p,
                                      tournament='Some tournament 1974',
                                      position=3,
                                      year=1974)
        p_str = str(ptr)
        # We expect to find player name, tournament name, and year
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(ptr.tournament, p_str)
        self.assertIn(str(ptr.year), p_str)


class PlayerTitleTests(TestCase):
    """Test the PlayerTitle class"""
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


class PlayerGameResultTests(TestCase):
    """Test the PlayerGameResult class"""
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

    # PlayeGameResult.game_name()
    def test_playergameresult_game_name(self):
        p = Player.objects.first()
        pgr = PlayerGameResult(tournament_name='Best Tournament',
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               date=date.today(),
                               position=2)
        name = pgr.game_name()
        self.assertEqual(name, 'R 1 B 3')

    # PlayerGameResult.wdd_url()
    def test_playergameresult_wdd_url(self):
        p = Player.objects.first()
        pgr = PlayerGameResult(tournament_name='Best Tournament',
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               date=date.today(),
                               position=2,
                               wdd_tournament_id=369)
        url = pgr.wdd_url()
        # TODO verify result
        # Check wdr_url() for a PGR with no WDR id
        self.assertIsNone(pgr.wdr_tournament_id)
        url = pgr.wdr_url()

    # PlayerGameResult.wdr_url()
    def test_playergameresult_wdr_url(self):
        wdd = WDDPlayer.objects.first()
        p = wdd.player
        pgr = PlayerGameResult(tournament_name='Best Tournament',
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               date=date.today(),
                               position=2,
                               wdr_tournament_id=369)
        url = pgr.wdr_url()
        # TODO verify result
        # Check wdr_url() for a PGR with no WDR id
        self.assertIsNotNone(pgr.wdr_tournament_id)
        url = pgr.wdr_url()

    # PlayerGameResult.__str__()
    def test_playergameresult_str(self):
        p = Player.objects.first()
        pgr = PlayerGameResult(tournament_name='Best Tournament',
                               round_number=1,
                               game_number=3,
                               player=p,
                               power=self.austria,
                               date=date.today(),
                               position=2)
        p_str = str(pgr)
        # We expect to find player name and power name
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(pgr.power.name, p_str)


class PlayerAwardTests(TestCase):
    """Test the PlayerAward class"""
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

    # PlayerAward.wdd_url()
    def test_playeraward_wdd_url_power(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         tournament='Some tournament',
                         date=datetime.now(timezone.utc),
                         name='Nicest Player of France',
                         wdd_tournament_id=369,
                         power=self.france)
        url = pa.wdd_url()
        # TODO verify result
        # Also check wdr_url() for a PA with no WDR id
        self.assertEqual('', pa.wdr_url())

    def test_playeraward_wdd_url_no_power(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         tournament='Some tournament',
                         date=datetime.now(timezone.utc),
                         name='Nicest Person',
                         wdd_tournament_id=369)
        url = pa.wdd_url()
        # TODO verify result

    # PlayerAward.wdr_url()
    def test_playeraward_wdr_url(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         tournament='Some tournament',
                         date=datetime.now(timezone.utc),
                         name='Nicest Person',
                         wdr_tournament_id=369)
        url = pa.wdr_url()
        # TODO verify result
        # Also check wdd_url() for a PA with no WDD id
        self.assertEqual('', pa.wdd_url())

    # PlayerAward.__str__()
    def test_playeraward_str(self):
        p = Player.objects.first()
        pa = PlayerAward(player=p,
                         tournament='Some tournament',
                         date=datetime.now(timezone.utc),
                         name='Nicest Person')
        p_str = str(pa)
        # We expect to find player name, award name, and tournament name
        self.assertIn(p.first_name, p_str)
        self.assertIn(p.last_name, p_str)
        self.assertIn(pa.name, p_str)
        self.assertIn(pa.tournament, p_str)


class PlayerRankingTests(TestCase):
    """Test the PlayerRanking class"""
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

    # PlayerRanking.wdd_url()
    def test_playerranking_wdd_url_wpe(self):
        p = Player.objects.first()
        self.assertNotEqual(p.wddplayer_set.count(), 0)
        pr = PlayerRanking(player=p,
                           system='World Performance Evaluation',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdd_url()
        # TODO Validate results

    def test_playerranking_wdd_url_dip_pouch(self):
        p = Player.objects.first()
        self.assertNotEqual(p.wddplayer_set.count(), 0)
        pr = PlayerRanking(player=p,
                           system='Dip Pouch Tournament Rating',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdd_url()
        # TODO Validate results

    def test_playerranking_wdd_url_sdr(self):
        p = Player.objects.first()
        self.assertNotEqual(p.wddplayer_set.count(), 0)
        pr = PlayerRanking(player=p,
                           system='SDR Marathon',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdd_url()
        # TODO Validate results

    def test_playerranking_wdd_url_other(self):
        p = Player.objects.first()
        self.assertNotEqual(p.wddplayer_set.count(), 0)
        pr = PlayerRanking(player=p,
                           system='WPE7',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdd_url()
        # TODO Validate results

    @tag('slow', 'wdd')
    def test_playerranking_wdd_url_no_id(self):
        wdd = WDDPlayer.objects.first()
        p = wdd.player
        wdd_id = wdd.wdd_player_id
        wdd.delete()
        pr = PlayerRanking(player=p,
                           system='World Performance Evaluation',
                           international_rank='8',
                           national_rank='3')
        self.assertEqual('', pr.wdd_url())
        # Cleanup
        WDDPlayer.objects.create(wdd_player_id=wdd_id,
                                 player=p)

    # PlayerRanking.wdr_url()
    def test_playerranking_wdr_url_wpe1(self):
        p = Player.objects.first()
        pr = PlayerRanking(player=p,
                           system='WPE7',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdr_url()
        # TODO Validate results

    def test_playerranking_wdr_url_wpe2(self):
        p = Player.objects.first()
        pr = PlayerRanking(player=p,
                           system='World Performance Evaluation',
                           international_rank='8',
                           national_rank='3')
        url = pr.wdr_url()
        # TODO Validate results

    # PlayerRanking.national_str()
    def test_playerranking_national_str(self):
        p = Player.objects.first()
        pr = PlayerRanking(player=p,
                           system='World Performance Evaluation',
                           international_rank='8',
                           national_rank='3')
        # TODO Validate results
        pr.national_str()

    # PlayerRanking.__str__()
    def test_playerranking_str(self):
        p = Player.objects.first()
        pr = PlayerRanking(player=p,
                           system='World Performance Evaluation',
                           international_rank='8',
                           national_rank='3')
        # TODO Validate results
        str(pr)
