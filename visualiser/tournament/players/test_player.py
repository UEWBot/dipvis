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

from datetime import date, datetime, timedelta
from datetime import timezone as datetime_timezone

from django.test import TestCase, tag

from tournament.diplomacy import GreatPower
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Tournament, TournamentPlayer)
from tournament.players import (MASK_ALL_BG, PlayerAward, PlayerGameResult,
                                PlayerRanking, PlayerTitle,
                                PlayerTournamentRanking, WDDPlayer)

from . import Player, player_picture_location

CHRIS_BRAND_WDD_ID = 4173
CHRIS_BRAND_WDR_ID = 7164


class PlayerPictureLocationTests(TestCase):
    # player_picture_location()
    def test_player_picture_location(self):
        res = player_picture_location(None, 'pretty_boy.jpg')
        # TODO validate result


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
        PlayerTournamentRanking.objects.create(player=p,
                                               tournament='Some tournament',
                                               position=3,
                                               year=1974)
        PlayerTitle.objects.create(player=p,
                                   title='Canadian Beaver',
                                   year=1976)
        PlayerGameResult.objects.create(player=p,
                                        tournament_name='Some tournament',
                                        round_number=4,
                                        game_number=17,
                                        power=self.austria,
                                        date=datetime.now(datetime_timezone.utc),
                                        position=2)
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=datetime.now(datetime_timezone.utc),
                                   name='Nicest Person')
        PlayerRanking.objects.create(player=p,
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
        start = datetime.now(datetime_timezone.utc)
        # Create one of each type of background record, with PlayerTournamentRanking last
        PlayerTitle.objects.create(player=p,
                                   title='Canadian Beaver',
                                   year=1976)
        PlayerGameResult.objects.create(player=p,
                                        tournament_name='Some tournament',
                                        round_number=4,
                                        game_number=17,
                                        power=self.austria,
                                        date=datetime.now(datetime_timezone.utc),
                                        position=2)
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=datetime.now(datetime_timezone.utc),
                                   name='Nicest Person')
        PlayerRanking.objects.create(player=p,
                                     system='Who Chris Likes Most',
                                     international_rank='8',
                                     national_rank='3')
        ptr = PlayerTournamentRanking.objects.create(player=p,
                                                     tournament='Some tournament',
                                                     position=3,
                                                     year=1974)
        end = datetime.now(datetime_timezone.utc)
        updated = p.background_updated()
        self.assertLess(start, updated)
        self.assertLess(updated, end)
        self.assertEqual(updated, ptr.updated)
        # Cleanup
        p.delete()

    def test_player_background_updated_playertitle(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        start = datetime.now(datetime_timezone.utc)
        # Create one of each type of background record, with PlayerTitle last
        PlayerTournamentRanking.objects.create(player=p,
                                               tournament='Some tournament',
                                               position=3,
                                               year=1974)
        PlayerGameResult.objects.create(player=p,
                                        tournament_name='Some tournament',
                                        round_number=4,
                                        game_number=17,
                                        power=self.austria,
                                        date=datetime.now(datetime_timezone.utc),
                                        position=2)
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=datetime.now(datetime_timezone.utc),
                                   name='Nicest Person')
        PlayerRanking.objects.create(player=p,
                                     system='Who Chris Likes Most',
                                     international_rank='8',
                                     national_rank='3')
        pt = PlayerTitle.objects.create(player=p,
                                        title='Canadian Beaver',
                                        year=1976)
        end = datetime.now(datetime_timezone.utc)
        updated = p.background_updated()
        self.assertLess(start, updated)
        self.assertLess(updated, end)
        self.assertEqual(updated, pt.updated)
        # Cleanup
        p.delete()

    def test_player_background_updated_playergameresult(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        start = datetime.now(datetime_timezone.utc)
        # Create one of each type of background record, with PlayerGameResult last
        PlayerTournamentRanking.objects.create(player=p,
                                               tournament='Some tournament',
                                               position=3,
                                               year=1974)
        PlayerTitle.objects.create(player=p,
                                   title='Canadian Beaver',
                                   year=1976)
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=datetime.now(datetime_timezone.utc),
                                   name='Nicest Person')
        PlayerRanking.objects.create(player=p,
                                     system='Who Chris Likes Most',
                                     international_rank='8',
                                     national_rank='3')
        pgr = PlayerGameResult.objects.create(player=p,
                                              tournament_name='Some tournament',
                                              round_number=4,
                                              game_number=17,
                                              power=self.austria,
                                              date=datetime.now(datetime_timezone.utc),
                                              position=2)
        end = datetime.now(datetime_timezone.utc)
        updated = p.background_updated()
        self.assertLess(start, updated)
        self.assertLess(updated, end)
        self.assertEqual(updated, pgr.updated)
        # Cleanup
        p.delete()

    def test_player_background_updated_playeraward(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        start = datetime.now(datetime_timezone.utc)
        # Create one of each type of background record, with PlayerAward last
        PlayerTournamentRanking.objects.create(player=p,
                                               tournament='Some tournament',
                                               position=3,
                                               year=1974)
        PlayerTitle.objects.create(player=p,
                                   title='Canadian Beaver',
                                   year=1976)
        PlayerGameResult.objects.create(player=p,
                                        tournament_name='Some tournament',
                                        round_number=4,
                                        game_number=17,
                                        power=self.austria,
                                        date=datetime.now(datetime_timezone.utc),
                                        position=2)
        PlayerRanking.objects.create(player=p,
                                     system='Who Chris Likes Most',
                                     international_rank='8',
                                     national_rank='3')
        pa = PlayerAward.objects.create(player=p,
                                        tournament='Some tournament',
                                        date=datetime.now(datetime_timezone.utc),
                                        name='Nicest Person')
        end = datetime.now(datetime_timezone.utc)
        updated = p.background_updated()
        self.assertLess(start, updated)
        self.assertLess(updated, end)
        self.assertEqual(updated, pa.updated)
        # Cleanup
        p.delete()

    def test_player_background_updated_playerranking(self):
        p = Player.objects.create(first_name='Unknown', last_name='Player')
        start = datetime.now(datetime_timezone.utc)
        # Create one of each type of background record, with PlayerRanking last
        PlayerTournamentRanking.objects.create(player=p,
                                               tournament='Some tournament',
                                               position=3,
                                               year=1974)
        PlayerTitle.objects.create(player=p,
                                   title='Canadian Beaver',
                                   year=1976)
        PlayerGameResult.objects.create(player=p,
                                        tournament_name='Some tournament',
                                        round_number=4,
                                        game_number=17,
                                        power=self.austria,
                                        date=datetime.now(datetime_timezone.utc),
                                        position=2)
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=datetime.now(datetime_timezone.utc),
                                   name='Nicest Person')
        pr = PlayerRanking.objects.create(player=p,
                                          system='Who Chris Likes Most',
                                          international_rank='8',
                                          national_rank='3')
        end = datetime.now(datetime_timezone.utc)
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
        self.assertEqual(res, ('Chris', 'BRAND'))
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
                                       end_date=today + timedelta(hours=72),
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET,
                                       is_published=True)
        t2 = Tournament.objects.create(name='t2',
                                       start_date=today,
                                       end_date=today + timedelta(hours=24),
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET,
                                       is_published=False)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=today,
                                       end_date=today + timedelta(hours=48),
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET,
                                       is_published=True)
        # Now we need a player that played in all three tournaments
        p = Player.objects.create(first_name='Joe',
                                  last_name='Schmoe')
        tp1 = TournamentPlayer.objects.create(tournament=t1,
                                              player=p)
        tp2 = TournamentPlayer.objects.create(tournament=t2,
                                              player=p)
        tp3 = TournamentPlayer.objects.create(tournament=t3,
                                              player=p)
        # Latest-ending tournament should be listed first
        tps = p.tournamentplayers(including_unpublished=False)
        self.assertEqual(list(tps), [tp1, tp3])
        tps = p.tournamentplayers(including_unpublished=True)
        self.assertEqual(list(tps), [tp1, tp3, tp2])
        # Cleanup
        p.delete()
        t3.delete()
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
        PlayerTournamentRanking.objects.create(player=p,
                                               tournament='Some tournament',
                                               position=3,
                                               year=1974)
        PlayerTitle.objects.create(player=p,
                                   title='Canadian Beaver',
                                   year=1976)
        PlayerGameResult.objects.create(player=p,
                                        tournament_name='Some tournament',
                                        round_number=4,
                                        game_number=17,
                                        power=self.austria,
                                        date=datetime.now(datetime_timezone.utc),
                                        position=2)
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=datetime.now(datetime_timezone.utc),
                                   name='Nicest Person')
        PlayerRanking.objects.create(player=p,
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
        PlayerTournamentRanking.objects.create(player=p,
                                               tournament='Some tournament',
                                               position=3,
                                               year=1974)
        PlayerTitle.objects.create(player=p,
                                   title='Canadian Beaver',
                                   year=1976)
        PlayerGameResult.objects.create(player=p,
                                        tournament_name='Some tournament',
                                        round_number=4,
                                        game_number=17,
                                        power=self.austria,
                                        date=datetime.now(datetime_timezone.utc),
                                        position=2)
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=datetime.now(datetime_timezone.utc),
                                   name='Nicest Person')
        PlayerRanking.objects.create(player=p,
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
        PlayerTournamentRanking.objects.create(player=p,
                                               tournament='Some tournament',
                                               position=3,
                                               year=1974)
        PlayerTitle.objects.create(player=p,
                                   title='Canadian Beaver',
                                   year=1976)
        PlayerGameResult.objects.create(player=p,
                                        tournament_name='Some tournament',
                                        round_number=4,
                                        game_number=17,
                                        power=self.austria,
                                        date=datetime.now(datetime_timezone.utc),
                                        position=2)
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=datetime.now(datetime_timezone.utc),
                                   name='Nicest Person')
        PlayerRanking.objects.create(player=p,
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
        PlayerTournamentRanking.objects.create(player=p,
                                               tournament='Some tournament',
                                               position=3,
                                               year=1974)
        PlayerTitle.objects.create(player=p,
                                   title='Canadian Beaver',
                                   year=1976)
        PlayerGameResult.objects.create(player=p,
                                        tournament_name='Some tournament',
                                        round_number=4,
                                        game_number=17,
                                        power=self.germany,
                                        date=today,
                                        position=2)
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=today,
                                   name='Best German',
                                   power=self.germany)
        PlayerRanking.objects.create(player=p,
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
        PlayerGameResult.objects.create(tournament_name='Best Tournament',
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
        PlayerGameResult.objects.create(tournament_name='Best Tournament',
                                        round_number=1,
                                        game_number=1,
                                        player=p,
                                        power=self.austria,
                                        date=date.today(),
                                        position=1,
                                        final_sc_count=19)
        PlayerGameResult.objects.create(tournament_name='Worst Tournament',
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
        PlayerAward.objects.create(player=p,
                                   tournament='Some tournament',
                                   date=yesterday,
                                   name='Best Germany',
                                   power=self.germany,
                                   final_sc_count=10)
        PlayerAward.objects.create(player=p,
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
