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
from django.db.models import Sum
from django.test import TestCase, tag, override_settings
from django.utils import timezone

from tournament.diplomacy import GreatPower, SupplyCentre, GameSet
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, Round, Game, DrawProposal, GameImage
from tournament.models import SupplyCentreOwnership, CentreCount, Preference
from tournament.models import validate_weight, SeederBias
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
from tournament.models import MASK_ALL_NEWS
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import SPRING
from tournament.models import find_game_scoring_system
from tournament.models import find_round_scoring_system
from tournament.models import find_tournament_scoring_system
from tournament.models import validate_game_name, validate_sc_count, validate_vote_count
from tournament.models import SCOwnershipsNotFound, InvalidScoringSystem, InvalidYear
from tournament.models import InvalidPreferenceList
from tournament.players import Player, MASK_ALL_BG

from datetime import timedelta

HOURS_8 = timedelta(hours=8)
HOURS_9 = timedelta(hours=9)
HOURS_10 = timedelta(hours=10)
HOURS_16 = timedelta(hours=16)
HOURS_24 = timedelta(hours=24)

@override_settings(HOSTNAME='example.com')
class TournamentModelTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')
        cls.set2 = GameSet.objects.get(name='Gibsons')

        s1 = G_SCORING_SYSTEMS[0].name

        now = timezone.now()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=Tournament.SECRET)
        t2 = Tournament.objects.create(name='t2',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=Tournament.SECRET)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=Tournament.COUNTS)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=t1.start_date)
        r12 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=t1.start_date + HOURS_8)
        r13 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=t1.start_date + HOURS_16)
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=t1.start_date + HOURS_24)
        # Add Rounds to t2
        r21 = Round.objects.create(tournament=t2,
                                   scoring_system=s1,
                                   dias=False,
                                   start=t2.start_date)
        r22 = Round.objects.create(tournament=t2,
                                   scoring_system=s1,
                                   dias=False,
                                   start=t2.start_date + HOURS_8)
        # Add Rounds to t3
        r31 = Round.objects.create(tournament=t3,
                                   scoring_system=s1,
                                   dias=True,
                                   start=t3.start_date,
                                   final_year=1907)
        r32 = Round.objects.create(tournament=t3,
                                   scoring_system=s1,
                                   dias=True,
                                   start=t3.start_date + HOURS_8,
                                   earliest_end_time=t3.start_date + HOURS_8,
                                   latest_end_time=t3.start_date + HOURS_9)

        # Add Games to r11
        g11 = Game.objects.create(name='g11',
                                  started_at=r11.start,
                                  the_round=r11,
                                  the_set=cls.set1)
        g12 = Game.objects.create(name='g12',
                                  started_at=r11.start,
                                  the_round=r11,
                                  the_set=cls.set1)
        # Add Games to r12
        g13 = Game.objects.create(name='g13',
                                  started_at=r12.start,
                                  the_round=r12,
                                  is_finished=True,
                                  the_set=cls.set1)
        g14 = Game.objects.create(name='g14',
                                  started_at=r12.start,
                                  the_round=r12,
                                  the_set=cls.set1)
        # Add Games to r13
        Game.objects.create(name='g15',
                            started_at=r13.start,
                            the_round=r13,
                            is_finished=True,
                            the_set=cls.set1)
        Game.objects.create(name='g16',
                            started_at=r13.start,
                            the_round=r13,
                            is_finished=True,
                            the_set=cls.set1)
        # Add Games to r21
        Game.objects.create(name='g21',
                            started_at=r21.start,
                            the_round=r21,
                            the_set=cls.set1)
        # Add Games to r22
        Game.objects.create(name='g22',
                            started_at=r22.start,
                            the_round=r22,
                            the_set=cls.set1)
        # Add Games to r31
        Game.objects.create(name='g31',
                            started_at=r31.start,
                            the_round=r31,
                            is_finished=True,
                            the_set=cls.set1)
        # Add Games to r32
        Game.objects.create(name='g32',
                            started_at=r32.start,
                            the_round=r32,
                            is_finished=True,
                            the_set=cls.set1)

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # Add CentreCounts to g11
        CentreCount.objects.create(power=cls.austria, game=g11, year=1901, count=5)
        CentreCount.objects.create(power=cls.england, game=g11, year=1901, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1901, count=5)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1901, count=5)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1901, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1901, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1901, count=4)

        # Solo victory for Germany in 1904
        CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=2)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=18)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=2)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1904, count=3)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1904, count=5)

        # Create some players
        # Avoid hitting the WDD by not providing a WDD id
        cls.p1 = Player.objects.create(first_name='Abbey', last_name='Brown')
        cls.p2 = Player.objects.create(first_name='Charles', last_name='Dog')
        cls.p3 = Player.objects.create(first_name='Ethel', last_name='Frankenstein')
        cls.p4 = Player.objects.create(first_name='George', last_name='Hotel')
        cls.p5 = Player.objects.create(first_name='Iris', last_name='Jackson')
        cls.p6 = Player.objects.create(first_name='Kevin', last_name='Lame')
        cls.p7 = Player.objects.create(first_name='Michelle', last_name='Nobody')
        cls.p8 = Player.objects.create(first_name='Owen', last_name='Pennies')
        # These last two are deliberately not in any tournaments
        cls.p9 = Player.objects.create(first_name='Queenie', last_name='Radiation')
        cls.p10 = Player.objects.create(first_name='Sebastian', last_name='Twinkie')

        # Tournament.news() will call Game.news() for all games in the current round,
        # which will need a player for every country
        # TODO These should really error out with no corresponding RoundPlayer. I guess clean() is not called ?
        # Add GamePlayers to g11
        GamePlayer.objects.create(player=cls.p1,
                                  game=g11,
                                  power=cls.austria,
                                  last_year=1903,
                                  last_season='F')
        GamePlayer.objects.create(player=cls.p2,
                                  game=g11,
                                  power=cls.austria,
                                  first_year=1903,
                                  first_season='X')
        GamePlayer.objects.create(player=cls.p3, game=g11, power=cls.england)
        GamePlayer.objects.create(player=cls.p4, game=g11, power=cls.france)
        GamePlayer.objects.create(player=cls.p5, game=g11, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=g11, power=cls.italy)
        GamePlayer.objects.create(player=cls.p7, game=g11, power=cls.russia)
        GamePlayer.objects.create(player=cls.p8, game=g11, power=cls.turkey)
        # Add GamePlayers to g12
        GamePlayer.objects.create(player=cls.p7, game=g12, power=cls.austria)
        GamePlayer.objects.create(player=cls.p6, game=g12, power=cls.england)
        GamePlayer.objects.create(player=cls.p5, game=g12, power=cls.france)
        GamePlayer.objects.create(player=cls.p4, game=g12, power=cls.germany)
        GamePlayer.objects.create(player=cls.p3, game=g12, power=cls.italy)
        GamePlayer.objects.create(player=cls.p2, game=g12, power=cls.russia)
        GamePlayer.objects.create(player=cls.p1, game=g12, power=cls.turkey)
        # Add GamePlayers to g13
        GamePlayer.objects.create(player=cls.p1,
                                  game=g13,
                                  power=cls.austria,
                                  last_year=1903,
                                  last_season='F')
        GamePlayer.objects.create(player=cls.p2,
                                  game=g13,
                                  power=cls.austria,
                                  first_year=1903,
                                  first_season='X')
        GamePlayer.objects.create(player=cls.p3, game=g13, power=cls.england)
        GamePlayer.objects.create(player=cls.p4, game=g13, power=cls.france)
        GamePlayer.objects.create(player=cls.p5, game=g13, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=g13, power=cls.italy)
        GamePlayer.objects.create(player=cls.p7, game=g13, power=cls.russia)
        GamePlayer.objects.create(player=cls.p8, game=g13, power=cls.turkey)
        # Add GamePlayers to g14
        GamePlayer.objects.create(player=cls.p7, game=g14, power=cls.austria)
        GamePlayer.objects.create(player=cls.p6, game=g14, power=cls.england)
        GamePlayer.objects.create(player=cls.p5, game=g14, power=cls.france)
        GamePlayer.objects.create(player=cls.p4, game=g14, power=cls.germany)
        GamePlayer.objects.create(player=cls.p3, game=g14, power=cls.italy)
        GamePlayer.objects.create(player=cls.p2, game=g14, power=cls.russia)
        GamePlayer.objects.create(player=cls.p1, game=g14, power=cls.turkey)
        # And the corresponding RoundPlayers
        RoundPlayer.objects.create(player=cls.p1, the_round=r11)
        RoundPlayer.objects.create(player=cls.p2, the_round=r11)
        RoundPlayer.objects.create(player=cls.p3, the_round=r11)
        RoundPlayer.objects.create(player=cls.p4, the_round=r11)
        RoundPlayer.objects.create(player=cls.p5, the_round=r11)
        RoundPlayer.objects.create(player=cls.p6, the_round=r11)
        RoundPlayer.objects.create(player=cls.p7, the_round=r11)
        RoundPlayer.objects.create(player=cls.p8, the_round=r11)
        RoundPlayer.objects.create(player=cls.p1, the_round=r12)
        RoundPlayer.objects.create(player=cls.p2, the_round=r12)
        RoundPlayer.objects.create(player=cls.p3, the_round=r12)
        RoundPlayer.objects.create(player=cls.p4, the_round=r12)
        RoundPlayer.objects.create(player=cls.p5, the_round=r12)
        RoundPlayer.objects.create(player=cls.p6, the_round=r12)
        RoundPlayer.objects.create(player=cls.p7, the_round=r12)
        RoundPlayer.objects.create(player=cls.p8, the_round=r12)
        # And TournamentPlayers
        TournamentPlayer.objects.create(player=cls.p1, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p2, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p3, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p5, tournament=t1, unranked=True)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p8, tournament=t1)

        # Add a TournamentPlayer to t3
        TournamentPlayer.objects.create(player=cls.p5, tournament=t3, score=147.3)
        # Add a RoundPlayer to r31
        RoundPlayer.objects.create(player=cls.p5, the_round=r31, score=0.0)
        # Add a RoundPlayer to r32
        RoundPlayer.objects.create(player=cls.p5, the_round=r32, score=47.3)

    # TODO RScoringBest

    # TODO TScoringSum

    # find_scoring_system()
    # Mostly tested implicitly, but we do want to check the error case
    def test_find_g_scoring_system_invalid(self):
        self.assertEqual(None, find_game_scoring_system('Invalid System'))

    def test_find_r_scoring_system_invalid(self):
        self.assertEqual(None, find_round_scoring_system('Invalid System'))

    def test_find_t_scoring_system_invalid(self):
        self.assertEqual(None, find_tournament_scoring_system('Invalid System'))

    # validate_sc_count()
    def test_validate_sc_count_negative(self):
        self.assertRaises(ValidationError, validate_sc_count, -1)

    def test_validate_sc_count_0(self):
        self.assertIsNone(validate_sc_count(0))

    def test_validate_sc_count_34(self):
        self.assertIsNone(validate_sc_count(34))

    def test_validate_sc_count_35(self):
        self.assertRaises(ValidationError, validate_sc_count, 35)

    # validate_game_name()
    def test_validate_game_name_spaces(self):
        self.assertRaises(ValidationError, validate_game_name, u'space name')

    def test_validate_game_name_valid(self):
        self.assertIsNone(validate_game_name(u'ok'))

    # validate_vote_count()
    def test_validate_vote_count_negative(self):
        self.assertRaises(ValidationError, validate_vote_count, -1)

    def test_validate_vote_count_8(self):
        self.assertRaises(ValidationError, validate_vote_count, 8)

    def test_validate_vote_count_1(self):
        self.assertIsNone(validate_vote_count(1))

    def test_validate_vote_count_7(self):
        self.assertIsNone(validate_vote_count(7))

    # TODO game_image_location()

    # TODO add_local_player_bg()

    # Tournament.powers_assigned_from_prefs()
    def test_tournament_powers_Assigned_from_prefs_false(self):
        t = Tournament.objects.first()
        self.assertEqual(t.powers_assigned_from_prefs(), False)

    def test_tournament_powers_Assigned_from_prefs_true(self):
        t = Tournament(name='Test Tournament',
                       start_date=timezone.now(),
                       end_date=timezone.now(),
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       power_assignment=Tournament.PREFERENCES)
        self.assertEqual(t.powers_assigned_from_prefs(), True)

    # Tournament.calculated_scores()
    def test_tournament_scores_invalid(self):
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=timezone.now(),
                                                      end_date=timezone.now(),
                                                      tournament_scoring_system='Invalid System',
                                                      round_scoring_system=R_SCORING_SYSTEMS[0].name)
        self.assertRaises(InvalidScoringSystem, t.calculated_scores)

    def test_tournament_scores_unfinished(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        scores = t.calculated_scores()

    def test_tournament_scores_before_start(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        # Ensure that all TournamentPlayers are included. although there are no RoundPlayers
        scores = t.calculated_scores()

    def test_tournament_scores_recalculate(self):
        t = Tournament.objects.get(name='t3')
        scores = t.calculated_scores()
        self.assertEqual(len(scores), 1)
        # This should be recalculated from the round scores
        self.assertEqual(scores[t.tournamentplayer_set.get().player], 47.3)

    def test_tournament_scores_with_non_player(self):
        # Only interesting for unfinished tournaments
        t = Tournament.objects.get(name='t1')
        # Add an extra player, who didn't actually play
        tp = TournamentPlayer(tournament=t, player=self.p10)
        tp.save()
        scores = t.calculated_scores()
        # Players who didn't play should get a score of zero
        self.assertEqual(scores[self.p10], 0.0)
        tp.delete()

    # Tournament.scores_detail()
    def test_tournament_scores_detail_invalid(self):
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=timezone.now(),
                                                      end_date=timezone.now(),
                                                      tournament_scoring_system='Invalid System',
                                                      round_scoring_system=R_SCORING_SYSTEMS[0].name)
        self.assertRaises(InvalidScoringSystem, t.scores_detail)

    def test_tournament_scores_detail_finished(self):
        t = Tournament.objects.get(name='t3')
        scores = t.scores_detail()[0]
        self.assertEqual(len(scores), 1)
        # This should just be retrieved from the TournamentPlayer
        self.assertEqual(scores[t.tournamentplayer_set.get().player], 147.3)

    def test_tournament_scores_detail_unfinished(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        scores = t.scores_detail()

    def test_tournament_scores_detail_before_start(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        # Ensure that all TournamentPlayers are included. although there are no RoundPlayers
        scores = t.scores_detail()

    def test_tournament_scores_detail_with_non_player(self):
        # Only interesting for unfinished tournaments
        t = Tournament.objects.get(name='t1')
        # Add an extra player, who didn't actually play
        tp = TournamentPlayer(tournament=t, player=self.p10)
        tp.save()
        scores = t.scores_detail()
        # Players who didn't play should get a score of zero
        self.assertEqual(scores[0][self.p10], 0.0)
        tp.delete()

    # Tournament.positions_and_scores()
    def test_tournament_positions_and_scores_finished(self):
        t = Tournament.objects.get(name='t3')
        # TODO Validate results
        t.positions_and_scores()

    def test_tournament_positions_and_scores_unfinished(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        t.positions_and_scores()

    def test_tournament_positions_and_scores_with_unranked(self):
        t = Tournament.objects.get(name='t1')
        # Discard the round scores
        p_and_s = t.positions_and_scores()[0]
        # The unranked player should have a special position
        self.assertEqual(p_and_s[self.p5][0], Tournament.UNRANKED)
        # As everyone else has the same score, they should all be ranked (joint) first
        for k in p_and_s:
            if k != self.p5:
                self.assertEqual(p_and_s[k][0], 1)

    # Tournament.round_numbered()
    def test_tourney_round_numbered_negative(self):
        t = Tournament.objects.get(name='t1')
        self.assertRaises(Round.DoesNotExist, t.round_numbered, -1)

    def test_tourney_round_numbered_3(self):
        t = Tournament.objects.get(name='t1')
        self.assertEqual(t.round_numbered(3).number(), 3)

    # Tournament.best_countries()
    def test_tournament_best_countries_with_games(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        t.best_countries()

    def test_tournament_best_countries_without_games(self):
        t = Tournament.objects.get(name='t3')
        self.assertEqual({}, t.best_countries())

    def test_tournament_best_countries_with_unranked(self):
        t = Tournament.objects.get(name='t1')
        bc = t.best_countries()
        # The German solo should not be included
        for gp in bc[self.germany]:
            self.assertFalse(gp.player == self.p5)

    # Tournament.background()
    def test_tournament_background_without_players(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        t.background()

    def test_tournament_background_with_players(self):
        t = Tournament.objects.get(name='t3')
        # TODO Validate results
        t.background()

    def test_tournament_background_mask(self):
        t = Tournament.objects.get(name='t3')
        # Test each mask bit individually
        mask = 1
        while mask <= MASK_ALL_BG:
            with self.subTest(mask=mask):
                # TODO Validate results
                t.background(mask=mask)
                mask *= 2

    # Tournament.news()
    def test_tournament_news_in_progress(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        t.news()

    def test_tournament_news_ended(self):
        t = Tournament.objects.get(name='t3')
        # TODO Validate results
        t.news()

    # Tournament.current_round()
    def test_tourney_current_round_none(self):
        # All games in t3 are finished
        t = Tournament.objects.get(name='t3')
        self.assertIsNone(t.current_round())

    def test_tourney_current_round(self):
        t = Tournament.objects.get(name='t1')
        r = t.current_round()
        rounds = t.round_set.count()
        # All earlier rounds should be finished or in progress
        for i in range(1, r.number()):
            self.assertTrue(t.round_numbered(i).is_finished() or t.round_numbered(i).in_progress(),
                            'round %d' % i)
        # All later rounds should be not in progress
        for i in range(r.number() + 1, rounds + 1):
            self.assertFalse(t.round_numbered(i).in_progress(), 'round %d' % i)
        # This round should be unfinished
        self.assertFalse(r.is_finished())

    # Tournament.is_finished()
    def test_tourney_is_finished_some_rounds_over(self):
        t = Tournament.objects.get(name='t1')
        self.assertFalse(t.is_finished())

    def test_tourney_is_finished_no_rounds_over(self):
        t = Tournament.objects.get(name='t2')
        self.assertFalse(t.is_finished())

    def test_tourney_is_finished_all_rounds_over(self):
        t = Tournament.objects.get(name='t3')
        self.assertTrue(t.is_finished())

    def test_tourney_is_finished_no_rounds(self):
        t = Tournament.objects.create(name='Roundless',
                                      start_date=timezone.now(),
                                      end_date=timezone.now(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name)
        self.assertFalse(t.is_finished())

    # Tournament.wdd_url()
    def test_tournament_wdd_url(self):
        t = Tournament.objects.get(name='t3')
        t.wdd_tournament_id = 7
        self.assertTrue(t.wdd_url().endswith('?id_tournament=7'))

    def test_tournament_wdd_url_none(self):
        t = Tournament.objects.get(name='t3')
        self.assertEqual('', t.wdd_url())

    # Tournament.get_absolute_url()
    def test_tournament_get_absolute_url(self):
        t = Tournament.objects.get(name='t3')
        t.get_absolute_url()

    # TournamentPlayer.position()
    def test_tournamentplayer_position_finished(self):
        t = Tournament.objects.get(name='t3')
        # Should only be one
        tp = t.tournamentplayer_set.first()
        self.assertEqual(tp.position(), 1)

    # TournamentPlayer.roundplayers()
    def test_tournamentplayer_roundplayers(self):
        t = Tournament.objects.get(name='t3')
        tp = t.tournamentplayer_set.first()
        rps = tp.roundplayers()
        self.assertEqual(rps.count(), 2)

    # TournamentPlayer.create_preferences_from_string()
    # some of these also test prefs_string(), for convenience
    def test_tp_create_preferences_from_string_invalid(self):
        tp = TournamentPlayer.objects.first()
        self.assertEqual(tp.preference_set.count(), 0)
        self.assertRaises(InvalidPreferenceList,
                          tp.create_preferences_from_string,
                          'TPIAFGE')
        # Check that no Preferences were created
        self.assertEqual(tp.preference_set.count(), 0)

    def test_tp_create_preferences_from_string_duplicates(self):
        tp = TournamentPlayer.objects.first()
        self.assertEqual(tp.preference_set.count(), 0)
        self.assertRaises(InvalidPreferenceList,
                          tp.create_preferences_from_string,
                          'TRRAFGE')
        # Check that no Preferences were created
        self.assertEqual(tp.preference_set.count(), 0)

    def test_tp_create_preferences_from_string_replace(self):
        tp = TournamentPlayer.objects.first()
        self.assertEqual(tp.preference_set.count(), 0)
        tp.create_preferences_from_string('TRIAFGE')
        self.assertEqual(tp.preference_set.count(), 7)
        tp.create_preferences_from_string('AEFGI')
        self.assertEqual(tp.preference_set.count(), 5)
        # Check that the Preferences are correct
        prefs = list(tp.preference_set.all())
        self.assertEqual(prefs[0].ranking, 1)
        self.assertEqual(prefs[0].power, self.austria)
        self.assertEqual(prefs[1].ranking, 2)
        self.assertEqual(prefs[1].power, self.england)
        self.assertEqual(prefs[2].ranking, 3)
        self.assertEqual(prefs[2].power, self.france)
        self.assertEqual(prefs[3].ranking, 4)
        self.assertEqual(prefs[3].power, self.germany)
        self.assertEqual(prefs[4].ranking, 5)
        self.assertEqual(prefs[4].power, self.italy)
        self.assertEqual(tp.prefs_string(), 'AEFGI')
        tp.preference_set.all().delete()

    def test_tp_create_preferences_from_string_lowercase(self):
        tp = TournamentPlayer.objects.first()
        self.assertEqual(tp.preference_set.count(), 0)
        tp.create_preferences_from_string('triafge')
        self.assertEqual(tp.preference_set.count(), 7)
        # Check that the Preferences are correct
        prefs = list(tp.preference_set.all())
        self.assertEqual(prefs[0].ranking, 1)
        self.assertEqual(prefs[0].power, self.turkey)
        self.assertEqual(prefs[1].ranking, 2)
        self.assertEqual(prefs[1].power, self.russia)
        self.assertEqual(prefs[2].ranking, 3)
        self.assertEqual(prefs[2].power, self.italy)
        self.assertEqual(prefs[3].ranking, 4)
        self.assertEqual(prefs[3].power, self.austria)
        self.assertEqual(prefs[4].ranking, 5)
        self.assertEqual(prefs[4].power, self.france)
        self.assertEqual(prefs[5].ranking, 6)
        self.assertEqual(prefs[5].power, self.germany)
        self.assertEqual(prefs[6].ranking, 7)
        self.assertEqual(prefs[6].power, self.england)
        self.assertEqual(tp.prefs_string(), 'TRIAFGE')
        tp.preference_set.all().delete()

    def test_tp_create_preferences_from_string_uppercase(self):
        tp = TournamentPlayer.objects.first()
        self.assertEqual(tp.preference_set.count(), 0)
        tp.create_preferences_from_string('TRIAFGE')
        self.assertEqual(tp.preference_set.count(), 7)
        # Check that the Preferences are correct
        prefs = list(tp.preference_set.all())
        self.assertEqual(prefs[0].ranking, 1)
        self.assertEqual(prefs[0].power, self.turkey)
        self.assertEqual(prefs[1].ranking, 2)
        self.assertEqual(prefs[1].power, self.russia)
        self.assertEqual(prefs[2].ranking, 3)
        self.assertEqual(prefs[2].power, self.italy)
        self.assertEqual(prefs[3].ranking, 4)
        self.assertEqual(prefs[3].power, self.austria)
        self.assertEqual(prefs[4].ranking, 5)
        self.assertEqual(prefs[4].power, self.france)
        self.assertEqual(prefs[5].ranking, 6)
        self.assertEqual(prefs[5].power, self.germany)
        self.assertEqual(prefs[6].ranking, 7)
        self.assertEqual(prefs[6].power, self.england)
        self.assertEqual(tp.prefs_string(), 'TRIAFGE')
        tp.preference_set.all().delete()

    # TournamentPlayer.prefs_string()
    def test_tp_prefs_string(self):
        tp = TournamentPlayer.objects.first()
        self.assertEqual(tp.preference_set.count(), 0)
        self.assertEqual(tp.prefs_string(), '')

    # TournamentPlayer.get_prefs_url()
    def test_tp_get_prefs_url(self):
        # A TournamentPlayer with a uuid_str
        tp = TournamentPlayer.objects.filter(uuid_str='').first()
        tp._generate_uuid()
        self.assertIn('https://', tp.get_prefs_url())

    def test_tp_get_prefs_url_no_uuid(self):
        # A TournamentPlayer without a uuid_str
        tp = TournamentPlayer.objects.filter(uuid_str='').first()
        self.assertIn('https://', tp.get_prefs_url())

    # TODO TournamentPlayer.send_prefs_email()

    # TournamentPlayer.__str__()
    def test_tournamentplayer_str(self):
        tp = TournamentPlayer.objects.first()
        # TODO Validate result
        str(tp)

    # TODO TournamentPlayer.save()

    # validate_weight()
    def test_validate_weight_0(self):
        self.assertRaises(ValidationError, validate_weight, 0)

    def test_validate_weight_1(self):
        validate_weight(1)

    def test_validate_weight_10(self):
        validate_weight(10)

    # SeederBias.clean()
    def test_seederbias_clean_clone(self):
        '''Same player twice'''
        t = Tournament.objects.get(name='t1')
        tp1 = t.tournamentplayer_set.first()
        sb = SeederBias(player1=tp1,
                        player2=tp1,
                        weight=3)
        self.assertRaises(ValidationError, sb.clean)

    def test_seederbias_clean_mixup(self):
        '''Two players from different tournaments'''
        t = Tournament.objects.get(name='t1')
        tp1 = t.tournamentplayer_set.first()
        t = Tournament.objects.get(name='t3')
        tp2 = t.tournamentplayer_set.first()
        sb = SeederBias(player1=tp1,
                        player2=tp2,
                        weight=3)
        self.assertRaises(ValidationError, sb.clean)

    def test_seederbias_clean_ok(self):
        t = Tournament.objects.get(name='t1')
        tp1 = t.tournamentplayer_set.first()
        tp2 = t.tournamentplayer_set.last()
        sb = SeederBias(player1=tp1,
                        player2=tp2,
                        weight=3)
        sb.clean()

    # SeederBias.__str__()
    def test_seederbias_str(self):
        t = Tournament.objects.get(name='t1')
        tp1 = t.tournamentplayer_set.first()
        tp2 = t.tournamentplayer_set.last()
        sb = SeederBias(player1=tp1,
                        player2=tp2,
                        weight=3)
        # TODO Validate result
        str(sb)

    # Preference._str__()
    def test_preference_str(self):
        tp = TournamentPlayer.objects.first()
        self.assertEqual(tp.preference_set.count(), 0)
        tp.create_preferences_from_string('TRIAFGE')
        p = Preference.objects.first()
        # TODO Validate result
        str(p)
        tp.preference_set.all().delete()

    # Round.scores()
    def test_round_scores_invalid(self):
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=timezone.now(),
                                                      end_date=timezone.now(),
                                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                      round_scoring_system='Invalid System')
        r = Round.objects.create(tournament=t, scoring_system=G_SCORING_SYSTEMS[0].name, dias=True, start=t.start_date)
        self.assertRaises(InvalidScoringSystem, r.scores)

    def test_round_scores_finished(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.scores()

    def test_round_scores_unfinished(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.scores()

    def test_round_scores_recalculate(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.scores(True)

    def test_round_scores_with_unplayed(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # Add a RoundPlayer who didn't play
        rp = RoundPlayer(player=self.p9, the_round=r)
        rp.save()
        self.assertTrue(self.p9 in r.scores())
        rp.delete()

    # Round.is_finished()
    def test_round_is_finished_no_games_over(self):
        t = Tournament.objects.get(name='t1')
        r1 = t.round_numbered(1)
        self.assertFalse(r1.is_finished())

    def test_round_is_finished_some_games_over(self):
        t = Tournament.objects.get(name='t1')
        r2 = t.round_numbered(2)
        self.assertFalse(r2.is_finished())

    def test_round_is_finished_all_games_over(self):
        t = Tournament.objects.get(name='t1')
        r3 = t.round_numbered(3)
        self.assertTrue(r3.is_finished())

    def test_round_is_finished_no_games(self):
        """
        Rounds with no games can't have started, let alone finished
        """
        t = Tournament.objects.get(name='t1')
        r4 = t.round_numbered(4)
        self.assertFalse(r4.is_finished())

    # Round.in_progress()
    def test_round_in_progress_no_games_over(self):
        t = Tournament.objects.get(name='t1')
        r1 = t.round_numbered(1)
        self.assertTrue(r1.in_progress())

    def test_round_in_progress_some_games_over(self):
        t = Tournament.objects.get(name='t1')
        r2 = t.round_numbered(2)
        self.assertTrue(r2.in_progress())

    def test_round_in_progress_all_games_over(self):
        t = Tournament.objects.get(name='t1')
        r3 = t.round_numbered(3)
        self.assertFalse(r3.in_progress())

    def test_round_in_progress_no_games(self):
        """
        Rounds with round players but no games are just starting,
        and so are deemed to be "in progress".
        """
        t = Tournament.objects.get(name='t1')
        r4 = t.round_numbered(4)
        rp = RoundPlayer(player=self.p9, the_round=r4)
        rp.save()
        self.assertTrue(r4.in_progress())
        rp.delete()

    def test_round_in_progress_no_round_players(self):
        """
        Rounds with no round players haven't started
        """
        t = Tournament.objects.get(name='t1')
        r4 = t.round_numbered(4)
        self.assertFalse(r4.in_progress())

    # Round.number()
    def test_round_number_11(self):
        t = Tournament.objects.get(name='t1')
        r11 = t.round_set.all()[0]
        self.assertEqual(r11.number(), 1)

    def test_round_number_12(self):
        t = Tournament.objects.get(name='t1')
        r12 = t.round_set.all()[1]
        self.assertEqual(r12.number(), 2)

    def test_round_number_13(self):
        t = Tournament.objects.get(name='t1')
        r13 = t.round_set.all()[2]
        self.assertEqual(r13.number(), 3)

    def test_round_number_14(self):
        t = Tournament.objects.get(name='t1')
        r14 = t.round_set.all()[3]
        self.assertEqual(r14.number(), 4)

    def test_round_number_21(self):
        t = Tournament.objects.get(name='t2')
        r21 = t.round_set.all()[0]
        self.assertEqual(r21.number(), 1)

    def test_round_number_22(self):
        t = Tournament.objects.get(name='t2')
        r22 = t.round_set.all()[1]
        self.assertEqual(r22.number(), 2)

    # Round.leader_str()
    def test_round_leader_str_unfinished(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.leader_str()

    def test_round_leader_str_finished(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.leader_str()

    # Round.news()
    def test_round_news_unfinished(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.news()

    # Round.background()
    def test_round_background(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.background()

    def test_round_background_final_year(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.background()

    def test_round_background_timed_end(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[1]
        # TODO Validate results
        r.background()

    def test_round_background_mask(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[0]
        # Test each mask bit individually
        mask = 1
        while mask <= MASK_ALL_BG:
            with self.subTest(mask=mask):
                # TODO Validate results
                r.background(mask=mask)
                mask *= 2

    # Round.clean()
    def test_round_clean_missing_earliest_end(self):
        t = Tournament.objects.get(name='t1')
        s1 = G_SCORING_SYSTEMS[0].name
        r = Round(tournament=t,
                  scoring_system=s1,
                  dias=True,
                  start=t.start_date + HOURS_8,
                  earliest_end_time=t.start_date + HOURS_9)
        self.assertRaises(ValidationError, r.clean)

    def test_round_clean_missing_latest_end(self):
        t = Tournament.objects.get(name='t1')
        s1 = G_SCORING_SYSTEMS[0].name
        r = Round(tournament=t,
                  scoring_system=s1,
                  dias=True,
                  start=t.start_date + HOURS_8,
                  latest_end_time=t.start_date + HOURS_10)
        self.assertRaises(ValidationError, r.clean)

    # Round.get_absolute_url()
    def test_round_get_absolute_url(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[0]
        r.get_absolute_url()

    # Round.__str__()
    def test_round_str(self):
        r = Round.objects.first()
        # TODO Validate result
        str(r)

    # Game.assign_powers_from_prefs()
    def test_game_assign_powers_from_prefs(self):
        now = timezone.now()
        t = Tournament(name='t4',
                       start_date=now,
                       end_date=now,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=Tournament.SECRET)
        t.save()
        tp1 = TournamentPlayer(tournament=t, player=self.p1)
        tp1.save()
        tp2 = TournamentPlayer(tournament=t, player=self.p2)
        tp2.save()
        tp3 = TournamentPlayer(tournament=t, player=self.p3)
        tp3.save()
        tp4 = TournamentPlayer(tournament=t, player=self.p4)
        tp4.save()
        tp5 = TournamentPlayer(tournament=t, player=self.p5)
        tp5.save()
        tp6 = TournamentPlayer(tournament=t, player=self.p6)
        tp6.save()
        tp7 = TournamentPlayer(tournament=t, player=self.p7)
        tp7.save()
        # We need a previous round with a finished game
        r1 = Round(tournament=t,
                   scoring_system='Sum of Squares',
                   dias=True,
                   start=t.start_date)
        r1.save()
        g1 = Game(name='newgame1',
                  started_at=r1.start,
                  the_round=r1,
                  is_finished=True,
                  the_set=self.set1)
        g1.save()
        rp = RoundPlayer(the_round=r1, player=self.p1, score=30.0)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p2, score=25.0)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p3, score=20.0)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p4, score=10.0)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p5, score=7.0)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p6, score=7.0)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p7, score=1.0)
        rp.save()
        # Now we can do the round for the game we want to seed
        r2 = Round(tournament=t,
                   scoring_system='Sum of Squares',
                   dias=True,
                   start=t.start_date + HOURS_8)
        r2.save()
        rp = RoundPlayer(the_round=r2, player=self.p1)
        rp.save()
        rp = RoundPlayer(the_round=r2, player=self.p2)
        rp.save()
        rp = RoundPlayer(the_round=r2, player=self.p3)
        rp.save()
        rp = RoundPlayer(the_round=r2, player=self.p4)
        rp.save()
        rp = RoundPlayer(the_round=r2, player=self.p5)
        rp.save()
        rp = RoundPlayer(the_round=r2, player=self.p6)
        rp.save()
        rp = RoundPlayer(the_round=r2, player=self.p7)
        rp.save()
        g2 = Game(name='newgame2',
                  started_at=r2.start,
                  the_round=r2,
                  is_finished=False,
                  the_set=self.set1)
        g2.save()
        gp = GamePlayer(game=g2, player=self.p1)
        gp.save()
        gp = GamePlayer(game=g2, player=self.p2)
        gp.save()
        gp = GamePlayer(game=g2, player=self.p3)
        gp.save()
        gp = GamePlayer(game=g2, player=self.p4)
        gp.save()
        gp = GamePlayer(game=g2, player=self.p5)
        gp.save()
        gp = GamePlayer(game=g2, player=self.p6)
        gp.save()
        gp = GamePlayer(game=g2, player=self.p7)
        gp.save()
        # Now add preferences for some players
        p = Preference(player=tp1, power=self.austria, ranking=1)
        p.save()
        p = Preference(player=tp2, power=self.germany, ranking=1)
        p.save()
        p = Preference(player=tp2, power=self.turkey, ranking=2)
        p.save()
        p = Preference(player=tp3, power=self.austria, ranking=1)
        p.save()
        p = Preference(player=tp3, power=self.france, ranking=2)
        p.save()
        g2.assign_powers_from_prefs()
        # We need to retrieve the GamePlayers from the database to see the updates
        # No powers taken - get first preference
        gp = GamePlayer.objects.get(game=g2, player=self.p1)
        self.assertEqual(gp.power, self.austria)
        # First preference still available, should get it
        gp = GamePlayer.objects.get(game=g2, player=self.p2)
        self.assertEqual(gp.power, self.germany)
        # First preference gone, but second available, should get that
        gp = GamePlayer.objects.get(game=g2, player=self.p3)
        self.assertEqual(gp.power, self.france)
        # All preferences gone, should get a random available power
        for p in [self.p4, self.p5, self.p6, self.p7]:
            gp = GamePlayer.objects.get(game=g2, player=p)
            self.assertIn(gp.power, [self.england, self.italy, self.russia, self.turkey])
        # Note that this will also delete all GamePlayers for that Game
        g2.delete()
        g1.delete()
        # Note that this will also delete all RoundPlayers for that Round
        r2.delete()
        r1.delete()
        # Note that this will also delete all TournamentPlayers for that Tournament
        t.delete()
        self.assertEqual(Preference.objects.count(), 0)

    # TODO Game.assign_powers_from_prefs() raising PowerAlreadyAssigned

    # Game.create_or_update_sc_counts_from_ownerships
    def test_create_sc_count_invalid(self):
        # Arbitrary game
        g = Game.objects.first()
        self.assertRaises(SCOwnershipsNotFound, g.create_or_update_sc_counts_from_ownerships, 1901)

    def test_create_sc_count(self):
        test_data = {
                        SupplyCentre.objects.get(abbreviation='Sev'): self.austria,
                        SupplyCentre.objects.get(abbreviation='Mos'): self.austria,
                        SupplyCentre.objects.get(abbreviation='Edi'): self.france,
                        SupplyCentre.objects.get(abbreviation='Par'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Mun'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Tun'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Spa'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Por'): self.italy,
                        SupplyCentre.objects.get(abbreviation='Bud'): self.italy,
                        SupplyCentre.objects.get(abbreviation='Bul'): self.austria,
                    }
        # expected results
        res = {
                  self.austria : 0,
                  self.england: 0,
                  self.france: 0,
                  self.germany: 0,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey : 0,
              }
        # Arbitrary game
        g = Game.objects.first()
        # Add some SC ownerships for a far off year
        YEAR=1920
        scos = []
        for k,v in test_data.items():
            sco = SupplyCentreOwnership(sc=k, owner=v, year=YEAR, game=g)
            sco.save()
            scos.append(sco)
            res[v] += 1
        # Quickly check that no CentreCounts exist already
        self.assertEqual(0, g.centrecount_set.filter(year=YEAR).count())
        g.create_or_update_sc_counts_from_ownerships(YEAR)
        ccs = g.centrecount_set.filter(year=YEAR)
        # We should always have CentreCounts for all powers
        self.assertEqual(len(ccs), 7)
        self.assertEqual(ccs.aggregate(Sum('count'))['count__sum'], len(test_data))
        for cc in ccs:
            self.assertEqual(cc.count, res[cc.power])
        # Remove everything we added to the database
        for sco in scos:
            sco.delete()
        for cc in ccs:
            cc.delete()

    # Game.compare_sc_counts_and_ownerships()
    def test_game_compare_sc_counts_and_ownerships(self):
        test_data = {
                        SupplyCentre.objects.get(abbreviation='Sev'): self.austria,
                        SupplyCentre.objects.get(abbreviation='Mos'): self.austria,
                        SupplyCentre.objects.get(abbreviation='Edi'): self.france,
                        SupplyCentre.objects.get(abbreviation='Par'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Mun'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Tun'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Spa'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Por'): self.italy,
                        SupplyCentre.objects.get(abbreviation='Bud'): self.italy,
                        SupplyCentre.objects.get(abbreviation='Bul'): self.austria,
                    }
        # expected results
        res = {
                  self.austria : 0,
                  self.england: 0,
                  self.france: 0,
                  self.germany: 0,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey : 0,
              }
        # Arbitrary game
        g = Game.objects.first()
        # Add some SC ownerships for a far off year
        YEAR=1920
        scos = []
        for k,v in test_data.items():
            sco = SupplyCentreOwnership(sc=k, owner=v, year=YEAR, game=g)
            sco.save()
            scos.append(sco)
            res[v] += 1
        # Quickly check that no CentreCounts exist already
        self.assertEqual(0, g.centrecount_set.filter(year=YEAR).count())
        g.create_or_update_sc_counts_from_ownerships(YEAR)
        ccs = g.centrecount_set.filter(year=YEAR)
        # Hopefully everything matches!
        self.assertEqual([], g.compare_sc_counts_and_ownerships(YEAR))
        # Now modify one SupplyCentreOwnership to create a mismatch
        sco.owner = self.england
        sco.save()
        # That should give us two mismatches (the old and new owners)
        self.assertEqual(2, len(g.compare_sc_counts_and_ownerships(YEAR)))
        # Remove everything we added to the database
        for sco in scos:
            sco.delete()
        for cc in ccs:
            cc.delete()

    # TODO Game.compare_sc_counts_and_ownerships() raises SCOwnershipsNotFound

    # TODO Game.compare_sc_counts_and_ownerships() with missing CentreCount

    # Game.scores
    def test_update_sc_count(self):
        test_data = {
                        SupplyCentre.objects.get(abbreviation='Sev'): self.austria,
                        SupplyCentre.objects.get(abbreviation='Mos'): self.austria,
                        SupplyCentre.objects.get(abbreviation='Edi'): self.france,
                        SupplyCentre.objects.get(abbreviation='Par'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Mun'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Tun'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Spa'): self.germany,
                        SupplyCentre.objects.get(abbreviation='Por'): self.italy,
                        SupplyCentre.objects.get(abbreviation='Bud'): self.italy,
                        SupplyCentre.objects.get(abbreviation='Bul'): self.austria,
                    }
        # expected results
        res = {
                  self.austria : 0,
                  self.england: 0,
                  self.france: 0,
                  self.germany: 0,
                  self.italy: 0,
                  self.russia: 0,
                  self.turkey : 0,
              }
        # Arbitrary game
        g = Game.objects.first()
        # Add some SC ownerships for a far off year
        YEAR=1920
        scos = []
        for k,v in test_data.items():
            sco = SupplyCentreOwnership(sc=k, owner=v, year=YEAR, game=g)
            sco.save()
            scos.append(sco)
            res[v] += 1
        # Quickly check that no CentreCounts exist already
        self.assertEqual(0, g.centrecount_set.filter(year=YEAR).count())
        # Add some CentreCounts to be updated by the metho being tested
        cc = CentreCount(power=self.england, game=g, year=YEAR, count=17)
        cc = CentreCount(power=self.turkey, game=g, year=YEAR, count=17)
        g.create_or_update_sc_counts_from_ownerships(YEAR)
        ccs = g.centrecount_set.filter(year=YEAR)
        # We should always have CentreCounts for all powers
        self.assertEqual(len(ccs), 7)
        self.assertEqual(ccs.aggregate(Sum('count'))['count__sum'], len(test_data))
        for cc in ccs:
            self.assertEqual(cc.count, res[cc.power])
        # Remove everything we added to the database
        for sco in scos:
            sco.delete()
        for cc in ccs:
            cc.delete()

    # Game.scores
    def test_game_scores_invalid(self):
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=timezone.now(),
                                                      end_date=timezone.now(),
                                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                      round_scoring_system=R_SCORING_SYSTEMS[0].name)
        r = Round.objects.create(tournament=t, scoring_system='Invalid System', dias=True, start=t.start_date)
        g = Game.objects.create(name='gamey', started_at=r.start, the_round=r, the_set=self.set1)
        self.assertRaises(InvalidScoringSystem, g.scores)

    # Game.positions()
    def test_game_positions(self):
        g = Game.objects.first()
        # TODO Validate results
        g.positions()

    # Game.is_dias()
    def test_game_is_dias(self):
        for g in Game.objects.all():
            self.assertEqual(g.is_dias(), g.the_round.dias)

    # Game.years_played()
    def test_game_years_played_first(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.years_played()[0], 1900)

    def test_game_years_played_last(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.years_played()[-1], 1904)

    def test_game_years_played_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        self.assertEqual(g.years_played()[0], 1900)

    # Game.players()
    def test_game_players_default(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(len(g.players()), 7)
        for gp in g.players().values():
            self.assertEqual(len(gp), 1)

    def test_game_players_all(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(len(g.players(False)), 7)
        players = g.players(False)
        for power in players.keys():
            if power.abbreviation == u'A':
                self.assertEqual(len(players[power]), 2)
            else:
                self.assertEqual(len(players[power]), 1)

    def test_game_players_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(3).game_set.get(name='g15')
        self.assertEqual(len(g.players()), 7)
        for gp in g.players().values():
            self.assertEqual(len(gp), 0)

    # Game.news()
    def test_game_news(self):
        g = Game.objects.first()
        # TODO Validate results
        g.news()

    def test_game_news_with_name(self):
        g = Game.objects.first()
        # TODO Validate results
        g.news(include_game_name=True)

    def test_game_news_mask(self):
        g = Game.objects.first()
        # Test each mask bit individually
        mask = 1
        while mask <= MASK_ALL_NEWS:
            with self.subTest(mask=mask):
                # TODO Validate results
                g.news(mask=mask)
                mask *= 2

    def test_game_news_sc_gains_losses(self):
        # Austria lost three, flagging it as interesting
        # France gained three, making it interesting
        # Germany gained two and lost two, making it interesting
        # Italy gained three, and so is interesting
        # The rest are uninteresting, having only gained one or two
        # Both neutral dots and owned dots make powers interesting
        test_data = {
                     SupplyCentre.objects.get(abbreviation='Lon'): self.england,
                     SupplyCentre.objects.get(abbreviation='Lvp'): self.england,
                     SupplyCentre.objects.get(abbreviation='Edi'): self.england,
                     SupplyCentre.objects.get(abbreviation='Nwy'): self.england,
                     SupplyCentre.objects.get(abbreviation='Bre'): self.france,
                     SupplyCentre.objects.get(abbreviation='Par'): self.france,
                     SupplyCentre.objects.get(abbreviation='Mar'): self.france,
                     SupplyCentre.objects.get(abbreviation='Spa'): self.france,
                     SupplyCentre.objects.get(abbreviation='Por'): self.france,
                     SupplyCentre.objects.get(abbreviation='Mun'): self.france,
                     SupplyCentre.objects.get(abbreviation='Den'): self.germany,
                     SupplyCentre.objects.get(abbreviation='Hol'): self.germany,
                     SupplyCentre.objects.get(abbreviation='Kie'): self.germany,
                     SupplyCentre.objects.get(abbreviation='Ven'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Rom'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Nap'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Tri'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Vie'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Gre'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Ber'): self.russia,
                     SupplyCentre.objects.get(abbreviation='StP'): self.russia,
                     SupplyCentre.objects.get(abbreviation='War'): self.russia,
                     SupplyCentre.objects.get(abbreviation='Mos'): self.russia,
                     SupplyCentre.objects.get(abbreviation='Sev'): self.russia,
                     SupplyCentre.objects.get(abbreviation='Bud'): self.russia,
                     SupplyCentre.objects.get(abbreviation='Con'): self.turkey,
                     SupplyCentre.objects.get(abbreviation='Ank'): self.turkey,
                     SupplyCentre.objects.get(abbreviation='Smy'): self.turkey,
                     SupplyCentre.objects.get(abbreviation='Bul'): self.turkey,
                    }
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        # Add some SC ownerships that give us gains and losses
        for k,v in test_data.items():
            sco = SupplyCentreOwnership(sc=k, owner=v, year=1901, game=g)
            sco.save()
        g.create_or_update_sc_counts_from_ownerships(1901)
        # TODO Validate the result
        g.news()
        # Remove everything we added to the database
        for sco in g.supplycentreownership_set.filter(year=1901):
            sco.delete()
        for sc in g.centrecount_set.filter(year=1901):
            sc.delete()

    # Game.background()
    def test_game_background(self):
        g = Game.objects.first()
        # TODO Validate results
        g.background()

    def test_game_background_mask(self):
        g = Game.objects.first()
        # Test each mask bit individually
        mask = 1
        while mask <= MASK_ALL_BG:
            with self.subTest(mask=mask):
                # TODO Validate results
                g.background(mask=mask)
                mask *= 2

    # Game.passed_draw()
    def test_game_passed_draw_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp = DrawProposal.objects.create(game=g, year=1905, season='S', passed=False, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertIsNone(g.passed_draw())
        dp.delete()

    def test_game_passed_draw_other_game(self):
        t = Tournament.objects.get(name='t1')
        g2 = t.round_numbered(2).game_set.get(name='g13')
        g1 = t.round_numbered(2).game_set.get(name='g14')
        dp = DrawProposal.objects.create(game=g1, year=1905, season='S', passed=True, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertIsNone(g2.passed_draw())
        dp.delete()

    def test_game_passed_draw_one(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp = DrawProposal.objects.create(game=g, year=1905, season='S', passed=True, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(g.passed_draw(), dp)
        dp.delete()

    def test_game_passed_draw_two(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp1 = DrawProposal.objects.create(game=g, year=1905, season='S', passed=False, proposer=self.austria,
                                          power_1=self.austria, power_2=self.england, power_3=self.france,
                                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        dp2 = DrawProposal.objects.create(game=g, year=1905, season='F', passed=True, proposer=self.austria,
                                          power_1=self.austria, power_2=self.england, power_3=self.france,
                                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(g.passed_draw(), dp2)
        dp1.delete()
        dp2.delete()

    # Game.board_toppers()
    def test_game_board_toppers_soloed(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        bt = g.board_toppers()
        self.assertEqual(len(bt), 1)
        bt = bt[0]
        self.assertEqual(bt.game, g)
        self.assertEqual(bt.year, 1904)
        self.assertEqual(bt.power, self.germany)
        self.assertEqual(bt.count, 18)

    def test_game_board_toppers_start(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        bt = g.board_toppers()
        self.assertEqual(len(bt), 1)
        bt = bt[0]
        self.assertEqual(bt.game, g)
        self.assertEqual(bt.year, 1900)
        self.assertEqual(bt.power, self.russia)
        self.assertEqual(bt.count, 4)

    # TODO Test board_toppers() returning more than one CentreCount

    # Game.neutrals()
    def test_game_neutrals_1900(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.neutrals(1900), 34 - (6*3 + 4))

    def test_game_neutrals_1901(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.neutrals(1901), 34 - (4*5 + 3*4))

    def test_game_neutrals_1899(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertRaises(InvalidYear, g.neutrals, 1899)

    def test_game_neutrals_1904(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.neutrals(1904), 0)

    def test_game_neutrals_1905(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertRaises(InvalidYear, g.neutrals, 1905)

    def test_game_neutrals_default(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.neutrals(), 0)

    def test_game_neutrals_none_default(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        self.assertEqual(g.neutrals(), 34 - (6*3 + 4))

    # Game.final_year()
    def test_game_final_year_1904(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.final_year(), 1904)

    def test_game_final_year_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        self.assertEqual(g.final_year(), 1900)

    # Game.soloer()
    def test_game_soloer_somebody(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.soloer().player, self.p5)
        self.assertEqual(g.soloer().game, g)

    def test_game_soloer_nobody(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        self.assertIsNone(g.soloer())

    # Game.survivors()
    def test_game_survivors(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        # survivors() just returns surviving players, regardless of whether they
        # lost to a solo or were excluded from a draw
        self.assertEqual(len(g.survivors()), 6)

    def test_game_survivors_year_1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(len(g.survivors(1901)), 7)

    def test_game_survivors_year_2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        # survivors() just returns surviving players, regardless of whether they
        # lost to a solo or were excluded from a draw
        self.assertEqual(len(g.survivors(1904)), 6)

    def test_game_survivors_invalid_year(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(len(g.survivors(1905)), 0)

    # Game.result_str()
    def test_game_result_str_soloed(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIn(' won by ', g.result_str())

    def test_game_result_str_in_progress(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        self.assertIsNone(g.result_str())

    def test_game_result_str_passed_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.austria,
                                    power_1=self.austria, power_2=self.england, power_3=self.france,
                                    power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertIn('Vote passed ', g.result_str())

    def test_game_result_str_conceded(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.england,
                                    power_1=self.england)
        self.assertIn('conceded ', g.result_str())

    def test_game_result_str_failed_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        DrawProposal.objects.create(game=g, year=1901, season='S', passed=False, proposer=self.austria,
                                    power_1=self.austria, power_2=self.england, power_3=self.france,
                                    power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        # Game is still ongoing
        self.assertIsNone(g.result_str())

    # TODO Add test of game that reached fixed endpoint

    # Game.clean()
    def test_game_clean_non_unique_name(self):
        g1 = Game.objects.first()
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(4)
        g2 = Game(name='g13',
                  started_at=g1.started_at + HOURS_8,
                  the_round=r,
                  is_finished=False,
                  the_set=g1.the_set)
        self.assertRaises(ValidationError, g2.clean)

    # Game.save()
    def test_game_save_new_game(self):
        g1 = Game.objects.first()
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(4)
        g2 = Game(name='newgame',
                  started_at=g1.started_at + HOURS_8,
                  the_round=r,
                  is_finished=False,
                  the_set=g1.the_set)
        g2.save()
        # We should now have initial image and SC ownership
        # Starting position
        self.assertEqual(g2.gameimage_set.count(), 1)
        # CentreCounts for each of the 7 GreatPowers
        self.assertEqual(g2.centrecount_set.count(), 7)
        # 22 home SCs owned
        self.assertEqual(g2.supplycentreownership_set.count(), 22)
        g2.delete()

    def test_game_save_change_set(self):
        g1 = Game.objects.first()
        self.assertEqual(g1.the_set, self.set1)
        g1.the_set = self.set2
        g1.save()
        # TODO Verify that the initial image has been updated

    @tag('slow')
    def test_game_save_end_of_game(self):
        now = timezone.now()
        t = Tournament(name='t4',
                       start_date=now,
                       end_date=now,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=Tournament.SECRET)
        t.save()
        tp = TournamentPlayer(tournament=t, player=self.p1)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p2)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p3)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p4)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p5)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p6)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p7)
        tp.save()
        r = Round(tournament=t,
                  scoring_system='Sum of Squares',
                  dias=True,
                  start=t.start_date)
        r.save()
        rp = RoundPlayer(the_round=r, player=self.p1)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p2)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p3)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p4)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p5)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p6)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p7)
        rp.save()
        g1 = Game(name='newgame1',
                  started_at=r.start,
                  the_round=r,
                  is_finished=False,
                  the_set=self.set1)
        g1.save()
        gp = GamePlayer(game=g1, player=self.p1, power=self.austria)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p2, power=self.england)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p3, power=self.france)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p4, power=self.germany)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p5, power=self.italy)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p6, power=self.russia)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p7, power=self.turkey)
        gp.save()
        # Add a second, ongoing, game
        g2 = Game(name='newgame2',
                  started_at=r.start,
                  the_round=r,
                  is_finished=False,
                  the_set=self.set1)
        g2.save()
        g1.is_finished = True
        g1.save()
        # Scores should be recorded for the game
        for gp in g1.gameplayer_set.all():
            if gp.power == self.russia:
                self.assertAlmostEqual(gp.score, 100.0 * 16 / 70)
            else:
                self.assertAlmostEqual(gp.score, 100.0 * 9 / 70)
        # But not for the Round
        for rp in r.roundplayer_set.all():
            self.assertEqual(rp.score, 0.0)
        g2.delete()
        # Note that this will also delete all GamePlayers for that Game
        g1.delete()
        # Note that this will also delete all RoundPlayers for that Round
        r.delete()
        # Note that this will also delete all TournamentPlayers for that Tournament
        t.delete()

    @tag('slow')
    def test_game_save_end_of_round(self):
        now = timezone.now()
        t = Tournament(name='t4',
                       start_date=now,
                       end_date=now,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=Tournament.SECRET)
        t.save()
        tp = TournamentPlayer(tournament=t, player=self.p1)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p2)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p3)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p4)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p5)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p6)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p7)
        tp.save()
        r = Round(tournament=t,
                 scoring_system='Sum of Squares',
                 dias=True,
                 start=t.start_date)
        r.save()
        rp = RoundPlayer(the_round=r, player=self.p1)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p2)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p3)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p4)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p5)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p6)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p7)
        rp.save()
        g1 = Game(name='newgame1',
                  started_at=r.start,
                  the_round=r,
                  is_finished=False,
                  the_set=self.set1)
        g1.save()
        gp = GamePlayer(game=g1, player=self.p1, power=self.austria)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p2, power=self.england)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p3, power=self.france)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p4, power=self.germany)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p5, power=self.italy)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p6, power=self.russia)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p7, power=self.turkey)
        gp.save()
        g1.is_finished = True
        g1.save()
        # Scores should be recorded for the game
        for gp in g1.gameplayer_set.all():
            if gp.power == self.russia:
                self.assertAlmostEqual(gp.score, 100.0 * 16 / 70)
            else:
                self.assertAlmostEqual(gp.score, 100.0 * 9 / 70)
        # And for the Round
        for rp in r.roundplayer_set.all():
            if rp.player == self.p6:
                self.assertAlmostEqual(rp.score, 100.0 * 16 / 70)
            else:
                self.assertAlmostEqual(rp.score, 100.0 * 9 / 70)
        # And for the Tournament
        for tp in t.tournamentplayer_set.all():
            if tp.player == self.p6:
                self.assertAlmostEqual(tp.score, 100.0 * 16 / 70)
            else:
                self.assertAlmostEqual(tp.score, 100.0 * 9 / 70)
        # Note that this will also delete all GamePlayers for that Game
        g1.delete()
        # Note that this will also delete all RoundPlayers for that Round
        r.delete()
        # Note that this will also delete all TournamentPlayers for that Tournament
        t.delete()

    @tag('slow')
    def test_game_save_end_of_tournament(self):
        now = timezone.now()
        t = Tournament(name='t4',
                       start_date=now,
                       end_date=now,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=Tournament.SECRET)
        t.save()
        tp = TournamentPlayer(tournament=t, player=self.p1)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p2)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p3)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p4)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p5)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p6)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p7)
        tp.save()
        # Include a player who didn't play any games
        tp = TournamentPlayer(tournament=t, player=self.p8)
        tp.save()
        r = Round(tournament=t,
                  scoring_system='Sum of Squares',
                  dias=True,
                  start=t.start_date)
        r.save()
        rp = RoundPlayer(the_round=r, player=self.p1)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p2)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p3)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p4)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p5)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p6)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p7)
        rp.save()
        g1 = Game(name='newgame1',
                  started_at=r.start,
                  the_round=r,
                  is_finished=False,
                  the_set=self.set1)
        g1.save()
        gp = GamePlayer(game=g1, player=self.p1, power=self.austria)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p2, power=self.england)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p3, power=self.france)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p4, power=self.germany)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p5, power=self.italy)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p6, power=self.russia)
        gp.save()
        gp = GamePlayer(game=g1, player=self.p7, power=self.turkey)
        gp.save()
        # Add a second, ongoing, game
        g2 = Game(name='newgame2',
                  started_at=r.start,
                  the_round=r,
                  is_finished=False,
                  the_set=self.set1)
        g2.save()
        g1.is_finished = True
        g1.save()
        # Scores should be recorded for the game
        for gp in g1.gameplayer_set.all():
            if gp.power == self.russia:
                self.assertAlmostEqual(gp.score, 100.0 * 16 / 70)
            else:
                self.assertAlmostEqual(gp.score, 100.0 * 9 / 70)
        # But not for the Round
        for rp in r.roundplayer_set.all():
            self.assertEqual(rp.score, 0.0)
        g2.delete()
        # Note that this will also delete all GamePlayers for that Game
        g1.delete()
        # Note that this will also delete all RoundPlayers for that Round
        r.delete()
        # Note that this will also delete all TournamentPlayers for that Tournament
        t.delete()

    # Game.get_absolute_url()
    def test_game_get_absolute_url(self):
        g = Game.objects.first()
        g.get_absolute_url()

    # SupplyCentreOwnership.__str__()
    def test_supplycentreownership_str(self):
        g = Game.objects.first()
        sc = SupplyCentre.objects.get(abbreviation='Mun')
        sco = SupplyCentreOwnership.objects.create(sc=sc, owner=self.austria, year=1909, game=g)
        # TODO validate result
        str(sco)

    # DrawProposal.draw_size()
    def test_draw_proposal_draw_size_one(self):
        g = Game.objects.first()
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria)
        self.assertEqual(dp.draw_size(), 1)

    def test_draw_proposal_draw_size_all(self):
        g = Game.objects.first()
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(dp.draw_size(), 7)

    # DrawProposal.powers()
    def test_draw_proposal_powers_one(self):
        g = Game.objects.first()
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria)
        self.assertEqual(len(dp.powers()), 1)

    def test_draw_proposal_powers_all(self):
        g = Game.objects.first()
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(len(dp.powers()), 7)

    # DrawProposal.power_is_part()
    def test_draw_proposal_power_is_part_one(self):
        g = Game.objects.first()
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria)
        self.assertEqual(dp.power_is_part(self.austria), True)
        self.assertEqual(dp.power_is_part(self.england), False)
        self.assertEqual(dp.power_is_part(self.france), False)
        self.assertEqual(dp.power_is_part(self.germany), False)
        self.assertEqual(dp.power_is_part(self.italy), False)
        self.assertEqual(dp.power_is_part(self.russia), False)
        self.assertEqual(dp.power_is_part(self.turkey), False)

    def test_draw_proposal_power_is_part_all(self):
        g = Game.objects.first()
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(dp.power_is_part(self.austria), True)
        self.assertEqual(dp.power_is_part(self.england), True)
        self.assertEqual(dp.power_is_part(self.france), True)
        self.assertEqual(dp.power_is_part(self.germany), True)
        self.assertEqual(dp.power_is_part(self.italy), True)
        self.assertEqual(dp.power_is_part(self.russia), True)
        self.assertEqual(dp.power_is_part(self.turkey), True)

    # DrawProposal.votes_against()
    def test_draw_proposal_votes_against_none(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal(game=g, year=1910, season='F', votes_in_favour=7, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(dp.votes_against(), 0)

    def test_draw_proposal_votes_against_some(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal(game=g, year=1910, season='F', votes_in_favour=2, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(dp.votes_against(), 5)

    def test_draw_proposal_votes_against_exception(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertRaises(TypeError, dp.votes_against)

    # DrawProposal.clean()
    def test_draw_proposal_clean_with_duplicates(self):
        g = Game.objects.first()
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.austria)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_clean_with_gap(self):
        g = Game.objects.first()
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_3=self.england)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_with_dead_powers(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1905, season='S', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_missing_power_dias(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1901, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_too_late(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1903, season='F', passed=True, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_multiple_successful(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp1 = DrawProposal.objects.create(game=g, year=1901, season='F', passed=True, proposer=self.austria,
                                          power_1=self.austria, power_2=self.england, power_3=self.france,
                                          power_4=self.germany, power_5=self.italy, power_6=self.russia,
                                          power_7=self.turkey)
        dp2 = DrawProposal(game=g, year=1901, season='F', passed=True, proposer=self.austria,
                           power_1=self.austria, power_2=self.england, power_3=self.france,
                           power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertRaises(ValidationError, dp2.clean)
        dp1.delete()

    # TODO DrawProposal.clean() with passed not set in a tournament with SECRET draw votes
    # TODO DrawProposal.clean() with votes_in_favour not set in a tournament with COUNTS draw votes
    # TODO DrawProposal.clean() sets passed from votes_in_favour correctly

    # TODO DrawProposal.save()

    # DrawProposal.__str__()
    def test_drawproposal_str(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g, year=1901, season='F', passed=True, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia,
                                         power_7=self.turkey)
        # TODO Validate result
        str(dp)

    # RoundPlayer.tournamentplayer()
    def test_round_player_tournamentplayer(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(1)
        rp = r.roundplayer_set.get(player=self.p8)
        tp = rp.tournamentplayer()
        self.assertEqual(tp.player, self.p8)
        self.assertEqual(tp.tournament, t)

    # RoundPlayer.gameplayers()
    def test_roundplayer_gameplayers_1(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(1)
        rp = RoundPlayer.objects.get(player=self.p8, the_round=r)
        # Player 8 is only in game g11
        self.assertEqual(rp.gameplayers().count(), 1)

    def test_roundplayer_gameplayers_2(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(1)
        rp = RoundPlayer.objects.get(player=self.p1, the_round=r)
        # Player 2 is in games g11 and g12
        self.assertEqual(rp.gameplayers().count(), 2)

    # RoundPlayer.clean()
    def test_roundplayer_clean(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(1)
        p = Player.objects.first()
        rp = RoundPlayer(player=p, the_round=r)
        self.assertRaises(ValidationError, rp.clean)

    # RoundPlayer.__str__()
    def test_roundplayer_str(self):
        rp = RoundPlayer.objects.first()
        # TODO Validate result
        str(rp)

    # GamePlayer.roundplayer()
    def test_gameplayer_roundplayer(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(1)
        g = r.game_set.get(name='g11')
        gp = g.gameplayer_set.get(player=self.p8)
        rp = gp.roundplayer()
        self.assertEqual(rp.player, self.p8)
        self.assertEqual(rp.the_round, r)

    # GamePlayer.tournamentplayer()
    def test_gameplayer_tournamentplayer(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(1)
        g = r.game_set.get(name='g11')
        gp = g.gameplayer_set.get(player=self.p8)
        tp = gp.tournamentplayer()
        self.assertEqual(tp.player, self.p8)
        self.assertEqual(tp.tournament, t)

    # TODO GamePlayer.preferences()
    # This is indirectly tested via GamePlayer.set_power_from_prefs(), below

    # GamePlayer.elimination_year()
    def test_gameplayer_elimination_year_replacement(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        gp = g.gameplayer_set.filter(power=self.austria).first()
        self.assertEqual(gp.elimination_year(), None)
        gp = g.gameplayer_set.filter(power=self.austria).last()
        self.assertEqual(gp.elimination_year(), 1904)

    def test_gameplayer_elimination_year_not_eliminated(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        gp = g.gameplayer_set.get(power=self.england)
        self.assertEqual(gp.elimination_year(), None)

    # GamePlayer.set_power_from_prefs()
    def test_gameplayer_set_power_from_prefs(self):
        now = timezone.now()
        t = Tournament(name='t4',
                       start_date=now,
                       end_date=now,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=Tournament.SECRET)
        t.save()
        tp1 = TournamentPlayer(tournament=t, player=self.p1)
        tp1.save()
        tp2 = TournamentPlayer(tournament=t, player=self.p2)
        tp2.save()
        tp3 = TournamentPlayer(tournament=t, player=self.p3)
        tp3.save()
        tp4 = TournamentPlayer(tournament=t, player=self.p4)
        tp4.save()
        tp5 = TournamentPlayer(tournament=t, player=self.p5)
        tp5.save()
        tp6 = TournamentPlayer(tournament=t, player=self.p6)
        tp6.save()
        tp7 = TournamentPlayer(tournament=t, player=self.p7)
        tp7.save()
        r = Round(tournament=t,
                  scoring_system='Sum of Squares',
                  dias=True,
                  start=t.start_date)
        r.save()
        rp = RoundPlayer(the_round=r, player=self.p1)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p2)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p3)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p4)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p5)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p6)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p7)
        rp.save()
        g1 = Game(name='newgame1',
                  started_at=r.start,
                  the_round=r,
                  is_finished=False,
                  the_set=self.set1)
        g1.save()
        gp1 = GamePlayer(game=g1, player=self.p1)
        gp1.save()
        gp2 = GamePlayer(game=g1, player=self.p2)
        gp2.save()
        gp3 = GamePlayer(game=g1, player=self.p3)
        gp3.save()
        gp4 = GamePlayer(game=g1, player=self.p4)
        gp4.save()
        gp5 = GamePlayer(game=g1, player=self.p5)
        gp5.save()
        gp6 = GamePlayer(game=g1, player=self.p6)
        gp6.save()
        gp7 = GamePlayer(game=g1, player=self.p7)
        gp7.save()
        # Now add preferences for some players
        p = Preference(player=tp1, power=self.austria, ranking=1)
        p.save()
        p = Preference(player=tp2, power=self.germany, ranking=1)
        p.save()
        p = Preference(player=tp2, power=self.turkey, ranking=2)
        p.save()
        p = Preference(player=tp3, power=self.austria, ranking=1)
        p.save()
        p = Preference(player=tp3, power=self.france, ranking=2)
        p.save()
        # No powers taken - get first preference
        gp1.set_power_from_prefs()
        self.assertEqual(gp1.power, self.austria)
        # First preference still available, should get it
        gp2.set_power_from_prefs()
        self.assertEqual(gp2.power, self.germany)
        # First preference gone, but second available, should get that
        gp3.set_power_from_prefs()
        self.assertEqual(gp3.power, self.france)
        # All preferences gone, should get a random available power
        gp4.set_power_from_prefs()
        self.assertIn(gp4.power, [self.england, self.italy, self.russia, self.turkey])
        # Note that this will also delete all GamePlayers for that Game
        g1.delete()
        # Note that this will also delete all RoundPlayers for that Round
        r.delete()
        # Note that this will also delete all TournamentPlayers for that Tournament
        t.delete()
        self.assertEqual(Preference.objects.count(), 0)

    # GamePlayer.clean()
    def test_gameplayer_clean_player_not_in_tournament(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        gp = GamePlayer(player=Player.objects.first(),
                        game=g,
                        power=self.austria)
        self.assertRaises(ValidationError, gp.clean)

    def test_gameplayer_clean_player_missing_last_year(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        tp = TournamentPlayer(player=self.p9, tournament=t)
        gp = GamePlayer(player=self.p9,
                        game=g,
                        power=self.austria,
                        last_year=1909)
        tp.save()
        self.assertRaises(ValidationError, gp.clean)
        tp.delete()

    def test_gameplayer_clean_player_missing_last_season(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        tp = TournamentPlayer(player=self.p9, tournament=t)
        gp = GamePlayer(player=self.p9,
                        game=g,
                        power=self.austria,
                        last_season='S')
        tp.save()
        self.assertRaises(ValidationError, gp.clean)
        tp.delete()

    def test_gameplayer_clean_overlap_1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(3).game_set.get(name='g15')
        tp1 = TournamentPlayer(player=self.p9, tournament=t)
        tp2 = TournamentPlayer(player=self.p10, tournament=t)
        gp1 = GamePlayer(player=self.p9,
                         game=g,
                         power=self.austria)
        gp2 = GamePlayer(player=self.p10,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        tp1.save()
        tp2.save()
        gp1.clean()
        gp1.save()
        self.assertRaises(ValidationError, gp2.clean)
        gp1.delete()
        tp2.delete()
        tp1.delete()

    def test_gameplayer_clean_overlap_2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(3).game_set.get(name='g15')
        tp1 = TournamentPlayer(player=self.p9, tournament=t)
        tp2 = TournamentPlayer(player=self.p10, tournament=t)
        gp1 = GamePlayer(player=self.p9,
                         game=g,
                         power=self.austria,
                         last_year=1902,
                         last_season='S')
        gp2 = GamePlayer(player=self.p10,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        tp1.save()
        tp2.save()
        gp1.clean()
        gp1.save()
        self.assertRaises(ValidationError, gp2.clean)
        gp1.delete()
        tp2.delete()
        tp1.delete()

    def test_gameplayer_clean_overlap_3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(3).game_set.get(name='g15')
        tp1 = TournamentPlayer(player=self.p9, tournament=t)
        tp2 = TournamentPlayer(player=self.p10, tournament=t)
        gp1 = GamePlayer(player=self.p9,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        gp2 = GamePlayer(player=self.p10,
                         game=g,
                         power=self.austria,
                         last_year=1902,
                         last_season='S')
        tp1.save()
        tp2.save()
        gp1.clean()
        gp1.save()
        self.assertRaises(ValidationError, gp2.clean)
        gp1.delete()
        tp2.delete()
        tp1.delete()

    def test_gameplayer_clean_overlap_4(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(3).game_set.get(name='g15')
        tp1 = TournamentPlayer(player=self.p9, tournament=t)
        tp2 = TournamentPlayer(player=self.p10, tournament=t)
        gp1 = GamePlayer(player=self.p9,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        gp2 = GamePlayer(player=self.p10,
                         game=g,
                         power=self.austria)
        tp1.save()
        tp2.save()
        gp1.clean()
        gp1.save()
        self.assertRaises(ValidationError, gp2.clean)
        gp1.delete()
        tp2.delete()
        tp1.delete()

    def test_gameplayer_clean_overlap_5(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(3).game_set.get(name='g15')
        tp1 = TournamentPlayer(player=self.p9, tournament=t)
        tp2 = TournamentPlayer(player=self.p10, tournament=t)
        gp1 = GamePlayer(player=self.p9,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        gp2 = GamePlayer(player=self.p10,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        tp1.save()
        tp2.save()
        gp1.clean()
        gp1.save()
        self.assertRaises(ValidationError, gp2.clean)
        gp1.delete()
        tp2.delete()
        tp1.delete()

    # GamePlayer.__str__()
    def test_gameplayer_str_with_power(self):
        gp = GamePlayer.objects.filter(power__isnull=False).first()
        # TODO Validate result
        str(gp)

    def test_gameplayer_str_no_power(self):
        g = Game.objects.first()
        gp = GamePlayer.objects.create(player=self.p8, game=g)
        # TODO Validate result
        str(gp)

    # GameImage.turn_str()
    def test_gameimage_turn_str(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        gi = GameImage.objects.get(game=g)
        self.assertEqual(gi.turn_str(), 'S1901M')

    # GameImage.clean()
    def test_gameimage_clean(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        gi1 = GameImage.objects.get(game=g)
        gi2 = GameImage(game=g, year=1902, season=SPRING, phase=GameImage.ADJUSTMENTS, image=gi1.image)
        self.assertRaises(ValidationError, gi2.clean)

    # GameImage.get_absolute_url()
    def test_game_image_get_absolute_url(self):
        gi = GameImage.objects.first()
        gi.get_absolute_url()

    # GameImage.__str__()
    def test_gameimage_str(self):
        gi = GameImage.objects.first()
        # TODO Validate result
        str(gi)

    # CentreCount.clean()
    def test_centrecount_clean_past_final_year(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        cc = CentreCount(power=self.austria, game=g, year=1908, count=7)
        self.assertRaises(ValidationError, cc.clean)

    def test_centrecount_clean_up_from_zero(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        cc1 = CentreCount(power=self.austria, game=g, year=1902, count=0)
        cc2 = CentreCount(power=self.austria, game=g, year=1903, count=1)
        cc1.save()
        self.assertRaises(ValidationError, cc2.clean)
        cc1.delete()

    def test_centrecount_clean_more_than_double(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        cc1 = CentreCount(power=self.austria, game=g, year=1902, count=5)
        cc2 = CentreCount(power=self.austria, game=g, year=1903, count=11)
        cc1.save()
        self.assertRaises(ValidationError, cc2.clean)
        cc1.delete()

    # Make sure that Issue #44 hasn't re-appeared
    # We should be able to save the CentreCounts for all 7 powers for the final game year
    def test_issue_44_1(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(4)
        r = Round.objects.create(tournament=t,
                                 scoring_system='Sum of Squares',
                                 dias=True,
                                 start=timezone.now() + HOURS_24,
                                 final_year=1910)
        g = Game.objects.create(name='g41', started_at=r.start, the_round=r, the_set=self.set1)
        # TODO Remove reliance on primary keys
        gp1 = GamePlayer.objects.create(player=Player.objects.get(pk=7), game=g, power=self.austria)
        gp2 = GamePlayer.objects.create(player=Player.objects.get(pk=6), game=g, power=self.england)
        gp3 = GamePlayer.objects.create(player=Player.objects.get(pk=5), game=g, power=self.france)
        gp4 = GamePlayer.objects.create(player=Player.objects.get(pk=4), game=g, power=self.germany)
        gp5 = GamePlayer.objects.create(player=Player.objects.get(pk=3), game=g, power=self.italy)
        gp6 = GamePlayer.objects.create(player=Player.objects.get(pk=2), game=g, power=self.russia)
        gp7 = GamePlayer.objects.create(player=Player.objects.get(pk=1), game=g, power=self.turkey)
        cc0 = CentreCount(game=g, count=0, power=self.austria, year=r.final_year - 1)
        cc0.save()
        cc1 = CentreCount(game=g, count=0, power=self.austria, year=r.final_year)
        cc1.save()
        cc2 = CentreCount(game=g, count=0, power=self.england, year=r.final_year)
        cc2.save()
        cc3 = CentreCount(game=g, count=9, power=self.france, year=r.final_year)
        cc3.save()
        cc4 = CentreCount(game=g, count=9, power=self.germany, year=r.final_year)
        cc4.save()
        cc5 = CentreCount(game=g, count=2, power=self.italy, year=r.final_year)
        cc5.save()
        cc6 = CentreCount(game=g, count=7, power=self.russia, year=r.final_year)
        cc6.save()
        cc7 = CentreCount(game=g, count=7, power=self.turkey, year=r.final_year)
        cc7.save()
        # We no longer expect CentreCount.save() to update Game.is_finished
        self.assertFalse(g.is_finished)
        cc0.delete()
        cc1.delete()
        cc2.delete()
        cc3.delete()
        cc4.delete()
        cc5.delete()
        cc6.delete()
        cc7.delete()
        gp1.delete()
        gp2.delete()
        gp3.delete()
        gp4.delete()
        gp5.delete()
        gp6.delete()
        gp7.delete()
        g.delete()
        r.delete()

    # We should be able to save the CentreCounts for all 7 powers for a game with a soloer
    def test_issue_44_2(self):
        t = Tournament.objects.get(name='t1')
        r = Round.objects.create(tournament=t,
                                 scoring_system='Sum of Squares',
                                 dias=True,
                                 start=timezone.now() + HOURS_24,
                                 final_year=1910)
        g = Game.objects.create(name='g41', started_at=r.start, the_round=r, the_set=self.set1)
        # TODO Remove reliance on primary keys
        gp1 = GamePlayer.objects.create(player=Player.objects.get(pk=7), game=g, power=self.austria)
        gp2 = GamePlayer.objects.create(player=Player.objects.get(pk=6), game=g, power=self.england)
        gp3 = GamePlayer.objects.create(player=Player.objects.get(pk=5), game=g, power=self.france)
        gp4 = GamePlayer.objects.create(player=Player.objects.get(pk=4), game=g, power=self.germany)
        gp5 = GamePlayer.objects.create(player=Player.objects.get(pk=3), game=g, power=self.italy)
        gp6 = GamePlayer.objects.create(player=Player.objects.get(pk=2), game=g, power=self.russia)
        gp7 = GamePlayer.objects.create(player=Player.objects.get(pk=1), game=g, power=self.turkey)
        cc1 = CentreCount(game=g, count=0, power=self.austria, year=r.final_year)
        cc1.save()
        cc2 = CentreCount(game=g, count=0, power=self.england, year=r.final_year)
        cc2.save()
        cc3 = CentreCount(game=g, count=7, power=self.france, year=r.final_year)
        cc3.save()
        cc4 = CentreCount(game=g, count=7, power=self.germany, year=r.final_year)
        cc4.save()
        cc5 = CentreCount(game=g, count=2, power=self.italy, year=r.final_year)
        cc5.save()
        cc6 = CentreCount(game=g, count=18, power=self.russia, year=r.final_year)
        cc6.save()
        cc7 = CentreCount(game=g, count=0, power=self.turkey, year=r.final_year)
        cc7.save()
        # We no longer expect CentreCount.save() to update Game.is_finished
        self.assertFalse(g.is_finished)
        cc1.delete()
        cc2.delete()
        cc3.delete()
        cc4.delete()
        cc5.delete()
        cc6.delete()
        cc7.delete()
        gp1.delete()
        gp2.delete()
        gp3.delete()
        gp4.delete()
        gp5.delete()
        gp6.delete()
        gp7.delete()
        g.delete()
        r.delete()

    # CentreCount.__str__()
    def test_centrecount_str(self):
        sc = CentreCount.objects.first()
        # TODO Validate result
        str(sc)
