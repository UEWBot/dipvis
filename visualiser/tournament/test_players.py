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

from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.test import TestCase, tag
from django.utils import timezone

from tournament.diplomacy.models.great_power import GreatPower
from tournament.models import DrawSecrecy
from tournament.models import Tournament, TournamentPlayer
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.players import Player, PlayerRanking, PlayerAward
from tournament.players import PlayerGameResult, PlayerTournamentRanking
from tournament.players import validate_wdd_player_id, validate_wdd_tournament_id
from tournament.players import add_player_bg
from tournament.players import MASK_ALL_BG

CHRIS_BRAND_WDD_ID = 4173
MATT_SHIELDS_WDD_ID = 588
MATT_SUNDSTROM_WDD_ID = 8355
NATE_COCKERILL_WDD_ID = 5009
SPIROS_BOBETSIS_WDD_ID = 12304
CLAESAR_WEBDIP_WDD_ID = 13317
MELINDA_HOLLEY_WDD_ID = 5185


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

    # TODO player_picture_location()

    # TODO wdd_url_to_id()

    # TODO add_player_bg()

    # TODO position_str()

    # Player.wdd_name()
    @tag('slow', 'wdd')
    def test_player_wdd_name(self):
        p = Player.objects.first()
        # TODO Validate results
        p.wdd_name()

    def test_player_wdd_name_no_id(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        # TODO Validate results
        p.wdd_name()

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

    # Player.wdd_url()
    def test_player_wdd_url(self):
        p = Player.objects.first()
        # TODO Validate results
        p.wdd_url()

    def test_player_wdd_url_no_id(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        # TODO Validate results
        p.wdd_url()

    # Player.tournamentplayers()
    def test_player_tournamentplayers(self):
        now = timezone.now()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET,
                                       is_published=True)
        t1.save()
        t2 = Tournament.objects.create(name='t2',
                                       start_date=now,
                                       end_date=now,
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
        # TODO Validate results
        p.background()

    @tag('slow', 'wdd')
    def test_player_background_invalid_date(self):
        # Spiros has yet to win a tournament
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
                               game_name='Top Board',
                               player=p,
                               power=self.austria,
                               date=timezone.now(),
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
                               game_name='Top Board',
                               player=p,
                               power=self.austria,
                               date=timezone.now(),
                               position=2)
        pgr.save()
        bg = p.background()
        self.assertIn('Joe Bloggs has played 1 tournament game.', bg)
        pgr.delete()
        p.delete()

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

    # TODO Player.save()

    # TODO Player.get_absolute_url()

    # PlayerTournamentRanking
    # PlayerTournamentRanking.wdd_url()
    @tag('slow', 'wdd')
    def test_playertournamentranking_wdd_url(self):
        p = Player.objects.first()
        add_player_bg(p)
        ptr = PlayerTournamentRanking.objects.first()
        url = ptr.wdd_url()
        # TODO verify result

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

    # PlayerGameResult
    # TODO PlayerGameResult.for_same_game()
    def test_playergameresult_same(self):
        p1 = Player.objects.first()
        p2 = Player.objects.last()
        # No final_sc_count (or other optional fields)
        pgr1 = PlayerGameResult(tournament_name='Best Tournament',
                                game_name='Top Board',
                                player=p1,
                                power=self.austria,
                                date=timezone.now(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name=pgr1.tournament_name,
                                game_name=pgr1.game_name,
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
                                game_name='Top Board',
                                player=p1,
                                power=self.austria,
                                date=timezone.now(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name='Worst Tournament',
                                game_name=pgr1.game_name,
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
                                game_name='Top Board',
                                player=p1,
                                power=self.austria,
                                date=timezone.now(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name=pgr1.tournament_name,
                                game_name='Bottom Board',
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
                                game_name='Top Board',
                                player=p1,
                                power=self.austria,
                                date=timezone.now(),
                                position=2)
        pgr2 = PlayerGameResult(tournament_name=pgr1.tournament_name,
                                game_name=pgr1.game_name,
                                player=p2,
                                power=self.russia,
                                date=timezone.now(),
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
