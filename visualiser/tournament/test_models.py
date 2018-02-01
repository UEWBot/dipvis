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
from django.utils import timezone
from django.db.models import Sum

from tournament.diplomacy import GreatPower, SupplyCentre, GameSet
from tournament.players import Player
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, Round, Game, DrawProposal, GameImage
from tournament.models import SupplyCentreOwnership, CentreCount
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import SECRET, COUNTS, SPRING, ADJUSTMENTS, UNRANKED
from tournament.models import find_game_scoring_system
from tournament.models import find_round_scoring_system
from tournament.models import find_tournament_scoring_system
from tournament.models import validate_game_name, validate_sc_count, validate_vote_count
from tournament.models import SCOwnershipsNotFound, InvalidScoringSystem, InvalidYear

from datetime import timedelta

HOURS_8 = timedelta(hours=8)
HOURS_9 = timedelta(hours=9)
HOURS_10 = timedelta(hours=10)
HOURS_16 = timedelta(hours=16)
HOURS_24 = timedelta(hours=24)

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
                                       draw_secrecy=SECRET)
        t2 = Tournament.objects.create(name='t2',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=SECRET)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=COUNTS)

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
        Game.objects.create(name='g13',
                            started_at=r12.start,
                            the_round=r12,
                            is_finished=True,
                            the_set=cls.set1)
        Game.objects.create(name='g14',
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
        # And the corresponding RoundPlayers
        RoundPlayer.objects.create(player=cls.p1, the_round=r11)
        RoundPlayer.objects.create(player=cls.p2, the_round=r11)
        RoundPlayer.objects.create(player=cls.p3, the_round=r11)
        RoundPlayer.objects.create(player=cls.p4, the_round=r11)
        RoundPlayer.objects.create(player=cls.p5, the_round=r11)
        RoundPlayer.objects.create(player=cls.p6, the_round=r11)
        RoundPlayer.objects.create(player=cls.p7, the_round=r11)
        RoundPlayer.objects.create(player=cls.p8, the_round=r11)
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
        RoundPlayer.objects.create(player=cls.p5, the_round=r31, score=100.0)
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

    # Tournament.scores()
    def test_tournament_scores_invalid(self):
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=timezone.now(),
                                                      end_date=timezone.now(),
                                                      tournament_scoring_system='Invalid System',
                                                      round_scoring_system=R_SCORING_SYSTEMS[0].name)
        self.assertRaises(InvalidScoringSystem, t.scores)

    def test_tournament_scores_finished(self):
        t = Tournament.objects.get(name='t3')
        # TODO Validate results
        t.scores()

    def test_tournament_scores_unfinished(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        t.scores()

    def test_tournament_scores_before_start(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        # Ensure that all TournamentPlayers are included. although there are no RoundPlayers
        t.scores()

    def test_tournament_scores_recalculate(self):
        t = Tournament.objects.get(name='t3')
        # TODO Validate results
        t.scores(True)

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
        p_and_s = t.positions_and_scores()
        self.assertEqual(p_and_s[self.p5][0], UNRANKED)

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
        # All earlier rounds should be finished
        for i in range(1, r.number()):
            # TODO coverage shows that this line is never hit
            self.assertTrue(t.round_numbered(i).is_finished(), 'round %d' % i)
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

    # TODO TournamentPlayer.save()

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

    # Game.create_or_update_sc_counts_from_ownerships
    def test_create_sc_count_invalid(self):
        # Arbitrary game
        g = Game.objects.get(pk=1)
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
        g = Game.objects.get(pk=1)
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
        g = t.round_numbered(2).game_set.get(name='g13')
        self.assertEqual(len(g.players()), 7)
        for gp in g.players().values():
            self.assertEqual(len(gp), 0)

    # Game.news()
    def test_game_news(self):
        g = Game.objects.get(pk=1)
        # TODO Validate results
        g.news()

    def test_game_news_with_name(self):
        g = Game.objects.get(pk=1)
        # TODO Validate results
        g.news(include_game_name=True)

    # Game.background()
    def test_game_background(self):
        g = Game.objects.get(pk=1)
        # TODO Validate results
        g.background()

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
        g1 = Game.objects.get(pk=1)
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(4)
        g2 = Game(name='g13',
                  started_at=g1.started_at + HOURS_8,
                  the_round=r,
                  is_finished=False,
                  the_set=g1.the_set)
        self.assertRaises(ValidationError, g2.clean)

    # TODO Game.save()

    # DrawProposal.draw_size()
    def test_draw_proposal_draw_size_one(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria)
        self.assertEqual(dp.draw_size(), 1)

    def test_draw_proposal_draw_size_all(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(dp.draw_size(), 7)

    # DrawProposal.powers()
    def test_draw_proposal_powers_one(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria)
        self.assertEqual(len(dp.powers()), 1)

    def test_draw_proposal_powers_all(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(len(dp.powers()), 7)

    # DrawProposal.power_is_part()
    def test_draw_proposal_power_is_part_one(self):
        g = Game.objects.get(pk=1)
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
        g = Game.objects.get(pk=1)
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
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.austria)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_clean_with_gap(self):
        g = Game.objects.get(pk=1)
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

    # RoundPlayer.clean()
    def test_roundplayer_clean(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(1)
        p = Player.objects.get(pk=1)
        rp = RoundPlayer(player=p, the_round=r)
        self.assertRaises(ValidationError, rp.clean)

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

    # GamePlayer.clean()
    def test_gameplayer_clean_player_not_in_tournament(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        gp = GamePlayer(player=Player.objects.get(pk=1),
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
        g = t.round_numbered(2).game_set.get(name='g13')
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
        g = t.round_numbered(2).game_set.get(name='g13')
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
        g = t.round_numbered(2).game_set.get(name='g13')
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
        g = t.round_numbered(2).game_set.get(name='g13')
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
        g = t.round_numbered(2).game_set.get(name='g13')
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
        gi2 = GameImage(game=g, year=1902, season=SPRING, phase=ADJUSTMENTS, image=gi1.image)
        self.assertRaises(ValidationError, gi2.clean)

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
