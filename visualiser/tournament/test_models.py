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

from datetime import date, datetime, time, timedelta, timezone
from unittest import skip

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.db.utils import IntegrityError
from django.test import TestCase, tag, override_settings

from tournament import backstabbr, webdip
from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.models.supply_centre import SupplyCentre
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, Round, Game, DrawProposal, GameImage
from tournament.models import SupplyCentreOwnership, CentreCount, Preference
from tournament.models import Award, SeederBias, Series, DBNCoverage, Team
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
from tournament.models import TScoringSumRounds, TScoringSumGames
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import NO_SCORING_SYSTEM_STR
from tournament.models import BestCountryCriteria, DrawSecrecy, Formats, Phases
from tournament.models import PowerAssignMethods, Seasons
from tournament.models import find_game_scoring_system
from tournament.models import find_round_scoring_system
from tournament.models import find_tournament_scoring_system
from tournament.models import scoring_systems_are_compatible
from tournament.models import validate_game_name, validate_vote_count
from tournament.models import validate_game_scoring_system
from tournament.models import validate_round_scoring_system
from tournament.models import validate_tournament_scoring_system
from tournament.models import SCOwnershipsNotFound, InvalidScoringSystem, InvalidYear
from tournament.models import InvalidPreferenceList, InvalidPowerAssignmentMethod
from tournament.models import PowerAlreadyAssigned
from tournament.players import Player, MASK_ALL_BG

HOURS_8 = timedelta(hours=8)
HOURS_9 = timedelta(hours=9)
HOURS_10 = timedelta(hours=10)
HOURS_16 = timedelta(hours=16)
HOURS_24 = timedelta(hours=24)
HOURS_48 = timedelta(hours=48)
HOURS_72 = timedelta(hours=72)

s1 = "Solo or bust"
s2 = "Sum of Squares"


def _find_t_scoring_system(cls, number):
    """
    Find a matching Tournament scoring system

    cls is the class
    number is the number of Games/Rounds that get counted
    """
    for t in T_SCORING_SYSTEMS:
        if isinstance(t, cls):
            if (cls == TScoringSumRounds) and (t.scored_rounds == number):
                return t
            elif (cls == TScoringSumGames) and (t.scored_games == number):
                return t
    raise AssertionError(f'No matching tournament scoring system found for {cls} {number}')


def _find_complex_t_scoring_system(games, fraction, count=None):
    """
    Find a matching Tournament scoring system

    games is the number of Games that get included at 100%
    fraction is the proportion of other Games that gets included
    count is the max number of other games that get included
    """
    for t in T_SCORING_SYSTEMS:
        if isinstance(t, TScoringSumGames) and (t.scored_games == games) and (t.residual_multiplier == fraction) and (t.residual_count == count):
            return t
    raise AssertionError(f'No matching tournament scoring system found for {games} {fraction} {count}')


class RoundScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

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
        # These two are deliberately not in any tournaments
        cls.p9 = Player.objects.create(first_name='Queenie', last_name='Radiation')
        cls.p10 = Player.objects.create(first_name='Sebastian', last_name='Twinkie')
        # The remainder are not used in this method but are available for use in tests
        cls.p11 = Player.objects.create(first_name='Ursula', last_name='Vampire')
        cls.p12 = Player.objects.create(first_name='Wilfred', last_name='Xylophone')
        cls.p13 = Player.objects.create(first_name='Yannis', last_name='Zygote')

    # RScoringBest.scores() without sitting-out bonus
    def test_r_scoring_best(self):
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        today = date.today()
        t = Tournament.objects.create(name='Round Scoring Test',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        # Check that we got the right scoring system
        self.assertIn("Best", t.round_scoring_system)
        # One Round
        r = Round.objects.create(tournament=t,
                                 scoring_system=s,
                                 dias=False,
                                 start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        # Two finished Games
        g1 = Game.objects.create(name='g1',
                                 started_at=r.start,
                                 the_round=r,
                                 is_finished=True,
                                 the_set=self.set1)
        g2 = Game.objects.create(name='g2',
                                 started_at=r.start,
                                 the_round=r,
                                 is_finished=True,
                                 the_set=self.set1)
        # 12 players, so we have two playing two games
        TournamentPlayer.objects.create(player=self.p1, tournament=t)
        TournamentPlayer.objects.create(player=self.p2, tournament=t)
        TournamentPlayer.objects.create(player=self.p3, tournament=t)
        TournamentPlayer.objects.create(player=self.p4, tournament=t)
        TournamentPlayer.objects.create(player=self.p5, tournament=t)
        TournamentPlayer.objects.create(player=self.p6, tournament=t)
        TournamentPlayer.objects.create(player=self.p7, tournament=t)
        TournamentPlayer.objects.create(player=self.p8, tournament=t)
        TournamentPlayer.objects.create(player=self.p9, tournament=t)
        TournamentPlayer.objects.create(player=self.p10, tournament=t)
        TournamentPlayer.objects.create(player=self.p11, tournament=t)
        TournamentPlayer.objects.create(player=self.p12, tournament=t)
        RoundPlayer.objects.create(player=self.p1, the_round=r)
        RoundPlayer.objects.create(player=self.p2, the_round=r)
        RoundPlayer.objects.create(player=self.p3, the_round=r)
        RoundPlayer.objects.create(player=self.p4, the_round=r)
        RoundPlayer.objects.create(player=self.p5, the_round=r)
        RoundPlayer.objects.create(player=self.p6, the_round=r)
        RoundPlayer.objects.create(player=self.p7, the_round=r)
        RoundPlayer.objects.create(player=self.p8, the_round=r)
        RoundPlayer.objects.create(player=self.p9, the_round=r)
        RoundPlayer.objects.create(player=self.p10, the_round=r)
        RoundPlayer.objects.create(player=self.p11, the_round=r)
        RoundPlayer.objects.create(player=self.p12, the_round=r)
        GamePlayer.objects.create(player=self.p1, game=g1, power=self.austria, score=0)
        GamePlayer.objects.create(player=self.p2, game=g1, power=self.england, score=1)
        GamePlayer.objects.create(player=self.p3, game=g1, power=self.france, score=2)
        GamePlayer.objects.create(player=self.p4, game=g1, power=self.germany, score=3)
        GamePlayer.objects.create(player=self.p5, game=g1, power=self.italy, score=4)
        GamePlayer.objects.create(player=self.p6, game=g1, power=self.russia, score=5)
        GamePlayer.objects.create(player=self.p7, game=g1, power=self.turkey, score=6)
        GamePlayer.objects.create(player=self.p12, game=g2, power=self.austria, score=0)
        GamePlayer.objects.create(player=self.p11, game=g2, power=self.england, score=1)
        GamePlayer.objects.create(player=self.p10, game=g2, power=self.france, score=2)
        GamePlayer.objects.create(player=self.p9, game=g2, power=self.germany, score=3)
        GamePlayer.objects.create(player=self.p8, game=g2, power=self.italy, score=4)
        GamePlayer.objects.create(player=self.p7, game=g2, power=self.russia, score=5)
        GamePlayer.objects.create(player=self.p6, game=g2, power=self.turkey, score=6)

        # Now we can test the RoundScoringSystem
        expected_results = {self.p1: 0,
                            self.p2: 1,
                            self.p3: 2,
                            self.p4: 3,
                            self.p5: 4,
                            self.p6: 6, # Best of 5 and 6
                            self.p7: 6, # Best of 5 and 6
                            self.p8: 4,
                            self.p9: 3,
                            self.p10: 2,
                            self.p11: 1,
                            self.p12: 0,
                           }
        r.update_scores()
        scores = r.scores()
        for p, s in expected_results.items():
            with self.subTest(player=p):
                self.assertEqual(scores[p], s)
        # Check the score_dropped attribute of each GamePlayer
        for gp in g1.gameplayer_set.all():
            if gp.score == 5:
                self.assertTrue(gp.score_dropped)
            else:
                self.assertFalse(gp.score_dropped)
        for gp in g2.gameplayer_set.all():
            if gp.score == 5:
                self.assertTrue(gp.score_dropped)
            else:
                self.assertFalse(gp.score_dropped)
        # Clean up
        t.delete()

    # RScoringBest.scores() with sitting bonus
    def test_r_scoring_best_with_bonus(self):
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        today = date.today()
        t = Tournament.objects.create(name='Round Scoring Test',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      non_player_round_score=4005,
                                      non_player_round_score_once=False,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        # Check that we got the right scoring system
        self.assertIn("Best", t.round_scoring_system)
        # One Round
        r = Round.objects.create(tournament=t,
                                 scoring_system=s,
                                 dias=False,
                                 start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        # One finished Game
        g = Game.objects.create(name='g1',
                                started_at=r.start,
                                the_round=r,
                                is_finished=True,
                                the_set=self.set1)
        # 8 players, so we have one sitting out
        TournamentPlayer.objects.create(player=self.p1, tournament=t)
        TournamentPlayer.objects.create(player=self.p2, tournament=t)
        TournamentPlayer.objects.create(player=self.p3, tournament=t)
        TournamentPlayer.objects.create(player=self.p4, tournament=t)
        TournamentPlayer.objects.create(player=self.p5, tournament=t)
        TournamentPlayer.objects.create(player=self.p6, tournament=t)
        TournamentPlayer.objects.create(player=self.p7, tournament=t)
        TournamentPlayer.objects.create(player=self.p8, tournament=t)
        RoundPlayer.objects.create(player=self.p1, the_round=r)
        RoundPlayer.objects.create(player=self.p2, the_round=r)
        RoundPlayer.objects.create(player=self.p3, the_round=r)
        RoundPlayer.objects.create(player=self.p4, the_round=r)
        RoundPlayer.objects.create(player=self.p5, the_round=r)
        RoundPlayer.objects.create(player=self.p6, the_round=r, game_count=0)
        RoundPlayer.objects.create(player=self.p7, the_round=r)
        RoundPlayer.objects.create(player=self.p8, the_round=r)
        GamePlayer.objects.create(player=self.p1, game=g, power=self.austria, score=0)
        GamePlayer.objects.create(player=self.p2, game=g, power=self.england, score=1)
        GamePlayer.objects.create(player=self.p3, game=g, power=self.france, score=2)
        GamePlayer.objects.create(player=self.p4, game=g, power=self.germany, score=3)
        GamePlayer.objects.create(player=self.p5, game=g, power=self.italy, score=4)
        GamePlayer.objects.create(player=self.p7, game=g, power=self.russia, score=5)
        GamePlayer.objects.create(player=self.p8, game=g, power=self.turkey, score=6)

        # Now we can test the RoundScoringSystem
        expected_results = {self.p1: 0,
                            self.p2: 1,
                            self.p3: 2,
                            self.p4: 3,
                            self.p5: 4,
                            self.p6: 4005,
                            self.p7: 5,
                            self.p8: 6,
                           }
        r.update_scores()
        scores = r.scores()
        for p, s in expected_results.items():
            with self.subTest(player=p):
                self.assertEqual(scores[p], s)
        # Clean up
        t.delete()

    # RScoringBest.scores() with one-off sitting bonus
    def test_r_scoring_best_with_one_bonus(self):
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        today = date.today()
        t = Tournament.objects.create(name='Round Scoring Test',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      non_player_round_score=4005,
                                      non_player_round_score_once=True,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        # Check that we got the right scoring system
        self.assertIn("Best", t.round_scoring_system)
        # Two Rounds
        r1 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r2 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_8)
        # Two finished Games
        g1 = Game.objects.create(name='g1',
                                 started_at=r1.start,
                                 the_round=r1,
                                 is_finished=True,
                                 the_set=self.set1)
        g2 = Game.objects.create(name='g2',
                                 started_at=r2.start,
                                 the_round=r2,
                                 is_finished=True,
                                 the_set=self.set1)
        # 9 players, so we have two sitting out each round
        TournamentPlayer.objects.create(player=self.p1, tournament=t)
        TournamentPlayer.objects.create(player=self.p2, tournament=t)
        TournamentPlayer.objects.create(player=self.p3, tournament=t)
        TournamentPlayer.objects.create(player=self.p4, tournament=t)
        TournamentPlayer.objects.create(player=self.p5, tournament=t)
        TournamentPlayer.objects.create(player=self.p6, tournament=t)
        TournamentPlayer.objects.create(player=self.p7, tournament=t)
        TournamentPlayer.objects.create(player=self.p8, tournament=t)
        TournamentPlayer.objects.create(player=self.p9, tournament=t)
        RoundPlayer.objects.create(player=self.p1, the_round=r1)
        RoundPlayer.objects.create(player=self.p2, the_round=r1)
        RoundPlayer.objects.create(player=self.p3, the_round=r1)
        RoundPlayer.objects.create(player=self.p4, the_round=r1, game_count=0)
        RoundPlayer.objects.create(player=self.p5, the_round=r1)
        RoundPlayer.objects.create(player=self.p6, the_round=r1, game_count=0)
        RoundPlayer.objects.create(player=self.p7, the_round=r1)
        RoundPlayer.objects.create(player=self.p8, the_round=r1)
        RoundPlayer.objects.create(player=self.p9, the_round=r1)
        RoundPlayer.objects.create(player=self.p1, the_round=r2)
        RoundPlayer.objects.create(player=self.p2, the_round=r2)
        RoundPlayer.objects.create(player=self.p3, the_round=r2, game_count=0)
        RoundPlayer.objects.create(player=self.p4, the_round=r2)
        RoundPlayer.objects.create(player=self.p5, the_round=r2)
        RoundPlayer.objects.create(player=self.p6, the_round=r2, game_count=0)
        RoundPlayer.objects.create(player=self.p7, the_round=r2)
        RoundPlayer.objects.create(player=self.p8, the_round=r2)
        RoundPlayer.objects.create(player=self.p9, the_round=r2)
        GamePlayer.objects.create(player=self.p1, game=g1, power=self.austria, score=0)
        GamePlayer.objects.create(player=self.p2, game=g1, power=self.england, score=1)
        GamePlayer.objects.create(player=self.p3, game=g1, power=self.france, score=2)
        GamePlayer.objects.create(player=self.p5, game=g1, power=self.germany, score=3)
        GamePlayer.objects.create(player=self.p7, game=g1, power=self.italy, score=4)
        GamePlayer.objects.create(player=self.p8, game=g1, power=self.russia, score=5)
        GamePlayer.objects.create(player=self.p9, game=g1, power=self.turkey, score=6)
        GamePlayer.objects.create(player=self.p1, game=g2, power=self.austria, score=10)
        GamePlayer.objects.create(player=self.p2, game=g2, power=self.england, score=11)
        GamePlayer.objects.create(player=self.p4, game=g2, power=self.france, score=12)
        GamePlayer.objects.create(player=self.p5, game=g2, power=self.germany, score=13)
        GamePlayer.objects.create(player=self.p7, game=g2, power=self.italy, score=14)
        GamePlayer.objects.create(player=self.p8, game=g2, power=self.russia, score=15)
        GamePlayer.objects.create(player=self.p9, game=g2, power=self.turkey, score=16)

        # Now we can test the RoundScoringSystem
        expected_results = {self.p1: 10,
                            self.p2: 11,
                            self.p3: 4005, # First time sitting out
                            self.p4: 12,
                            self.p5: 13,
                            self.p6: 0, # Already sat out round 1
                            self.p7: 14,
                            self.p8: 15,
                            self.p9: 16,
                           }
        r2.update_scores()
        scores = r2.scores()
        for p, s in expected_results.items():
            with self.subTest(player=p):
                self.assertEqual(scores[p], s)
        # Check the score_dropped attribute of each GamePlayer
        for gp in g1.gameplayer_set.all():
            self.assertFalse(gp.score_dropped)
        for gp in g2.gameplayer_set.all():
            self.assertFalse(gp.score_dropped)
        # Clean up
        t.delete()

    # RScoringAll.scores()
    def test_r_scoring_all(self):
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        today = date.today()
        t = Tournament.objects.create(name='Round Scoring Test',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=R_SCORING_SYSTEMS[1].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        # Check that we got the right scoring system
        self.assertIn("all", t.round_scoring_system)
        # One Round
        r = Round.objects.create(tournament=t,
                                 scoring_system=s,
                                 dias=False,
                                 start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        # Two finished Games
        g1 = Game.objects.create(name='g1',
                                 started_at=r.start,
                                 the_round=r,
                                 is_finished=True,
                                 the_set=self.set1)
        g2 = Game.objects.create(name='g2',
                                 started_at=r.start,
                                 the_round=r,
                                 is_finished=True,
                                 the_set=self.set1)
        # 13 players, two playing two games and 1 sitting out
        TournamentPlayer.objects.create(player=self.p1, tournament=t)
        TournamentPlayer.objects.create(player=self.p2, tournament=t)
        TournamentPlayer.objects.create(player=self.p3, tournament=t)
        TournamentPlayer.objects.create(player=self.p4, tournament=t)
        TournamentPlayer.objects.create(player=self.p5, tournament=t)
        TournamentPlayer.objects.create(player=self.p6, tournament=t)
        TournamentPlayer.objects.create(player=self.p7, tournament=t)
        TournamentPlayer.objects.create(player=self.p8, tournament=t)
        TournamentPlayer.objects.create(player=self.p9, tournament=t)
        TournamentPlayer.objects.create(player=self.p10, tournament=t)
        TournamentPlayer.objects.create(player=self.p11, tournament=t)
        TournamentPlayer.objects.create(player=self.p12, tournament=t)
        TournamentPlayer.objects.create(player=self.p13, tournament=t)
        RoundPlayer.objects.create(player=self.p1, the_round=r)
        RoundPlayer.objects.create(player=self.p2, the_round=r)
        RoundPlayer.objects.create(player=self.p3, the_round=r)
        RoundPlayer.objects.create(player=self.p4, the_round=r)
        RoundPlayer.objects.create(player=self.p5, the_round=r)
        RoundPlayer.objects.create(player=self.p6, the_round=r)
        RoundPlayer.objects.create(player=self.p7, the_round=r)
        RoundPlayer.objects.create(player=self.p8, the_round=r)
        RoundPlayer.objects.create(player=self.p9, the_round=r)
        RoundPlayer.objects.create(player=self.p10, the_round=r)
        RoundPlayer.objects.create(player=self.p11, the_round=r)
        RoundPlayer.objects.create(player=self.p12, the_round=r)
        RoundPlayer.objects.create(player=self.p13, the_round=r)
        GamePlayer.objects.create(player=self.p1, game=g1, power=self.austria, score=0)
        GamePlayer.objects.create(player=self.p2, game=g1, power=self.england, score=1)
        GamePlayer.objects.create(player=self.p3, game=g1, power=self.france, score=2)
        GamePlayer.objects.create(player=self.p4, game=g1, power=self.germany, score=3)
        GamePlayer.objects.create(player=self.p5, game=g1, power=self.italy, score=4)
        GamePlayer.objects.create(player=self.p6, game=g1, power=self.russia, score=5)
        GamePlayer.objects.create(player=self.p7, game=g1, power=self.turkey, score=6)
        GamePlayer.objects.create(player=self.p12, game=g2, power=self.austria, score=0)
        GamePlayer.objects.create(player=self.p11, game=g2, power=self.england, score=1)
        GamePlayer.objects.create(player=self.p10, game=g2, power=self.france, score=2)
        GamePlayer.objects.create(player=self.p9, game=g2, power=self.germany, score=3)
        GamePlayer.objects.create(player=self.p8, game=g2, power=self.italy, score=4)
        GamePlayer.objects.create(player=self.p7, game=g2, power=self.russia, score=5)
        GamePlayer.objects.create(player=self.p6, game=g2, power=self.turkey, score=6)

        # Now we can test the RoundScoringSystem
        expected_results = {self.p1: 0,
                            self.p2: 1,
                            self.p3: 2,
                            self.p4: 3,
                            self.p5: 4,
                            self.p6: 11, # Sum of 5 and 6
                            self.p7: 11, # Sum of 5 and 6
                            self.p8: 4,
                            self.p9: 3,
                            self.p10: 2,
                            self.p11: 1,
                            self.p12: 0,
                            self.p13: 0,
                           }
        r.update_scores()
        scores = r.scores()
        for p, s in expected_results.items():
            with self.subTest(player=p):
                self.assertEqual(scores[p], s)
        # Check the score_dropped attribute of each GamePlayer
        for gp in g1.gameplayer_set.all():
            self.assertFalse(gp.score_dropped)
        for gp in g2.gameplayer_set.all():
            self.assertFalse(gp.score_dropped)
        # Clean up
        t.delete()

    # RScoringBest.__str__()
    def test_rscoringbest0_str(self):
        # TODO This depends on the ordering
        r = R_SCORING_SYSTEMS[0]
        r_str = str(r)
        self.assertIn('est game counts', r_str)

    # RScoringSum.__str__()
    def test_rscoringsum_str(self):
        # TODO This depends on the ordering
        r = R_SCORING_SYSTEMS[1]
        r_str = str(r)
        self.assertIn('ll game scores', r_str)


class TournamentScoringWDC2025Tests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.tss = find_tournament_scoring_system('WDC 2025')

        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # Create some players
        # Avoid hitting the WDD by not providing a WDD id
        cls.p1 = Player.objects.create(first_name='Abbey', last_name='Antelope')
        cls.p2 = Player.objects.create(first_name='Beth', last_name='Bottom')
        cls.p3 = Player.objects.create(first_name='Charles', last_name='Chicanery')
        cls.p4 = Player.objects.create(first_name='Daisy', last_name='Duke')
        cls.p5 = Player.objects.create(first_name='Ethel', last_name='Elephant')
        cls.p6 = Player.objects.create(first_name='Fred', last_name='Flintstone')
        cls.p7 = Player.objects.create(first_name='George', last_name='Gigantic')
        cls.p8 = Player.objects.create(first_name='Helen', last_name='Horrendous')
        cls.p9 = Player.objects.create(first_name='Iris', last_name='Idiotic')
        cls.p10 = Player.objects.create(first_name='Jake', last_name='Jello')
        cls.p11 = Player.objects.create(first_name='Kevin', last_name='Koala')
        cls.p12 = Player.objects.create(first_name='Lydia', last_name='Lamppost')
        cls.p13 = Player.objects.create(first_name='Michelle', last_name='Mybelle')
        cls.p14 = Player.objects.create(first_name='Nicola', last_name='Nuts')
        cls.p15 = Player.objects.create(first_name='Owen', last_name='Ocelot')
        cls.p16 = Player.objects.create(first_name='Pete', last_name='Peculiar')
        cls.p17 = Player.objects.create(first_name='Queenie', last_name='Qwerty')
        cls.p18 = Player.objects.create(first_name='Robert', last_name='Rules')
        cls.p19 = Player.objects.create(first_name='Sebastian', last_name='Saxophone')
        cls.p20 = Player.objects.create(first_name='Theresa', last_name='Tumultuous')
        cls.p21 = Player.objects.create(first_name='Ursula', last_name='Umbrella')
        cls.p22 = Player.objects.create(first_name='Victoria', last_name='Virgin')
        cls.p23 = Player.objects.create(first_name='Wilfred', last_name='Wildebeest')
        cls.p24 = Player.objects.create(first_name='Xavier', last_name='Xray')
        cls.p25 = Player.objects.create(first_name='Yannis', last_name='Yellow')
        cls.p26 = Player.objects.create(first_name='Zara', last_name='Zebra')
        players = [cls.p1, cls.p2, cls.p3, cls.p4, cls.p5, cls.p6, cls.p7, cls.p8, cls.p9,
                   cls.p10, cls.p11, cls.p12, cls.p13, cls.p14, cls.p15, cls.p16, cls.p17,
                   cls.p18, cls.p19, cls.p20, cls.p21, cls.p22, cls.p23, cls.p24]

        # 4-round tournament with 4 games per round
        s = G_SCORING_SYSTEMS[0].name
        today = date.today()
        cls.t = Tournament.objects.create(name='WDC 2025 Tournament Scoring Test',
                                          start_date=today,
                                          end_date=today + HOURS_24,
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=cls.tss.name,
                                          draw_secrecy=DrawSecrecy.SECRET)
        cls.r1 = Round.objects.create(tournament=cls.t,
                                      scoring_system=s,
                                      dias=False,
                                      start=datetime.combine(cls.t.start_date, time(hour=8, tzinfo=timezone.utc)))
        cls.r2 = Round.objects.create(tournament=cls.t,
                                      scoring_system=s,
                                      dias=False,
                                      start=cls.r1.start + HOURS_8)
        cls.r3 = Round.objects.create(tournament=cls.t,
                                      scoring_system=s,
                                      dias=False,
                                      start=cls.r2.start + HOURS_8)
        cls.r4 = Round.objects.create(tournament=cls.t,
                                      scoring_system=s,
                                      dias=False,
                                      start=cls.r3.start + HOURS_8)
        gps = [[(cls.p1, cls.austria, 10.0), # Round 1 Game 1
                (cls.p2, cls.england, 20.0),
                (cls.p3, cls.russia, 30.0),
                (cls.p4, cls.germany, 40.0),
                (cls.p5, cls.italy, 50.0),
                (cls.p6, cls.france, 60.0),
                (cls.p7, cls.turkey, 70.0)],
               [(cls.p8, cls.austria, 10.0), # Round 1 Game 2
                (cls.p9, cls.england, 20.0),
                (cls.p10, cls.france, 30.0),
                (cls.p11, cls.germany, 40.0),
                (cls.p12, cls.italy, 50.0),
                (cls.p13, cls.russia, 60.0),
                (cls.p14, cls.turkey, 70.0)],
               [(cls.p15, cls.austria, 10.0), # Round 1 Game 3
                (cls.p16, cls.england, 20.0),
                (cls.p17, cls.france, 30.0),
                (cls.p18, cls.germany, 40.0),
                (cls.p19, cls.italy, 50.0),
                (cls.p20, cls.russia, 60.0),
                (cls.p21, cls.turkey, 70.0)],
               [(cls.p1, cls.austria, 10.0), # Round 2 Game 1
                (cls.p2, cls.england, 20.0),
                (cls.p3, cls.france, 30.0),
                (cls.p4, cls.germany, 40.0),
                (cls.p5, cls.italy, 50.0),
                (cls.p6, cls.russia, 60.0),
                (cls.p7, cls.turkey, 70.0)],
               [(cls.p8, cls.austria, 10.0), # Round 2 Game 2
                (cls.p9, cls.england, 20.0),
                (cls.p10, cls.france, 30.0),
                (cls.p11, cls.germany, 40.0),
                (cls.p12, cls.italy, 50.0),
                (cls.p13, cls.russia, 60.0),
                (cls.p14, cls.turkey, 70.0)],
               [(cls.p15, cls.austria, 10.0), # Round 2 Game 3
                (cls.p16, cls.russia, 20.0),
                (cls.p17, cls.france, 30.0),
                (cls.p18, cls.germany, 40.0),
                (cls.p19, cls.italy, 50.0),
                (cls.p20, cls.england, 60.0),
                (cls.p21, cls.turkey, 70.0)],
               [(cls.p1, cls.austria, 10.0), # Round 3 Game 1
                (cls.p2, cls.england, 20.0),
                (cls.p3, cls.france, 30.0),
                (cls.p4, cls.germany, 40.0),
                (cls.p5, cls.italy, 50.0),
                (cls.p6, cls.russia, 60.0),
                (cls.p7, cls.turkey, 70.0)],
               [(cls.p9, cls.austria, 10.0), # Round 3 Game 2
                (cls.p10, cls.england, 20.0),
                (cls.p11, cls.france, 30.0),
                (cls.p12, cls.germany, 40.0),
                (cls.p13, cls.italy, 50.0),
                (cls.p14, cls.russia, 60.0),
                (cls.p15, cls.turkey, 70.0)],
               [(cls.p17, cls.austria, 10.0), # Round 3 Game 3
                (cls.p18, cls.england, 20.0),
                (cls.p19, cls.france, 30.0),
                (cls.p20, cls.germany, 40.0),
                (cls.p21, cls.italy, 50.0),
                (cls.p22, cls.russia, 60.0),
                (cls.p23, cls.turkey, 70.0)],
               [(cls.p24, cls.austria, 10.0), # Round 4 Game 1
                (cls.p23, cls.england, 20.0),
                (cls.p22, cls.france, 30.0),
                (cls.p21, cls.germany, 40.0),
                (cls.p20, cls.italy, 50.0),
                (cls.p19, cls.russia, 60.0),
                (cls.p18, cls.turkey, 70.0)],
               [(cls.p17, cls.austria, 10.0), # Round 4 Game 2
                (cls.p16, cls.england, 20.0),
                (cls.p15, cls.france, 30.0),
                (cls.p14, cls.germany, 40.0),
                (cls.p13, cls.italy, 50.0),
                (cls.p12, cls.russia, 60.0),
                (cls.p11, cls.turkey, 70.0)],
               [(cls.p10, cls.austria, 10.0), # Round 4 Game 3
                (cls.p9, cls.england, 20.0),
                (cls.p8, cls.france, 30.0),
                (cls.p7, cls.germany, 40.0),
                (cls.p6, cls.italy, 50.0),
                (cls.p5, cls.russia, 60.0),
                (cls.p4, cls.turkey, 70.0)],
              ]
        # Create 3 games per round, and store players, powers, and scores
        games = {}
        for r in [cls.r1, cls.r2, cls.r3, cls.r4]:
            for n in range(3):
                g = Game.objects.create(name=f'g{r.number()}{n}',
                                        started_at=r.start,
                                        the_round=r,
                                        is_finished=True,
                                        the_set=cls.set1)
                games[g] = gps.pop(0)
        # Create TournamentPlayers
        for p in players:
            TournamentPlayer.objects.create(tournament=cls.t, player=p)
        # Create RoundPlayers
        for r in [cls.r1, cls.r2, cls.r3, cls.r4]:
            for p in players:
                RoundPlayer.objects.create(player=p, the_round=r)
        # Create GamePlayers
        for g, players in games.items():
            for player, power, score in players:
                gp = GamePlayer.objects.create(player=player, game=g, power=power, score=score)

    # TScoringWDC2025.__str__()
    def test_str(self):
        res = str(self.tss)
        self.assertEqual(res, 'WDC 2025')

    # TScoringWDC2025.scores() without ties
    def test_scores_no_ties(self):
        # Propagate scores from GP through RP to TP
        for r in [self.r1, self.r2, self.r3, self.r4]:
            r.update_scores()
        rps = RoundPlayer.objects.filter(the_round__tournament=self.t)
        scores = self.tss.scores(rps)
        # validate results
        self.assertEqual(len(scores), 24)
        for p, score in scores.items():
            with self.subTest(player=str(p)):
                gps = p.gameplayer_set.filter(game__the_round__tournament=self.t).order_by('-score')
                # Score should be either:
                # - best two of the first three rounds plus the 4th round
                # - best two of the first three rounds plus 1.5x the 4th round
                gp13 = gps.exclude(game__the_round=self.r4)
                try:
                    gp4_score = gps.get(game__the_round=self.r4).score
                except GamePlayer.DoesNotExist:
                    gp4_score = 0.0
                if len(gp13) == 3:
                    res = sum(gp.score for gp in list(gp13)[:2])
                else:
                    res = sum(gp.score for gp in gp13.all())
                self.assertTrue((score - res == gp4_score) or (score - res == 1.5 * gp4_score))

    # TScoringWDC2025.scores() tiebreakers
    def test_scores_with_ties(self):
        # Set GP scores to have some ties
        # TODO This still needs work. The idea is to have 8 players tied,
        #      that split into two equal groups on the each tiebreaker
        scores = {self.p2: {self.r1: 60, self.r2: 0, self.r3: 0},
                  self.p3: {self.r1: 30, self.r2: 30, self.r3: 10},
                  self.p8: {self.r1: 60, self.r2: 0},
                  self.p9: {self.r1: 30, self.r2: 30, self.r3: 5},
                  self.p10: {self.r1: 60, self.r2: 0, self.r3: 0},
                  self.p16: {self.r1: 30, self.r2: 30},
                  self.p17: {self.r1: 30, self.r2: 30, self.r3: 20},
                  self.p22: {self.r3: 60}}
        tied = {self.p2: 60.0,   # wins first tiebreak (single game score)
                self.p3: 60.0,   # wins second tiebreak (total SCs in scored games)
                self.p8: 105.0,  # wins first tiebreak (single game score)
                self.p9: 80.0,   # loses all three tiebreaks
                self.p10: 75.0,  # wins first tiebreak (single game score)
                self.p16: 90.0,  # wins second tiebreak (total SCs in scored games)
                self.p17: 75.0,  # wins third tiebreak (score in dropped round)
                self.p22: 105.0, # wins first tiebreak (single game score)
               }
        old_scores = {}
        for p, res in scores.items():
            old_scores[p] = {}
            for r, points in res.items():
                gp = p.gameplayer_set.get(game__the_round=r)
                old_scores[p][r] = gp.score
                gp.score = points
                gp.save(update_fields=['score'])
        # Propagate scores from GP through RP to TP
        for r in [self.r1, self.r2, self.r3, self.r4]:
            r.update_scores()
        rps = RoundPlayer.objects.filter(the_round__tournament=self.t)
        scores = self.tss.scores(rps)
        # validate results
        self.assertEqual(len(scores), 24)
        for p, score in scores.items():
            with self.subTest(player=str(p)):
                gps = p.gameplayer_set.filter(game__the_round__tournament=self.t).order_by('-score')
                # Score should be either:
                # - best two of the first three rounds plus the 4th round
                # - best two of the first three rounds plus 1.5x the 4th round
                gp13 = gps.exclude(game__the_round=self.r4)
                try:
                    gp4_score = gps.get(game__the_round=self.r4).score
                except GamePlayer.DoesNotExist:
                    gp4_score = 0.0
                if len(gp13) == 3:
                    res = sum(gp.score for gp in list(gp13)[:2])
                else:
                    res = sum(gp.score for gp in gp13.all())
                self.assertTrue((score - res == gp4_score) or (score - res == 1.5 * gp4_score))
                # Check that ties were broken correctly
                if p in tied:
                    self.assertEqual(score, tied[p])
        # Cleanup
        for p, res in old_scores.items():
            for r, points in res.items():
                gp = GamePlayer.objects.get(game__the_round=r, player=p)
                gp.score = points
                gp.save(update_fields=['score'])


class TournamentScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

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
        # These two are deliberately not in any tournaments
        cls.p9 = Player.objects.create(first_name='Queenie', last_name='Radiation')
        cls.p10 = Player.objects.create(first_name='Sebastian', last_name='Twinkie')
        # The remainder are not used in this method but are available for use in tests
        cls.p11 = Player.objects.create(first_name='Ursula', last_name='Vampire')
        cls.p12 = Player.objects.create(first_name='Wilfred', last_name='Xylophone')
        cls.p13 = Player.objects.create(first_name='Yannis', last_name='Zygote')

    # TScoringSumRounds.__str__()
    def test_tscoringsumrounds_str(self):
        for t in T_SCORING_SYSTEMS:
            if isinstance(t, TScoringSumRounds):
                t_str = str(t)
                # TODO check the result

    # TScoringSumRounds.scores()
    def test_tscoringsumrounds_scores(self):
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        today = date.today()
        tss = _find_t_scoring_system(TScoringSumRounds, 2)
        t = Tournament.objects.create(name='Tournament Scoring Test',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=tss.name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        # Three Rounds
        r1 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r2 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_8)
        r3 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_24)
        # One finished Game per round
        Game.objects.create(name='g1',
                                 started_at=r1.start,
                                 the_round=r1,
                                 is_finished=True,
                                 the_set=self.set1)
        Game.objects.create(name='g2',
                                 started_at=r2.start,
                                 the_round=r2,
                                 is_finished=True,
                                 the_set=self.set1)
        Game.objects.create(name='g3',
                                 started_at=r3.start,
                                 the_round=r3,
                                 is_finished=True,
                                 the_set=self.set1)

        TournamentPlayer.objects.create(player=self.p1, tournament=t)
        TournamentPlayer.objects.create(player=self.p2, tournament=t)
        TournamentPlayer.objects.create(player=self.p3, tournament=t)
        TournamentPlayer.objects.create(player=self.p4, tournament=t)
        # p5 doesn't play at all
        TournamentPlayer.objects.create(player=self.p5, tournament=t)
        TournamentPlayer.objects.create(player=self.p6, tournament=t)
        TournamentPlayer.objects.create(player=self.p7, tournament=t)
        TournamentPlayer.objects.create(player=self.p8, tournament=t, unranked=True)
        TournamentPlayer.objects.create(player=self.p9, tournament=t)
        TournamentPlayer.objects.create(player=self.p10, tournament=t)
        TournamentPlayer.objects.create(player=self.p11, tournament=t)
        TournamentPlayer.objects.create(player=self.p12, tournament=t)

        # Mix of players playing 1, 2, and all 3 rounds
        # p1 skips round 2, p4 skips round 1, p7 skips round 3
        # p3 and p6 play just round 3, p10 plays just round 2, p11 plays just round 1
        round_scores = {r1: {self.p1: (6, False),
                             self.p2: (7, False),
                             self.p7: (3, False),
                             self.p8: (10, False),
                             self.p9: (1, True),
                             self.p11: (4, False),
                             self.p12: (40, False)},
                        r2: {self.p2: (50, False),
                             self.p4: (70, False),
                             self.p7: (30, False),
                             self.p8: (500, False),
                             self.p9: (20, False),
                             self.p10: (60, False),
                             self.p12: (2, True)},
                        r3: {self.p1: (700, False),
                             self.p3: (400, False),
                             self.p4: (200, False),
                             self.p6: (100, False),
                             self.p8: (5, True),
                             self.p9: (600, False),
                             self.p12: (300, False)}}

        for r in round_scores.keys():
            for p, (s, _) in round_scores[r].items():
                RoundPlayer.objects.create(player=p, the_round=r, score=s)

        t.update_scores()
        t_scores = t.scores_detail()

        expected_scores = {self.p1: 706,
                           self.p2: 57,
                           self.p3: 400,
                           self.p4: 270,
                           self.p5: 0,
                           self.p6: 100,
                           self.p7: 33,
                           self.p8: 510,
                           self.p9: 620,
                           self.p10: 60,
                           self.p11: 4,
                           self.p12: 340}
        for p, score in expected_scores.items():
            with self.subTest(player=p):
                self.assertAlmostEqual(t_scores[p], score)

        for r in round_scores.keys():
            with self.subTest(round_num=r.number()):
                for p, (s, drop) in round_scores[r].items():
                    with self.subTest(player=p):
                        # check score_dropped
                        rp = RoundPlayer.objects.get(player=p, the_round=r)
                        self.assertEqual(rp.score_dropped, drop)

    # TScoringSumGames.__init__()
    def test_tscoringsum_games_init(self):
        self.assertRaises(ValueError,
                          TScoringSumGames,
                          'Test system', 3, 0.0, 1)

    # TScoringSumGames.__str__()
    def test_tscoringsumgames_str(self):
        for t in T_SCORING_SYSTEMS:
            if isinstance(t, TScoringSumGames):
                t_str = str(t)
                # TODO check the result

    # TScoringSumGames.scores()
    def test_tscoringsumgames_scores(self):
        """ TScoringSumGames with no sitting out bonus"""
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        today = date.today()
        tss = _find_t_scoring_system(TScoringSumGames, 4)
        t = Tournament.objects.create(name='Tournament Scoring Test',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=NO_SCORING_SYSTEM_STR,
                                      tournament_scoring_system=tss.name,
                                      draw_secrecy=DrawSecrecy.SECRET)

        # Five Rounds
        r1 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r2 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_8)
        r3 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_9)
        r4 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_10)
        r5 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_16)
        # Two finished Games per round
        g11 = Game.objects.create(name='g11',
                                  started_at=r1.start,
                                  the_round=r1,
                                  is_finished=True,
                                  the_set=self.set1)
        g12 = Game.objects.create(name='g12',
                                  started_at=r1.start,
                                  the_round=r1,
                                  is_finished=True,
                                  the_set=self.set1)
        g21 = Game.objects.create(name='g21',
                                  started_at=r2.start,
                                  the_round=r2,
                                  is_finished=True,
                                  the_set=self.set1)
        g22 = Game.objects.create(name='g22',
                                  started_at=r2.start,
                                  the_round=r2,
                                  is_finished=True,
                                  the_set=self.set1)
        g31 = Game.objects.create(name='g31',
                                  started_at=r3.start,
                                  the_round=r3,
                                  is_finished=True,
                                  the_set=self.set1)
        g32 = Game.objects.create(name='g32',
                                  started_at=r3.start,
                                  the_round=r3,
                                  is_finished=True,
                                  the_set=self.set1)
        g41 = Game.objects.create(name='g41',
                                  started_at=r4.start,
                                  the_round=r4,
                                  is_finished=True,
                                  the_set=self.set1)
        g42 = Game.objects.create(name='g42',
                                  started_at=r4.start,
                                  the_round=r4,
                                  is_finished=True,
                                  the_set=self.set1)
        g51 = Game.objects.create(name='g51',
                                  started_at=r5.start,
                                  the_round=r5,
                                  is_finished=True,
                                  the_set=self.set1)
        g52 = Game.objects.create(name='g52',
                                  started_at=r5.start,
                                  the_round=r5,
                                  is_finished=True,
                                  the_set=self.set1)

        TournamentPlayer.objects.create(player=self.p1, tournament=t)
        TournamentPlayer.objects.create(player=self.p2, tournament=t)
        TournamentPlayer.objects.create(player=self.p3, tournament=t)
        TournamentPlayer.objects.create(player=self.p4, tournament=t)
        # p5 doesn't play at all
        TournamentPlayer.objects.create(player=self.p5, tournament=t)
        TournamentPlayer.objects.create(player=self.p6, tournament=t)
        TournamentPlayer.objects.create(player=self.p7, tournament=t)
        TournamentPlayer.objects.create(player=self.p8, tournament=t, unranked=True)
        TournamentPlayer.objects.create(player=self.p9, tournament=t)
        TournamentPlayer.objects.create(player=self.p10, tournament=t)
        TournamentPlayer.objects.create(player=self.p11, tournament=t)
        TournamentPlayer.objects.create(player=self.p12, tournament=t)
        TournamentPlayer.objects.create(player=self.p13, tournament=t)

        game_scores = {g11: {self.p1: 20,
                             self.p2: 7000,
                             self.p3: 30000,
                             self.p8: 1,
                             self.p9: 2,
                             self.p10: 3,
                             self.p11: 20000},
                       g12: {self.p2: 10000,
                             self.p4: 700,
                             self.p8: 2,
                             self.p9: 300,
                             self.p10: 20000,
                             self.p12: 6000,
                             self.p13: 2000},
                       g21: {self.p1: 1,
                             self.p2: 400,
                             self.p4: 40000,
                             self.p9: 1,
                             self.p11: 8,
                             self.p12: 6,
                             self.p13: 3},
                       g22: {self.p3: 50,
                             self.p8: 30,
                             self.p9: 3000,
                             self.p10: 10,
                             self.p11: 20,
                             self.p12: 80000,
                             self.p13: 40000},
                       g31: {self.p1: 7000,
                             self.p3: 400,
                             self.p8: 200,
                             self.p9: 10000,
                             self.p10: 5000,
                             self.p11: 600,
                             self.p12: 300},
                       g32: {self.p2: 50,
                             self.p4: 7000,
                             self.p8: 3000,
                             self.p9: 5,
                             self.p10: 2,
                             self.p11: 6,
                             self.p13: 2},
                       g41: {self.p1: 90000,
                             self.p4: 4,
                             self.p6: 2000,
                             self.p7: 100,
                             self.p8: 50000,
                             self.p10: 1,
                             self.p11: 3000},
                       g42: {self.p3: 5000,
                             self.p6: 70,
                             self.p8: 5,
                             self.p9: 10,
                             self.p10: 7,
                             self.p12: 6,
                             self.p13: 40},
                       g51: {self.p1: 300,
                             self.p6: 400,
                             self.p8: 9,
                             self.p9: 8,
                             self.p11: 7,
                             self.p12: 3,
                             self.p13: 300},
                       g52: {self.p4: 70,
                             self.p7: 70,
                             self.p8: 7,
                             self.p10: 200,
                             self.p11: 2,
                             self.p12: 60,
                             self.p13: 4}}

        powers = [self.austria,
                  self.england,
                  self.france,
                  self.germany,
                  self.italy,
                  self.russia,
                  self.turkey]

        for g in game_scores.keys():
            for p, s in game_scores[g].items():
                try:
                    with transaction.atomic():
                        RoundPlayer.objects.create(player=p, the_round=g.the_round)
                except IntegrityError:
                    # This player is playing two games this round
                    pass
                the_power = powers.pop(0)
                powers.append(the_power)
                GamePlayer.objects.create(player=p, game=g, power=the_power, score=s)

        for r in t.round_set.all():
            r.update_scores()
        t_scores = t.scores_detail()

        # Check tournament scores
        expected_scores = {self.p1: 97320,
                           self.p2: 17450,
                           self.p3: 35450,
                           self.p4: 47770,
                           self.p5: 0,
                           self.p6: 2470,
                           self.p7: 170,
                           self.p8: 53230,
                           self.p9: 13310,
                           self.p10: 25210,
                           self.p11: 23620,
                           self.p12: 86360,
                           self.p13: 42340}
        for p, score in expected_scores.items():
            with self.subTest(player=p):
                self.assertAlmostEqual(t_scores[p], score)

        # Check GamePlayer score_dropped flags
        for g in game_scores.keys():
            with self.subTest(game=g):
                for p, s in game_scores[g].items():
                    with self.subTest(player=p):
                        gp = GamePlayer.objects.get(player=p, game=g)
                        # All scores less than 10 get dropped
                        self.assertEqual(gp.score_dropped, s < 10)

        # Check round scores and score_dropped flags
        for r in t.round_set.all():
            with self.subTest(round_num=r.number()):
                for rp in r.roundplayer_set.all():
                    with self.subTest(player=rp.player):
                        # With no sitting-out bonus, round scores should all be zero
                        self.assertEqual(rp.score, 0.0)
                        gp_set = GamePlayer.objects.filter(game__the_round=r, player=rp.player).distinct()
                        gp_list = list(gp_set)
                        if len(gp_list) == 1:
                            # Round dropped if game score is dropped (i.e. < 10)
                            score = game_scores[gp_list[0].game][rp.player]
                            self.assertEqual(rp.score_dropped, score < 10)
                        else:
                            score1 = game_scores[gp_list[0].game][rp.player]
                            score2 = game_scores[gp_list[1].game][rp.player]
                            if (score1 < 10) and (score2 < 10):
                                # Neither score counts.
                                # Round is dropped
                                self.assertTrue(rp.score_dropped)
                            else:
                                # One or both scores count.
                                # Round not dropped
                                self.assertFalse(rp.score_dropped)

    def test_tscoringsumgames_scores2(self):
        """Test TScoringSumGames with residual_multiplier"""
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        today = date.today()
        tss = _find_complex_t_scoring_system(2, 0.5)
        t = Tournament.objects.create(name='Tournament Scoring Test',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=NO_SCORING_SYSTEM_STR,
                                      tournament_scoring_system=tss.name,
                                      draw_secrecy=DrawSecrecy.SECRET)

        # Five Rounds
        r1 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r2 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_8)
        r3 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_9)
        r4 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_10)
        r5 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_16)
        # Two finished Games per round
        g11 = Game.objects.create(name='g11',
                                  started_at=r1.start,
                                  the_round=r1,
                                  is_finished=True,
                                  the_set=self.set1)
        g12 = Game.objects.create(name='g12',
                                  started_at=r1.start,
                                  the_round=r1,
                                  is_finished=True,
                                  the_set=self.set1)
        g21 = Game.objects.create(name='g21',
                                  started_at=r2.start,
                                  the_round=r2,
                                  is_finished=True,
                                  the_set=self.set1)
        g22 = Game.objects.create(name='g22',
                                  started_at=r2.start,
                                  the_round=r2,
                                  is_finished=True,
                                  the_set=self.set1)
        g31 = Game.objects.create(name='g31',
                                  started_at=r3.start,
                                  the_round=r3,
                                  is_finished=True,
                                  the_set=self.set1)
        g32 = Game.objects.create(name='g32',
                                  started_at=r3.start,
                                  the_round=r3,
                                  is_finished=True,
                                  the_set=self.set1)
        g41 = Game.objects.create(name='g41',
                                  started_at=r4.start,
                                  the_round=r4,
                                  is_finished=True,
                                  the_set=self.set1)
        g42 = Game.objects.create(name='g42',
                                  started_at=r4.start,
                                  the_round=r4,
                                  is_finished=True,
                                  the_set=self.set1)
        g51 = Game.objects.create(name='g51',
                                  started_at=r5.start,
                                  the_round=r5,
                                  is_finished=True,
                                  the_set=self.set1)
        g52 = Game.objects.create(name='g52',
                                  started_at=r5.start,
                                  the_round=r5,
                                  is_finished=True,
                                  the_set=self.set1)

        TournamentPlayer.objects.create(player=self.p1, tournament=t)
        TournamentPlayer.objects.create(player=self.p2, tournament=t)
        TournamentPlayer.objects.create(player=self.p3, tournament=t)
        TournamentPlayer.objects.create(player=self.p4, tournament=t)
        # p5 doesn't play at all
        TournamentPlayer.objects.create(player=self.p5, tournament=t)
        TournamentPlayer.objects.create(player=self.p6, tournament=t)
        TournamentPlayer.objects.create(player=self.p7, tournament=t)
        TournamentPlayer.objects.create(player=self.p8, tournament=t, unranked=True)
        TournamentPlayer.objects.create(player=self.p9, tournament=t)
        TournamentPlayer.objects.create(player=self.p10, tournament=t)
        TournamentPlayer.objects.create(player=self.p11, tournament=t)
        TournamentPlayer.objects.create(player=self.p12, tournament=t)
        TournamentPlayer.objects.create(player=self.p13, tournament=t)

        game_scores = {g11: {self.p1: 20,
                             self.p2: 7000,
                             self.p3: 30000,
                             self.p8: 1,
                             self.p9: 2,
                             self.p10: 3,
                             self.p11: 20000},
                       g12: {self.p2: 10000,
                             self.p4: 700,
                             self.p8: 2,
                             self.p9: 300,
                             self.p10: 20000,
                             self.p12: 6000,
                             self.p13: 2000},
                       g21: {self.p1: 1,
                             self.p2: 400,
                             self.p4: 40000,
                             self.p9: 1,
                             self.p11: 8,
                             self.p12: 6,
                             self.p13: 3},
                       g22: {self.p3: 50,
                             self.p8: 30,
                             self.p9: 3000,
                             self.p10: 10,
                             self.p11: 20,
                             self.p12: 80000,
                             self.p13: 40000},
                       g31: {self.p1: 7000,
                             self.p3: 400,
                             self.p8: 200,
                             self.p9: 10000,
                             self.p10: 5000,
                             self.p11: 600,
                             self.p12: 300},
                       g32: {self.p2: 50,
                             self.p4: 7000,
                             self.p8: 3000,
                             self.p9: 5,
                             self.p10: 2,
                             self.p11: 6,
                             self.p13: 2},
                       g41: {self.p1: 90000,
                             self.p4: 4,
                             self.p6: 2000,
                             self.p7: 100,
                             self.p8: 50000,
                             self.p10: 1,
                             self.p11: 3000},
                       g42: {self.p3: 5000,
                             self.p6: 70,
                             self.p8: 5,
                             self.p9: 10,
                             self.p10: 7,
                             self.p12: 6,
                             self.p13: 40},
                       g51: {self.p1: 300,
                             self.p6: 400,
                             self.p8: 9,
                             self.p9: 8,
                             self.p11: 7,
                             self.p12: 3,
                             self.p13: 300},
                       g52: {self.p4: 70,
                             self.p7: 70,
                             self.p8: 7,
                             self.p10: 200,
                             self.p11: 2,
                             self.p12: 60,
                             self.p13: 4}}

        powers = [self.austria,
                  self.england,
                  self.france,
                  self.germany,
                  self.italy,
                  self.russia,
                  self.turkey]

        for g in game_scores.keys():
            for p, s in game_scores[g].items():
                try:
                    with transaction.atomic():
                        RoundPlayer.objects.create(player=p, the_round=g.the_round)
                except IntegrityError:
                    # This player is playing two games this round
                    pass
                the_power = powers.pop(0)
                powers.append(the_power)
                GamePlayer.objects.create(player=p, game=g, power=the_power, score=s)

        for r in t.round_set.all():
            r.update_scores()
        t_scores = t.scores_detail()

        # Check tournament scores
        expected_scores = {self.p1: 97000 + (321/6),
                           self.p2: 17000 + (450/4),
                           self.p3: 35000 + (450/4),
                           self.p4: 47000 + (774/6),
                           self.p5: 0,
                           self.p6: 2400 + (70/2),
                           self.p7: 170,
                           self.p8: 53000 + (254/14),
                           self.p9: 13000 + (326/12),
                           self.p10: 25000 + (223/12),
                           self.p11: 23000 + (643/12),
                           self.p12: 86000 + (375/10),
                           self.p13: 42000 + (349/10)}
        for p, score in expected_scores.items():
            with self.subTest(player=p):
                self.assertAlmostEqual(t_scores[p], score)

        # Check GamePlayer score_dropped flags
        for g in game_scores.keys():
            with self.subTest(game=g):
                for p, s in game_scores[g].items():
                    with self.subTest(player=p):
                        gp = GamePlayer.objects.get(player=p, game=g)
                        # All scores are used
                        self.assertFalse(gp.score_dropped)

        # Check round scores and score_dropped flags
        for r in t.round_set.all():
            with self.subTest(round_num=r.number()):
                for rp in r.roundplayer_set.all():
                    with self.subTest(player=rp.player):
                        # With no sitting-out bonus, we don't get a round score at all
                        self.assertEqual(rp.score, 0.0)
                        self.assertFalse(rp.score_dropped)

    def test_tscoringsumgames_scores3(self):
        """ TScoringSumGames with sitting out bonus"""
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        today = date.today()
        tss = _find_t_scoring_system(TScoringSumGames, 4)
        t = Tournament.objects.create(name='Tournament Scoring Test',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=NO_SCORING_SYSTEM_STR,
                                      non_player_round_score=100.0,
                                      non_player_round_score_once=True,
                                      tournament_scoring_system=tss.name,
                                      draw_secrecy=DrawSecrecy.SECRET)

        # Five Rounds
        r1 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r2 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_8)
        r3 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_9)
        r4 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_10)
        r5 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_16)
        # Two finished Games per round
        g11 = Game.objects.create(name='g11',
                                  started_at=r1.start,
                                  the_round=r1,
                                  is_finished=True,
                                  the_set=self.set1)
        g12 = Game.objects.create(name='g12',
                                  started_at=r1.start,
                                  the_round=r1,
                                  is_finished=True,
                                  the_set=self.set1)
        g21 = Game.objects.create(name='g21',
                                  started_at=r2.start,
                                  the_round=r2,
                                  is_finished=True,
                                  the_set=self.set1)
        g22 = Game.objects.create(name='g22',
                                  started_at=r2.start,
                                  the_round=r2,
                                  is_finished=True,
                                  the_set=self.set1)
        g31 = Game.objects.create(name='g31',
                                  started_at=r3.start,
                                  the_round=r3,
                                  is_finished=True,
                                  the_set=self.set1)
        g32 = Game.objects.create(name='g32',
                                  started_at=r3.start,
                                  the_round=r3,
                                  is_finished=True,
                                  the_set=self.set1)
        g41 = Game.objects.create(name='g41',
                                  started_at=r4.start,
                                  the_round=r4,
                                  is_finished=True,
                                  the_set=self.set1)
        g42 = Game.objects.create(name='g42',
                                  started_at=r4.start,
                                  the_round=r4,
                                  is_finished=True,
                                  the_set=self.set1)
        g51 = Game.objects.create(name='g51',
                                  started_at=r5.start,
                                  the_round=r5,
                                  is_finished=True,
                                  the_set=self.set1)
        g52 = Game.objects.create(name='g52',
                                  started_at=r5.start,
                                  the_round=r5,
                                  is_finished=True,
                                  the_set=self.set1)

        TournamentPlayer.objects.create(player=self.p1, tournament=t)
        TournamentPlayer.objects.create(player=self.p2, tournament=t)
        TournamentPlayer.objects.create(player=self.p3, tournament=t)
        TournamentPlayer.objects.create(player=self.p4, tournament=t)
        # p5 doesn't play at all
        TournamentPlayer.objects.create(player=self.p5, tournament=t)
        TournamentPlayer.objects.create(player=self.p6, tournament=t)
        TournamentPlayer.objects.create(player=self.p7, tournament=t)
        TournamentPlayer.objects.create(player=self.p8, tournament=t, unranked=True)
        TournamentPlayer.objects.create(player=self.p9, tournament=t)
        TournamentPlayer.objects.create(player=self.p10, tournament=t)
        TournamentPlayer.objects.create(player=self.p11, tournament=t)
        TournamentPlayer.objects.create(player=self.p12, tournament=t)
        TournamentPlayer.objects.create(player=self.p13, tournament=t)

        game_scores = {g11: {self.p1: 20,
                             self.p2: 7000,
                             self.p3: 30000,
                             self.p8: 1,
                             self.p9: 2,
                             self.p10: 3,
                             self.p11: 20000},
                       g12: {self.p2: 10000,
                             self.p4: 700,
                             self.p8: 2,
                             self.p9: 300,
                             self.p10: 20000,
                             self.p12: 6000,
                             self.p13: 2000},
                       g21: {self.p1: 1,
                             self.p2: 400,
                             self.p4: 40000,
                             self.p9: 1,
                             self.p11: 8,
                             self.p12: 6,
                             self.p13: 3},
                       g22: {self.p3: 50,
                             self.p8: 30,
                             self.p9: 3000,
                             self.p10: 10,
                             self.p11: 20,
                             self.p12: 80000,
                             self.p13: 40000},
                       g31: {self.p1: 7000,
                             self.p3: 400,
                             self.p8: 200,
                             self.p9: 10000,
                             self.p10: 5000,
                             self.p11: 600,
                             self.p12: 300},
                       g32: {self.p2: 50,
                             self.p4: 7000,
                             self.p8: 3000,
                             self.p9: 5,
                             self.p10: 2,
                             self.p11: 6,
                             self.p13: 2},
                       g41: {self.p1: 90000,
                             self.p4: 4,
                             self.p6: 2000,
                             self.p7: 100,
                             self.p8: 50000,
                             self.p10: 1,
                             self.p11: 3000},
                       g42: {self.p3: 5000,
                             self.p6: 70,
                             self.p8: 5,
                             self.p9: 10,
                             self.p10: 7,
                             self.p12: 6,
                             self.p13: 40},
                       g51: {self.p1: 300,
                             self.p6: 400,
                             self.p8: 9,
                             self.p9: 8,
                             self.p11: 7,
                             self.p12: 3,
                             self.p13: 300},
                       g52: {self.p4: 70,
                             self.p7: 70,
                             self.p8: 7,
                             self.p10: 200,
                             self.p11: 2,
                             self.p12: 60,
                             self.p13: 4}}

        powers = [self.austria,
                  self.england,
                  self.france,
                  self.germany,
                  self.italy,
                  self.russia,
                  self.turkey]

        for g in game_scores.keys():
            # Everyone except p5 present for every round
            for p in [self.p1, self.p2, self.p3, self.p4, self.p6, self.p7, self.p8, self.p9, self.p10, self.p11, self.p12, self.p13]:
                try:
                    with transaction.atomic():
                        RoundPlayer.objects.create(player=p, the_round=g.the_round)
                except IntegrityError:
                    # Already added this player for this round
                    pass
            for p, s in game_scores[g].items():
                the_power = powers.pop(0)
                powers.append(the_power)
                GamePlayer.objects.create(player=p, game=g, power=the_power, score=s)

        for r in t.round_set.all():
            r.update_scores()
        t_scores = t.scores_detail()

        # Check tournament scores
        expected_scores = {self.p1: 97320,
                           self.p2: 17500, # Sat 2 rounds
                           self.p3: 35500, # Sat 1 round
                           self.p4: 47770,
                           self.p5: 0,
                           self.p6: 2570, # Sat 3 rounds
                           self.p7: 270, # Sat 3 rounds
                           self.p8: 53230,
                           self.p9: 13310,
                           self.p10: 25210,
                           self.p11: 23620,
                           self.p12: 86360,
                           self.p13: 42340}
        for p, score in expected_scores.items():
            with self.subTest(player=p):
                self.assertAlmostEqual(t_scores[p], score)

        # Check GamePlayer score_dropped flags
        for g in game_scores.keys():
            with self.subTest(game=g):
                for p, s in game_scores[g].items():
                    with self.subTest(player=p):
                        gp = GamePlayer.objects.get(player=p, game=g)
                        # p2 and p3 use their sitting bonus rather than their score < 100
                        if p in [self.p2, self.p3]:
                            self.assertEqual(gp.score_dropped, s < 100)
                        else:
                            self.assertEqual(gp.score_dropped, s < 10)

        # Check round scores and score_dropped flags
        for r in t.round_set.all():
            with self.subTest(round_num=r.number()):
                for rp in r.roundplayer_set.all():
                    with self.subTest(player=rp.player):
                        gp_set = GamePlayer.objects.filter(game__the_round=r, player=rp.player).distinct()
                        gp_list = list(gp_set)
                        if len(gp_list) == 0:
                            # All sitting-out bonuses count towards total score
                            self.assertEqual(rp.score_dropped, rp.score == 0.0)
                        elif len(gp_list) == 1:
                            # Round score should be zero because the player played the round
                            self.assertEqual(rp.score, 0.0)
                            # Round dropped if game score is dropped
                            self.assertEqual(rp.score_dropped, gp_list[0].score_dropped)
                        else:
                            # Round score should be zero because the player played the round
                            self.assertEqual(rp.score, 0.0)
                            score1 = game_scores[gp_list[0].game][rp.player]
                            score2 = game_scores[gp_list[1].game][rp.player]
                            if (score1 < 10) and (score2 < 10):
                                # Neither score counts.
                                # Round is dropped
                                self.assertTrue(rp.score_dropped)
                            else:
                                # One or both scores count.
                                # Round not dropped
                                self.assertFalse(rp.score_dropped)

    def test_tscoringsumgames_scores4(self):
        """Test TScoringSumGames with residual_multiplier and residual_count"""
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        today = date.today()
        tss = _find_complex_t_scoring_system(2, 0.5, 1)
        t = Tournament.objects.create(name='Tournament Scoring Test',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=NO_SCORING_SYSTEM_STR,
                                      tournament_scoring_system=tss.name,
                                      draw_secrecy=DrawSecrecy.SECRET)

        # Five Rounds
        r1 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r2 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_8)
        r3 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_9)
        r4 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_10)
        r5 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=r1.start + HOURS_16)
        # Two finished Games per round
        g11 = Game.objects.create(name='g11',
                                  started_at=r1.start,
                                  the_round=r1,
                                  is_finished=True,
                                  the_set=self.set1)
        g12 = Game.objects.create(name='g12',
                                  started_at=r1.start,
                                  the_round=r1,
                                  is_finished=True,
                                  the_set=self.set1)
        g21 = Game.objects.create(name='g21',
                                  started_at=r2.start,
                                  the_round=r2,
                                  is_finished=True,
                                  the_set=self.set1)
        g22 = Game.objects.create(name='g22',
                                  started_at=r2.start,
                                  the_round=r2,
                                  is_finished=True,
                                  the_set=self.set1)
        g31 = Game.objects.create(name='g31',
                                  started_at=r3.start,
                                  the_round=r3,
                                  is_finished=True,
                                  the_set=self.set1)
        g32 = Game.objects.create(name='g32',
                                  started_at=r3.start,
                                  the_round=r3,
                                  is_finished=True,
                                  the_set=self.set1)
        g41 = Game.objects.create(name='g41',
                                  started_at=r4.start,
                                  the_round=r4,
                                  is_finished=True,
                                  the_set=self.set1)
        g42 = Game.objects.create(name='g42',
                                  started_at=r4.start,
                                  the_round=r4,
                                  is_finished=True,
                                  the_set=self.set1)
        g51 = Game.objects.create(name='g51',
                                  started_at=r5.start,
                                  the_round=r5,
                                  is_finished=True,
                                  the_set=self.set1)
        g52 = Game.objects.create(name='g52',
                                  started_at=r5.start,
                                  the_round=r5,
                                  is_finished=True,
                                  the_set=self.set1)

        TournamentPlayer.objects.create(player=self.p1, tournament=t)
        TournamentPlayer.objects.create(player=self.p2, tournament=t)
        TournamentPlayer.objects.create(player=self.p3, tournament=t)
        TournamentPlayer.objects.create(player=self.p4, tournament=t)
        # p5 doesn't play at all
        TournamentPlayer.objects.create(player=self.p5, tournament=t)
        TournamentPlayer.objects.create(player=self.p6, tournament=t)
        TournamentPlayer.objects.create(player=self.p7, tournament=t)
        TournamentPlayer.objects.create(player=self.p8, tournament=t, unranked=True)
        TournamentPlayer.objects.create(player=self.p9, tournament=t)
        TournamentPlayer.objects.create(player=self.p10, tournament=t)
        TournamentPlayer.objects.create(player=self.p11, tournament=t)
        TournamentPlayer.objects.create(player=self.p12, tournament=t)
        TournamentPlayer.objects.create(player=self.p13, tournament=t)

        game_scores = {g11: {self.p1: 20,
                             self.p2: 7000,
                             self.p3: 30000,
                             self.p8: 1,
                             self.p9: 2,
                             self.p10: 3,
                             self.p11: 20000},
                       g12: {self.p2: 10000,
                             self.p4: 700,
                             self.p8: 2,
                             self.p9: 300,
                             self.p10: 20000,
                             self.p12: 6000,
                             self.p13: 2000},
                       g21: {self.p1: 1,
                             self.p2: 400,
                             self.p4: 40000,
                             self.p9: 1,
                             self.p11: 8,
                             self.p12: 6,
                             self.p13: 3},
                       g22: {self.p3: 50,
                             self.p8: 30,
                             self.p9: 3000,
                             self.p10: 10,
                             self.p11: 20,
                             self.p12: 80000,
                             self.p13: 40000},
                       g31: {self.p1: 7000,
                             self.p3: 400,
                             self.p8: 200,
                             self.p9: 10000,
                             self.p10: 5000,
                             self.p11: 600,
                             self.p12: 300},
                       g32: {self.p2: 50,
                             self.p4: 7000,
                             self.p8: 3000,
                             self.p9: 5,
                             self.p10: 2,
                             self.p11: 6,
                             self.p13: 2},
                       g41: {self.p1: 90000,
                             self.p4: 4,
                             self.p6: 2000,
                             self.p7: 100,
                             self.p8: 50000,
                             self.p10: 1,
                             self.p11: 3000},
                       g42: {self.p3: 5000,
                             self.p6: 70,
                             self.p8: 5,
                             self.p9: 10,
                             self.p10: 7,
                             self.p12: 6,
                             self.p13: 40},
                       g51: {self.p1: 300,
                             self.p6: 400,
                             self.p8: 9,
                             self.p9: 8,
                             self.p11: 7,
                             self.p12: 3,
                             self.p13: 300},
                       g52: {self.p4: 70,
                             self.p7: 70,
                             self.p8: 7,
                             self.p10: 200,
                             self.p11: 2,
                             self.p12: 60,
                             self.p13: 4}}

        powers = [self.austria,
                  self.england,
                  self.france,
                  self.germany,
                  self.italy,
                  self.russia,
                  self.turkey]

        for g in game_scores.keys():
            for p, s in game_scores[g].items():
                try:
                    with transaction.atomic():
                        RoundPlayer.objects.create(player=p, the_round=g.the_round)
                except IntegrityError:
                    # This player is playing two games this round
                    pass
                the_power = powers.pop(0)
                powers.append(the_power)
                GamePlayer.objects.create(player=p, game=g, power=the_power, score=s)

        for r in t.round_set.all():
            r.update_scores()
        t_scores = t.scores_detail()

        # Check tournament scores
        expected_scores = {self.p1: 97000 + (300/2),
                           self.p2: 17000 + (400/2),
                           self.p3: 35000 + (400/2),
                           self.p4: 47000 + (700/2),
                           self.p5: 0,
                           self.p6: 2400 + (70/2),
                           self.p7: 170,
                           self.p8: 53000 + (200/2),
                           self.p9: 13000 + (300/2),
                           self.p10: 25000 + (200/2),
                           self.p11: 23000 + (600/2),
                           self.p12: 86000 + (300/2),
                           self.p13: 42000 + (300/2)}
        for p, score in expected_scores.items():
            with self.subTest(player=p):
                self.assertAlmostEqual(t_scores[p], score)

        # Check GamePlayer score_dropped flags
        for g in game_scores.keys():
            with self.subTest(game=g):
                for p, s in game_scores[g].items():
                    with self.subTest(player=p):
                        gp = GamePlayer.objects.get(player=p, game=g)
                        # All scores are used
                        self.assertFalse(gp.score_dropped)

        # Check round scores and score_dropped flags
        for r in t.round_set.all():
            with self.subTest(round_num=r.number()):
                for rp in r.roundplayer_set.all():
                    with self.subTest(player=rp.player):
                        # With no sitting-out bonus, we don't get a round score at all
                        self.assertEqual(rp.score, 0.0)
                        self.assertFalse(rp.score_dropped)


class ModelTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    # find_scoring_system()
    # Mostly tested implicitly, but we do want to check the error case
    def test_find_g_scoring_system_invalid(self):
        self.assertRaises(InvalidScoringSystem, find_game_scoring_system, 'Invalid System')

    def test_find_r_scoring_system_invalid(self):
        self.assertRaises(InvalidScoringSystem, find_round_scoring_system, 'Invalid System')

    def test_find_t_scoring_system_invalid(self):
        self.assertRaises(InvalidScoringSystem, find_tournament_scoring_system, 'Invalid System')

    # validate_game_name()
    def test_validate_game_name_spaces(self):
        self.assertRaises(ValidationError, validate_game_name, u'space name')

    def test_validate_game_name_slash(self):
        self.assertRaises(ValidationError, validate_game_name, u'nam/e')

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

    # validate_tournament_scoring_system()
    def test_validate_tournament_scoring_system_ok(self):
        self.assertIsNone(validate_tournament_scoring_system(T_SCORING_SYSTEMS[0].name))

    def test_validate_tournament_scoring_system_bad(self):
        self.assertRaises(ValidationError, validate_tournament_scoring_system, "Chris Wins")

    # validate_round_scoring_system()
    def test_validate_round_scoring_system_ok(self):
        self.assertIsNone(validate_round_scoring_system(R_SCORING_SYSTEMS[0].name))

    def test_validate_round_scoring_system_bad(self):
        self.assertRaises(ValidationError, validate_round_scoring_system, "Chris Wins")

    # validate_game_scoring_system()
    def test_validate_game_scoring_system_ok(self):
        self.assertIsNone(validate_game_scoring_system(G_SCORING_SYSTEMS[0].name))

    def test_validate__scoring_system_bad(self):
        self.assertRaises(ValidationError, validate_game_scoring_system, "Chris Wins")

    # TODO game_image_location()

    # scoring_systems_are_compatible()
    def test_scoring_systems_compatible_sum_1(self):
        self.assertFalse(scoring_systems_are_compatible("None", "Sum best 2 rounds"))

    def test_scoring_systems_compatible_sum_2(self):
        for rss in R_SCORING_SYSTEMS:
            with self.subTest(system=rss.name):
                self.assertTrue(scoring_systems_are_compatible(rss.name, "Sum best 2 rounds"))

    def test_scoring_systems_compatible_sum_games_1(self):
        self.assertTrue(scoring_systems_are_compatible("None", "Best single game result"))

    def test_scoring_systems_compatible_sum_games_2(self):
        for rss in R_SCORING_SYSTEMS:
            with self.subTest(system=rss.name):
                self.assertFalse(scoring_systems_are_compatible(rss.name, "Best single game result"))


class AwardTests(TestCase):
    # Award.__str__()
    def test_award_str(self):
        a = Award(name="Test Award", description="The best")
        # TODO validate results
        str(a)


class SeriesTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    # Series.save() and get_absolute_url()
    def test_series_get_absolute_url(self):
        s = Series(name="Test Series", description="Text")
        s.save()
        url = s.get_absolute_url()
        self.assertIn('test-series', url)
        # Clean up
        s.delete()

    def test_series_save_with_slug(self):
        s = Series(name="Test Series", description="Text", slug="sluggy")
        s.save()
        url = s.get_absolute_url()
        self.assertIn('sluggy', url)
        # Clean up
        s.delete()

    def test_series_str(self):
        s = Series(name="Test Series", description="Text", slug="sluggy")
        str(s)


class TeamTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        today = date.today()

        cls.TEST_TEAM_NAME = 'Test team'

        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + HOURS_24,
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          team_size=2,
                                          draw_secrecy=DrawSecrecy.SECRET)
        cls.tm = Team.objects.create(tournament=cls.t,
                                     name=cls.TEST_TEAM_NAME)
        # Add Rounds to t1
        # One team round
        r11 = Round.objects.create(tournament=cls.t,
                                   scoring_system=s1,
                                   dias=True,
                                   is_team_round=True,
                                   start=datetime.combine(cls.t.start_date, time(hour=8, tzinfo=timezone.utc)))
        # and one non-team round
        r12 = Round.objects.create(tournament=cls.t,
                                   scoring_system=s1,
                                   dias=True,
                                   start=r11.start + HOURS_8)
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
                                  the_set=cls.set1)
        g14 = Game.objects.create(name='g14',
                                  started_at=r12.start,
                                  the_round=r12,
                                  the_set=cls.set1)

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

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
        # These two are deliberately not in any tournaments
        cls.p9 = Player.objects.create(first_name='Queenie', last_name='Radiation')
        cls.p10 = Player.objects.create(first_name='Sebastian', last_name='Twinkie')

        # And TournamentPlayers
        TournamentPlayer.objects.create(player=cls.p1, tournament=cls.t, score=1.0)
        TournamentPlayer.objects.create(player=cls.p2, tournament=cls.t, score=2.0, backstabbr_username='nobody')
        TournamentPlayer.objects.create(player=cls.p3, tournament=cls.t, score=3.0)
        TournamentPlayer.objects.create(player=cls.p4, tournament=cls.t, score=4.0)
        TournamentPlayer.objects.create(player=cls.p5, tournament=cls.t, score=5.0, unranked=True)
        TournamentPlayer.objects.create(player=cls.p6, tournament=cls.t, score=6.0)
        TournamentPlayer.objects.create(player=cls.p7, tournament=cls.t, score=7.0, location='The Moon')
        TournamentPlayer.objects.create(player=cls.p8, tournament=cls.t, score=8.0)

        # And the corresponding RoundPlayers
        RoundPlayer.objects.create(player=cls.p1, the_round=r11, score=111.0)
        RoundPlayer.objects.create(player=cls.p2, the_round=r11, score=112.0)
        RoundPlayer.objects.create(player=cls.p3, the_round=r11, score=113.0)
        RoundPlayer.objects.create(player=cls.p4, the_round=r11, score=114.0)
        RoundPlayer.objects.create(player=cls.p5, the_round=r11, score=115.0)
        RoundPlayer.objects.create(player=cls.p6, the_round=r11, score=116.0)
        RoundPlayer.objects.create(player=cls.p7, the_round=r11, score=117.0)
        RoundPlayer.objects.create(player=cls.p8, the_round=r11, score=118.0)
        RoundPlayer.objects.create(player=cls.p1, the_round=r12, score=121.0)
        RoundPlayer.objects.create(player=cls.p2, the_round=r12, score=122.0)
        RoundPlayer.objects.create(player=cls.p3, the_round=r12, score=123.0)
        RoundPlayer.objects.create(player=cls.p4, the_round=r12, score=124.0)
        RoundPlayer.objects.create(player=cls.p5, the_round=r12, score=125.0)
        RoundPlayer.objects.create(player=cls.p6, the_round=r12, score=126.0)
        RoundPlayer.objects.create(player=cls.p7, the_round=r12, score=127.0)
        RoundPlayer.objects.create(player=cls.p8, the_round=r12, score=128.0)

        # And GamePlayers
        GamePlayer.objects.create(player=cls.p1,
                                  game=g11,
                                  power=cls.austria,
                                  score=1.0)
        GamePlayer.objects.create(player=cls.p3, game=g11, power=cls.england,
                                  score=1.1)
        GamePlayer.objects.create(player=cls.p4, game=g11, power=cls.france,
                                  score=1.2)
        GamePlayer.objects.create(player=cls.p5, game=g11, power=cls.germany,
                                  score=1.3)
        GamePlayer.objects.create(player=cls.p6, game=g11, power=cls.italy,
                                  score=1.4)
        GamePlayer.objects.create(player=cls.p7, game=g11, power=cls.russia,
                                  score=1.6)
        GamePlayer.objects.create(player=cls.p8, game=g11, power=cls.turkey,
                                  score=1.5)
        # Add GamePlayers to g12
        GamePlayer.objects.create(player=cls.p7, game=g12, power=cls.austria,
                                  score=2.5)
        GamePlayer.objects.create(player=cls.p6, game=g12, power=cls.england,
                                  score=2.4)
        GamePlayer.objects.create(player=cls.p5, game=g12, power=cls.france,
                                  score=2.2)
        GamePlayer.objects.create(player=cls.p4, game=g12, power=cls.germany,
                                  score=2.3)
        GamePlayer.objects.create(player=cls.p3, game=g12, power=cls.italy,
                                  score=2.1)
        GamePlayer.objects.create(player=cls.p2, game=g12, power=cls.russia,
                                  score=2.0)
        GamePlayer.objects.create(player=cls.p1, game=g12, power=cls.turkey,
                                  score=2.6)
        # Add GamePlayers to g13
        GamePlayer.objects.create(player=cls.p1,
                                  game=g13,
                                  power=cls.austria,
                                  score=3.2)
        GamePlayer.objects.create(player=cls.p3, game=g13, power=cls.england,
                                  score=3.5)
        GamePlayer.objects.create(player=cls.p4, game=g13, power=cls.france,
                                  score=3.1)
        GamePlayer.objects.create(player=cls.p5, game=g13, power=cls.germany,
                                  score=3.6)
        GamePlayer.objects.create(player=cls.p6, game=g13, power=cls.italy,
                                  score=3.3)
        GamePlayer.objects.create(player=cls.p7, game=g13, power=cls.russia,
                                  score=3.0)
        GamePlayer.objects.create(player=cls.p8, game=g13, power=cls.turkey,
                                  score=3.4)
        # Add GamePlayers to g14
        GamePlayer.objects.create(player=cls.p7, game=g14, power=cls.austria,
                                  score=4.4)
        GamePlayer.objects.create(player=cls.p6, game=g14, power=cls.england,
                                  score=4.1)
        GamePlayer.objects.create(player=cls.p5, game=g14, power=cls.france,
                                  score=4.0)
        GamePlayer.objects.create(player=cls.p4, game=g14, power=cls.germany,
                                  score=4.2)
        GamePlayer.objects.create(player=cls.p3, game=g14, power=cls.italy,
                                  score=4.6)
        GamePlayer.objects.create(player=cls.p2, game=g14, power=cls.russia,
                                  score=4.3)
        GamePlayer.objects.create(player=cls.p1, game=g14, power=cls.turkey,
                                  score=4.5)

    def test_two_teams_same_name(self):
        """Two teams of the same name in the same tournament"""
        self.assertRaises(IntegrityError,
                          Team.objects.create,
                          tournament=self.t,
                          name=self.TEST_TEAM_NAME)

    # Team.gameplayers()
    def test_gameplayers(self):
        self.tm.players.add(self.p3)
        self.tm.players.add(self.p4)
        gps = self.tm.gameplayers()
        self.assertEqual(len(gps), 4)
        for gp in gps:
            self.assertIn(gp.player, [self.p3, self.p4])
            self.assertTrue(gp.game.the_round.is_team_round)
        # Cleanup
        self.tm.players.remove(self.p3)
        self.tm.players.remove(self.p4)

    # Team.results()
    def test_results(self):
        """Results for Team with space for more players"""
        self.tm.players.add(self.p4)
        res = self.tm.results()
        self.assertEqual(len(res), self.t.team_size)
        for entry in res:
            p = entry['player']
            if p:
                self.assertIn(p, self.tm.players.all())
                for gp in entry['gameplayers']:
                    self.assertEqual(gp.player, p)

    # Team.score_is_final()
    def test_score_is_final_unfinished_game(self):
        """Team game still in progress"""
        self.tm.players.add(self.p3)
        self.tm.players.add(self.p4)
        r = self.t.round_set.first()
        self.assertTrue(r.is_team_round)
        g = r.game_set.first()
        g.is_finished = True
        g.save()
        self.assertFalse(self.tm.score_is_final())
        # Cleanup
        g.is_finished = False
        g.save()
        self.tm.players.remove(self.p3)
        self.tm.players.remove(self.p4)

    def test_score_is_final_round_not_started(self):
        """Before team round has started"""
        self.tm.players.add(self.p3)
        self.tm.players.add(self.p4)
        r1 = self.t.round_set.first()
        r1.is_team_round = False
        r1.save()
        r2 = self.t.round_set.last()
        r3 = Round.objects.create(tournament=self.t,
                                  scoring_system=r2.scoring_system,
                                  dias=True,
                                  is_team_round=True,
                                  start=r2.start + HOURS_8)
        r3.save()
        self.assertFalse(self.tm.score_is_final())
        # Cleanup
        r1.is_team_round = True
        r1.save()
        r3.delete()
        self.tm.players.remove(self.p3)
        self.tm.players.remove(self.p4)

    def test_score_is_final_between_team_rounds(self):
        """Between team rounds"""
        self.tm.players.add(self.p3)
        self.tm.players.add(self.p4)
        r1 = self.t.round_set.first()
        for g in r1.game_set.all():
            g.is_finished = True
            g.save()
        r2 = self.t.round_set.last()
        r3 = Round.objects.create(tournament=self.t,
                                  scoring_system=r2.scoring_system,
                                  dias=True,
                                  is_team_round=True,
                                  start=r2.start + HOURS_8)
        self.assertFalse(self.tm.score_is_final())
        # Cleanup
        for g in r1.game_set.all():
            g.is_finished = False
            g.save()
        r3.delete()
        self.tm.players.remove(self.p3)
        self.tm.players.remove(self.p4)

    def test_score_is_final_all_team_rounds_over(self):
        """All team games complete"""
        self.tm.players.add(self.p3)
        self.tm.players.add(self.p4)
        r = self.t.round_set.first()
        self.assertTrue(r.is_team_round)
        for g in r.game_set.all():
            g.is_finished = True
            g.save()
        self.assertTrue(self.tm.score_is_final())
        # Cleanup
        for g in r.game_set.all():
            g.is_finished = False
            g.save()
        self.tm.players.remove(self.p3)
        self.tm.players.remove(self.p4)

    # Team.clean()
    def test_clean_no_teams(self):
        """non-team tournament"""
        r = self.t.round_set.get(is_team_round=True)
        r.is_team_round = False
        r.save()
        self.t.team_size = None
        self.t.save()
        self.assertRaises(ValidationError, self.tm.clean)
        # Cleanup
        self.t.team_size = 2
        self.t.save()
        r.is_team_round = True
        r.save()

    def test_clean_ok(self):
        self.tm.players.add(self.p2)
        self.tm.players.add(self.p4)
        self.tm.clean()
        # Cleanup
        self.tm.players.remove(self.p2)
        self.tm.players.remove(self.p4)

    # Team.__str__()
    def test_team_str(self):
        s = str(self.tm)


class DBNCoverageTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        today = date.today()

        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + HOURS_24,
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)

    def test_dbncoverage_str(self):
        c = DBNCoverage(tournament=self.t,
                        dbn_url='https://www.youtube.com/watch?v=jtqvNeVU1tI',
                        description='description')
        str(c)


class TournamentTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)
        t2 = Tournament.objects.create(name='t2',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       is_finished=True,
                                       draw_secrecy=DrawSecrecy.COUNTS)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=8, tzinfo=timezone.utc)))
        r12 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=r11.start + HOURS_8)
        r13 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   is_finished=True,
                                   start=r11.start + HOURS_16)
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=r11.start + HOURS_24)
        # Add Rounds to t2
        r21 = Round.objects.create(tournament=t2,
                                   scoring_system=s1,
                                   dias=False,
                                   start=datetime.combine(t2.start_date, time(hour=8, tzinfo=timezone.utc)))
        r22 = Round.objects.create(tournament=t2,
                                   scoring_system=s1,
                                   dias=False,
                                   start=r21.start + HOURS_8)
        # Add Rounds to t3
        r31 = Round.objects.create(tournament=t3,
                                   scoring_system=s1,
                                   dias=True,
                                   is_finished=True,
                                   start=datetime.combine(t3.start_date, time(hour=8, tzinfo=timezone.utc)),
                                   final_year=1907)
        cls.r32 = Round.objects.create(tournament=t3,
                                       scoring_system=s1,
                                       dias=True,
                                       is_finished=True,
                                       start=r31.start + HOURS_8,
                                       earliest_end_time=r31.start + HOURS_8,
                                       latest_end_time=r31.start + HOURS_9)

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
                            started_at=cls.r32.start,
                            the_round=cls.r32,
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

        # Eliminate Italy in 1903
        CentreCount.objects.create(power=cls.austria, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.england, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1903, count=10)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1903, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1903, count=4)

        # Solo victory for Germany in 1904
        CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=18)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=0)
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
        # These two are deliberately not in any tournaments
        cls.p9 = Player.objects.create(first_name='Queenie', last_name='Radiation')
        cls.p10 = Player.objects.create(first_name='Sebastian', last_name='Twinkie')
        # The remainder are not used in this method but are available for use in tests
        cls.p11 = Player.objects.create(first_name='Ursula', last_name='Vampire')

        # Tournament.news() will call Game.news() for all games in the current round,
        # which will need a player for every country
        # TODO These should really error out with no corresponding RoundPlayer. I guess clean() is not called ?
        # Add GamePlayers to g11
        GamePlayer.objects.create(player=cls.p1,
                                  game=g11,
                                  power=cls.austria,
                                  score=1.0)
        GamePlayer.objects.create(player=cls.p3, game=g11, power=cls.england,
                                  score=1.1)
        GamePlayer.objects.create(player=cls.p4, game=g11, power=cls.france,
                                  score=1.2)
        GamePlayer.objects.create(player=cls.p5, game=g11, power=cls.germany,
                                  score=1.3)
        GamePlayer.objects.create(player=cls.p6, game=g11, power=cls.italy,
                                  score=1.4)
        GamePlayer.objects.create(player=cls.p7, game=g11, power=cls.russia,
                                  score=1.6)
        GamePlayer.objects.create(player=cls.p8, game=g11, power=cls.turkey,
                                  score=1.5)
        # Add GamePlayers to g12
        GamePlayer.objects.create(player=cls.p7, game=g12, power=cls.austria,
                                  score=2.5)
        GamePlayer.objects.create(player=cls.p6, game=g12, power=cls.england,
                                  score=2.4)
        GamePlayer.objects.create(player=cls.p5, game=g12, power=cls.france,
                                  score=2.2)
        GamePlayer.objects.create(player=cls.p4, game=g12, power=cls.germany,
                                  score=2.3)
        GamePlayer.objects.create(player=cls.p3, game=g12, power=cls.italy,
                                  score=2.1)
        GamePlayer.objects.create(player=cls.p2, game=g12, power=cls.russia,
                                  score=2.0)
        GamePlayer.objects.create(player=cls.p1, game=g12, power=cls.turkey,
                                  score=2.6)
        # Add GamePlayers to g13
        GamePlayer.objects.create(player=cls.p1,
                                  game=g13,
                                  power=cls.austria,
                                  score=3.2)
        GamePlayer.objects.create(player=cls.p3, game=g13, power=cls.england,
                                  score=3.5)
        GamePlayer.objects.create(player=cls.p4, game=g13, power=cls.france,
                                  score=3.1)
        GamePlayer.objects.create(player=cls.p5, game=g13, power=cls.germany,
                                  score=3.6)
        GamePlayer.objects.create(player=cls.p6, game=g13, power=cls.italy,
                                  score=3.3)
        GamePlayer.objects.create(player=cls.p7, game=g13, power=cls.russia,
                                  score=3.0)
        GamePlayer.objects.create(player=cls.p8, game=g13, power=cls.turkey,
                                  score=3.4)
        # Add GamePlayers to g14
        GamePlayer.objects.create(player=cls.p7, game=g14, power=cls.austria,
                                  score=4.4)
        GamePlayer.objects.create(player=cls.p6, game=g14, power=cls.england,
                                  score=4.1)
        GamePlayer.objects.create(player=cls.p5, game=g14, power=cls.france,
                                  score=4.0)
        GamePlayer.objects.create(player=cls.p4, game=g14, power=cls.germany,
                                  score=4.2)
        GamePlayer.objects.create(player=cls.p3, game=g14, power=cls.italy,
                                  score=4.6)
        GamePlayer.objects.create(player=cls.p2, game=g14, power=cls.russia,
                                  score=4.3)
        GamePlayer.objects.create(player=cls.p1, game=g14, power=cls.turkey,
                                  score=4.5)
        # And the corresponding RoundPlayers
        RoundPlayer.objects.create(player=cls.p1, the_round=r11, score=111.0)
        RoundPlayer.objects.create(player=cls.p2, the_round=r11, score=112.0)
        RoundPlayer.objects.create(player=cls.p3, the_round=r11, score=113.0)
        RoundPlayer.objects.create(player=cls.p4, the_round=r11, score=114.0)
        RoundPlayer.objects.create(player=cls.p5, the_round=r11, score=115.0)
        RoundPlayer.objects.create(player=cls.p6, the_round=r11, score=116.0)
        RoundPlayer.objects.create(player=cls.p7, the_round=r11, score=117.0)
        RoundPlayer.objects.create(player=cls.p8, the_round=r11, score=118.0)
        RoundPlayer.objects.create(player=cls.p1, the_round=r12, score=121.0)
        RoundPlayer.objects.create(player=cls.p2, the_round=r12, score=122.0)
        RoundPlayer.objects.create(player=cls.p3, the_round=r12, score=123.0)
        RoundPlayer.objects.create(player=cls.p4, the_round=r12, score=124.0)
        RoundPlayer.objects.create(player=cls.p5, the_round=r12, score=125.0)
        RoundPlayer.objects.create(player=cls.p6, the_round=r12, score=126.0)
        RoundPlayer.objects.create(player=cls.p7, the_round=r12, score=127.0)
        RoundPlayer.objects.create(player=cls.p8, the_round=r12, score=128.0)
        # And TournamentPlayers
        TournamentPlayer.objects.create(player=cls.p1, tournament=t1, score=1.0)
        TournamentPlayer.objects.create(player=cls.p2, tournament=t1, score=2.0, backstabbr_username='nobody')
        TournamentPlayer.objects.create(player=cls.p3, tournament=t1, score=3.0)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t1, score=4.0)
        TournamentPlayer.objects.create(player=cls.p5, tournament=t1, score=5.0, unranked=True)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t1, score=6.0)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t1, score=7.0, location='The Moon')
        TournamentPlayer.objects.create(player=cls.p8, tournament=t1, score=8.0)

        # Add TournamentPlayers to t3
        TournamentPlayer.objects.create(player=cls.p5, tournament=t3, score=147.3)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t3, score=47.3)
        # Add RoundPlayers to r31
        RoundPlayer.objects.create(player=cls.p5, the_round=r31, score=0.1)
        RoundPlayer.objects.create(player=cls.p7, the_round=r31, score=5.0)
        # Add RoundPlayers to r32
        RoundPlayer.objects.create(player=cls.p5, the_round=cls.r32, score=47.3)
        RoundPlayer.objects.create(player=cls.p7, the_round=cls.r32, score=57.3)

    # Tournament.powers_assigned_from_prefs()
    def test_tournament_powers_Assigned_from_prefs_false(self):
        t = Tournament.objects.first()
        self.assertFalse(t.powers_assigned_from_prefs())

    def test_tournament_powers_assigned_from_prefs_true(self):
        today = date.today()
        t = Tournament(name='Test Tournament',
                       start_date=today,
                       end_date=today + HOURS_24,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       power_assignment=PowerAssignMethods.PREFERENCES)
        self.assertTrue(t.powers_assigned_from_prefs())

    # Tournament.show_game_urls()
    def test_tournament_show_game_urls_flag_unset(self):
        t = Tournament.objects.first()
        self.assertFalse(t.delay_game_url_publication)
        self.assertTrue(t.show_game_urls())

    def test_tournament_show_game_urls_still_playing(self):
        t = Tournament.objects.first()
        self.assertFalse(t.delay_game_url_publication)
        end = t.end_date
        # Move the end date of the Tournament and flag as delaying game URL display
        t.delay_game_url_publication = True
        t.end_date = date.today() + HOURS_24
        t.save(update_fields=['delay_game_url_publication', 'end_date'])
        self.assertFalse(t.show_game_urls())
        # Clean up
        t.delay_game_url_publication = False
        t.end_date = end
        t.save(update_fields=['delay_game_url_publication', 'end_date'])

    def test_tournament_show_game_urls_later(self):
        t = Tournament.objects.first()
        self.assertFalse(t.delay_game_url_publication)
        start = t.start_date
        end = t.end_date
        # Move the end date of the Tournament and flag as delaying game URL display
        t.delay_game_url_publication = True
        today = date.today()
        t.start_date = today - HOURS_72
        t.end_date = today - HOURS_48
        t.save(update_fields=['delay_game_url_publication', 'start_date', 'end_date'])
        self.assertTrue(t.show_game_urls())
        # Clean up
        t.delay_game_url_publication = False
        t.start_date = start
        t.end_date = end
        t.save(update_fields=['delay_game_url_publication', 'start_date', 'end_date'])

    # Tournament._calculated_scores()
    def test_tournament_calculated_scores_invalid(self):
        today = date.today()
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=today,
                                                      end_date=today + HOURS_24,
                                                      tournament_scoring_system='Invalid System',
                                                      round_scoring_system=R_SCORING_SYSTEMS[0].name)
        self.assertRaises(InvalidScoringSystem, t._calculated_scores)

    def test_tournament_calculated_scores_unfinished(self):
        t = Tournament.objects.get(name='t1')
        scores = t._calculated_scores()
        self.assertEqual(len(scores), t.tournamentplayer_set.count())
        # This should be recalculated from the round scores
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                rps = tp.player.roundplayer_set.filter(the_round__tournament=t)
                total = rps.aggregate(Sum('score'))['score__sum']
                self.assertEqual(scores[tp.player], total)

    def test_tournament_calculated_scores_recalculate(self):
        t = Tournament.objects.get(name='t3')
        scores = t._calculated_scores()
        self.assertEqual(len(scores), 2)
        # This should be recalculated from the round scores
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                rps = tp.player.roundplayer_set.filter(the_round__tournament=t)
                total = rps.aggregate(Sum('score'))['score__sum']
                self.assertEqual(scores[tp.player], total)

    def test_tournament_calculated_scores_for_players(self):
        t = Tournament.objects.get(name='t1')
        player_list = [self.p2, self.p3, self.p6, self.p8]
        rps = RoundPlayer.objects.filter(the_round__tournament=t).filter(player__in=player_list)
        scores = t._calculated_scores(for_players=rps)
        self.assertEqual(len(scores), len(player_list))
        # This should be recalculated from the round scores
        for tp in t.tournamentplayer_set.filter(player__in=player_list):
            with self.subTest(player=tp.player):
                rps = tp.player.roundplayer_set.filter(the_round__tournament=t)
                total = rps.aggregate(Sum('score'))['score__sum']
                self.assertEqual(scores[tp.player], total)

    def test_tournament_calculated_scores_first_round(self):
        # Pass in a QuerySet to limit the RoundPlayers
        t = Tournament.objects.get(name='t3')
        # Just the first round
        rps = t.round_numbered(1).roundplayer_set.all()
        scores = t._calculated_scores(for_players=rps)
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                rp = rps.get(player=tp.player)
                self.assertAlmostEqual(scores[tp.player], rp.score)

    # Tournament.scores_detail()
    def test_tournament_scores_detail_finished(self):
        t = Tournament.objects.get(name='t3')
        # Record expected results
        exp = {}
        for tp in t.tournamentplayer_set.all():
            exp[tp] = tp.score
        scores = t.scores_detail()
        self.assertEqual(len(scores), 2)
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                self.assertAlmostEqual(scores[tp.player], exp[tp])

    def test_tournament_scores_detail_unfinished(self):
        t = Tournament.objects.get(name='t1')
        scores = t.scores_detail()
        # Every TournamentPlayer should have a score
        self.assertEqual(len(scores), t.tournamentplayer_set.count())
        # Scores should just be read from TournamentPlayers
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                self.assertAlmostEqual(scores[tp.player], tp.score)

    def test_tournament_scores_detail_before_start(self):
        t = Tournament.objects.get(name='t2')
        self.assertEqual(t.tournamentplayer_set.count(), 0)
        for r in t.round_set.all():
            self.assertEqual(r.roundplayer_set.count(), 0)
        the_score = 17.3
        tp = TournamentPlayer.objects.create(player=self.p5, tournament=t, score=the_score)
        # Ensure that all TournamentPlayers are included. although there are no RoundPlayers
        scores = t.scores_detail()
        self.assertEqual(len(scores), 1)
        self.assertAlmostEqual(scores[tp.player], the_score)
        # Cleanup
        tp.delete()

    def test_tournament_scores_detail_with_non_player(self):
        # Only interesting for unfinished tournaments
        t = Tournament.objects.get(name='t1')
        # Add an extra player, who didn't actually play
        tp = TournamentPlayer(tournament=t, player=self.p10)
        tp.save()
        scores = t.scores_detail()
        # Players who didn't play should get a score of zero
        self.assertEqual(scores[tp.player], 0.0)
        # Cleanup
        tp.delete()

    # Tournament.positions_and_scores()
    def test_tournament_positions_and_scores_finished(self):
        t = Tournament.objects.get(name='t3')
        # Record expected results
        scores = {}
        for tp in t.tournamentplayer_set.all():
            scores[tp] = tp.score
        p_and_s = t.positions_and_scores()
        # This should just read the TournamentPlayer attributes
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                self.assertAlmostEqual(p_and_s[tp.player][1], scores[tp])

    def test_tournament_positions_and_scores_unfinished(self):
        t = Tournament.objects.get(name='t1')
        # Record expected results
        scores = {}
        for tp in t.tournamentplayer_set.all():
            scores[tp] = tp.score
        p_and_s = t.positions_and_scores()
        # This should just read the TournamentPlayer attributes
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                self.assertAlmostEqual(p_and_s[tp.player][1], scores[tp])

    def test_tournament_positions_and_scores_with_unranked(self):
        t = Tournament.objects.get(name='t1')
        scores = {}
        for tp in t.tournamentplayer_set.all():
            scores[tp] = tp.score
            tp.score = 0.0
            tp.save()
        p_and_s = t.positions_and_scores()
        # The unranked player should have a special position
        self.assertEqual(p_and_s[self.p5][0], Tournament.UNRANKED)
        # As everyone else has the same score, they should all be ranked (joint) first
        for k in p_and_s:
            if k != self.p5:
                with self.subTest(k=k):
                    self.assertEqual(p_and_s[k][0], 1)
        # Cleanup
        for tp in t.tournamentplayer_set.all():
            tp.score = scores[tp]
            tp.save()

    def test_tournament_positions_and_scores_round_zero(self):
        t = Tournament.objects.get(name='t3')
        # Store the current scores
        scores = {}
        for tp in t.tournamentplayer_set.all():
            scores[tp] = tp.score
        for r in t.round_set.all():
            for rp in r.roundplayer_set.all():
                scores[rp] = rp.score
            # Call update_scores() to set rp.tournament_score
            r.update_scores()
        p_and_s = t.positions_and_scores(after_round_num=0)
        # All scores should be zero before the first round
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                self.assertAlmostEqual(p_and_s[tp.player][1], 0.0)
                # Everyone should be joint first
                self.assertEqual(p_and_s[tp.player][0], 1)
        # Cleanup
        for xp, score in scores.items():
            xp.score = score
            xp.save()

    def test_tournament_positions_and_scores_round(self):
        t = Tournament.objects.get(name='t3')
        # Store the current scores
        scores = {}
        for tp in t.tournamentplayer_set.all():
            scores[tp] = tp.score
        for r in t.round_set.all():
            for rp in r.roundplayer_set.all():
                scores[rp] = rp.score
            # Call update_scores() to set rp.tournament_score
            r.update_scores()
        p_and_s = t.positions_and_scores(after_round_num=1)
        # Just the first round should count
        rps = t.round_numbered(1).roundplayer_set.all()
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                rp = rps.get(player=tp.player)
                self.assertAlmostEqual(p_and_s[tp.player][1], rp.score)
        # Cleanup
        for xp, score in scores.items():
            xp.score = score
            xp.save()

    def test_tournament_positions_and_scores_last_round(self):
        t = Tournament.objects.get(name='t3')
        # Store the current scores
        scores = {}
        for tp in t.tournamentplayer_set.all():
            scores[tp] = tp.score
        for r in t.round_set.all():
            for rp in r.roundplayer_set.all():
                scores[rp] = rp.score
            # Call update_scores() to set rp.tournament_score
            r.update_scores()
        p_and_s = t.positions_and_scores(after_round_num=t.round_set.count())
        # This should just report the scores stored in the database
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                self.assertAlmostEqual(p_and_s[tp.player][1], tp.score)
        # Cleanup
        for xp, score in scores.items():
            xp.score = score
            xp.save()

    def test_tournament_positions_and_scores_tscoringsumgames(self):
        # Check that positions_and_scores() with round specified
        # doesn't break TScoringSumGames
        t = Tournament.objects.get(name='t3')
        # Store current scores
        t_scores = {}
        r_scores = {}
        r = t.round_numbered(1)
        rps = r.roundplayer_set.all()
        for tp in t.tournamentplayer_set.all():
            t_scores[tp] = tp.score
            rp = rps.get(player=tp.player)
            r_scores[tp] = rp.score
        t_sys = t.tournament_scoring_system
        r_sys = t.round_scoring_system
        tss = _find_t_scoring_system(TScoringSumGames, 3)
        t.tournament_scoring_system = tss.name
        t.round_scoring_system = 'None'
        t.save()
        # Changing scoring system will re-calculate scores, so we need to restore them
        for tp in t.tournamentplayer_set.all():
            tp.score = t_scores[tp]
            tp.save()
            rp = rps.get(player=tp.player)
            rp.score = r_scores[tp]
            rp.save()
        p_and_s = t.positions_and_scores(after_round_num=1)
        # TournamentPlayer and RoundPlayer scores should be unchanged
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                tp.refresh_from_db()
                self.assertEqual(tp.score, t_scores[tp])
                rp = rps.get(player=tp.player)
                rp.refresh_from_db()
                self.assertEqual(rp.score, r_scores[tp])
        # Cleanup
        t.tournament_scoring_system = t_sys
        t.round_scoring_system = r_sys
        t.save()
        # Changing scoring system will re-calculate scores, so we need to restore them
        for tp in t.tournamentplayer_set.all():
            tp.score = t_scores[tp]
            tp.save()
            rp = rps.get(player=tp.player)
            rp.score = r_scores[tp]
            rp.save()

    # Tournament.team_scores()
    def test_tournament_team_scores_current(self):
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save(update_fields=['team_size'])
        r1 = t.round_numbered(1)
        r1.is_team_round = True
        r1.save(update_fields=['is_team_round'])
        tm1 = Team.objects.create(tournament=t,
                                  score=10.0,
                                  name='Test team 1')
        tm1.players.add(self.p3)
        tm1.players.add(self.p5)
        tm2 = Team.objects.create(tournament=t,
                                  score=5.0,
                                  name='Test team 2')
        tm2.players.add(self.p1)
        tm2.players.add(self.p6)
        scores = t.team_scores()
        # This should return the score from the Team objects
        self.assertEqual(len(scores), 2)
        for tm, (rank, score) in scores.items():
            if tm == tm1:
                self.assertEqual(rank, 1)
                self.assertEqual(score, 10.0)
            elif tm == tm2:
                self.assertEqual(rank, 2)
                self.assertEqual(score, 5.0)
            else:
                self.assertTrue(False)
        # Cleanup
        tm1.delete()
        tm2.delete()
        r1.is_team_round = False
        r1.save(update_fields=['is_team_round'])
        t.team_size = None
        t.save(update_fields=['team_size'])

    def test_tournament_team_scores_before_team_rounds(self):
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save(update_fields=['team_size'])
        r2 = t.round_numbered(2)
        r2.is_team_round = True
        r2.save(update_fields=['is_team_round'])
        tm1 = Team.objects.create(tournament=t,
                                  score=10.0,
                                  name='Test team 1')
        tm1.players.add(self.p3)
        tm1.players.add(self.p5)
        tm2 = Team.objects.create(tournament=t,
                                  score=5.0,
                                  name='Test team 2')
        tm2.players.add(self.p1)
        tm2.players.add(self.p6)
        scores = t.team_scores(after_round_num=1)
        # All teams should score zero
        self.assertEqual(len(scores), 2)
        for tm, (rank, score) in scores.items():
            if tm == tm1:
                self.assertEqual(rank, 1)
                self.assertAlmostEqual(score, 0.0)
            elif tm == tm2:
                self.assertEqual(rank, 1)
                self.assertAlmostEqual(score, 0.0)
            else:
                self.assertTrue(False)
        # Cleanup
        tm1.delete()
        tm2.delete()
        r2.is_team_round = False
        r2.save(update_fields=['is_team_round'])
        t.team_size = None
        t.save(update_fields=['team_size'])

    def test_tournament_team_scores_between_team_rounds(self):
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save(update_fields=['team_size'])
        r1 = t.round_numbered(1)
        r1.is_team_round = True
        r1.save(update_fields=['is_team_round'])
        r2 = t.round_numbered(2)
        r2.is_team_round = True
        r2.save(update_fields=['is_team_round'])
        tm1 = Team.objects.create(tournament=t,
                                  score=10.0,
                                  name='Test team 1')
        tm1.players.add(self.p3)
        tm1.players.add(self.p5)
        tm2 = Team.objects.create(tournament=t,
                                  score=5.0,
                                  name='Test team 2')
        tm2.players.add(self.p1)
        tm2.players.add(self.p6)
        scores = t.team_scores(after_round_num=1)
        self.assertEqual(len(scores), 2)
        for tm, (rank, score) in scores.items():
            if tm == tm1:
                self.assertEqual(rank, 2)
                self.assertAlmostEqual(score, 1.1 + 2.1 + 1.3 + 2.2)
            elif tm == tm2:
                self.assertEqual(rank, 1)
                self.assertAlmostEqual(score, 1.0 + 2.6 + 1.4 + 2.4)
            else:
                self.assertTrue(False)
        # Cleanup
        tm1.delete()
        tm2.delete()
        r1.is_team_round = False
        r1.save(update_fields=['is_team_round'])
        r2.is_team_round = False
        r2.save(update_fields=['is_team_round'])
        t.team_size = None
        t.save(update_fields=['team_size'])

    def test_tournament_team_scores_after_team_rounds(self):
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save(update_fields=['team_size'])
        r1 = t.round_numbered(1)
        r1.is_team_round = True
        r1.save(update_fields=['is_team_round'])
        r2 = t.round_numbered(2)
        r2.is_team_round = True
        r2.save(update_fields=['is_team_round'])
        tm1 = Team.objects.create(tournament=t,
                                  score=10.0,
                                  name='Test team 1')
        tm1.players.add(self.p3)
        tm1.players.add(self.p5)
        tm2 = Team.objects.create(tournament=t,
                                  score=5.0,
                                  name='Test team 2')
        tm2.players.add(self.p1)
        tm2.players.add(self.p6)
        scores = t.team_scores(after_round_num=2)
        self.assertEqual(len(scores), 2)
        for tm, (rank, score) in scores.items():
            if tm == tm1:
                self.assertEqual(rank, 2)
                self.assertAlmostEqual(score, 1.1 + 2.1 + 1.3 + 2.2 + 3.5 + 4.6 + 3.6 + 4.0)
            elif tm == tm2:
                self.assertEqual(rank, 1)
                self.assertAlmostEqual(score, 1.0 + 2.6 + 1.4 + 2.4 + 3.2 + 4.5 + 3.3 + 4.1)
            else:
                self.assertTrue(False)
        # Cleanup
        tm1.delete()
        tm2.delete()
        r1.is_team_round = False
        r1.save(update_fields=['is_team_round'])
        r2.is_team_round = False
        r2.save(update_fields=['is_team_round'])
        t.team_size = None
        t.save(update_fields=['team_size'])

    # Tournament.winner()
    def test_tournament_winner_not_finished(self):
        t = Tournament.objects.get(name='t1')
        self.assertEqual(t.winner(), None)

    def test_tournament_winner_finished(self):
        t = Tournament.objects.get(name='t3')
        self.assertEqual(t.winner(), self.p5)

    # Tournament.update_scores()
    def test_tournament_update_scores_before_start(self):
        t = Tournament.objects.get(name='t2')
        self.assertEqual(t.tournamentplayer_set.count(), 0)
        self.assertEqual(RoundPlayer.objects.filter(the_round__tournament=t).count(), 0)
        # Add some TournamentPlayers with non-zero scores
        TournamentPlayer.objects.create(player=self.p5, tournament=t, score=147.3)
        TournamentPlayer.objects.create(player=self.p7, tournament=t, score=47.3)
        t.update_scores()
        # Verify that all TournamentPlayers' scores are updated. although there are no RoundPlayers
        for tp in t.tournamentplayer_set.all():
            self.assertEqual(tp.score, 0.0)
        # Clean up
        t.tournamentplayer_set.all().delete()

    def test_tournament_update_scores_with_non_player(self):
        t = Tournament.objects.get(name='t1')
        # Add an extra player, who didn't actually play, with a non-zero score
        tp = TournamentPlayer(tournament=t, player=self.p10, score=76.3)
        tp.save()
        t.update_scores()
        # Players who didn't play should get a score of zero
        tp.refresh_from_db()
        self.assertEqual(tp.score, 0.0)
        tp.delete()

    def test_tournament_update_scores(self):
        today = date.today()
        t = Tournament(name='t5',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=DrawSecrecy.SECRET)
        t.save()
        tp = TournamentPlayer(tournament=t, player=self.p1, score=1)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p2, score=2)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p3, score=3)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p4, score=4)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p5, score=5)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p6, score=6)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p7, score=7)
        tp.save()
        # Include a player who didn't play any games
        tp = TournamentPlayer(tournament=t, player=self.p8, score=8)
        tp.save()
        r = Round(tournament=t,
                  scoring_system='Sum of Squares',
                  dias=True,
                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r.save()
        rp = RoundPlayer(the_round=r, player=self.p1, score=7)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p2, score=6)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p3, score=5)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p4, score=4)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p5, score=3)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p6, score=2)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p7, score=1)
        rp.save()
        # We need a finished Game in the Round so the Round is finished
        g = Game(name='newgame2',
                 started_at=r.start,
                 the_round=r,
                 is_finished=True,
                 the_set=self.set1)
        g.save()
        t.update_scores()
        # Score for all TournamentPlayers should be updated
        # from the RoundPlayer scores
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                try:
                    rp = RoundPlayer.objects.filter(player=tp.player,
                                                    the_round__tournament=t).get()
                    self.assertEqual(tp.score, rp.score)
                except RoundPlayer.DoesNotExist:
                    self.assertEqual(tp.score, 0.0)
        # Note that this will also delete all other objects for the Tournament
        t.delete()

    def test_tournament_update_scores_for_players(self):
        today = date.today()
        t = Tournament(name='t5',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=DrawSecrecy.SECRET)
        t.save()
        tp = TournamentPlayer(tournament=t, player=self.p1, score=1)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p2, score=2)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p3, score=3)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p4, score=4)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p5, score=5)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p6, score=6)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p7, score=7)
        tp.save()
        # Include two players who didn't play any games
        tp = TournamentPlayer(tournament=t, player=self.p8, score=8)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p9, score=9)
        tp.save()
        r = Round(tournament=t,
                  scoring_system='Sum of Squares',
                  dias=True,
                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r.save()
        rp = RoundPlayer(the_round=r, player=self.p1, score=7)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p2, score=6)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p3, score=5)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p4, score=4)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p5, score=3)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p6, score=2)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p7, score=1)
        rp.save()
        # Which players to update - include some but not all who
        # played and some but not all who didn't
        player_list = [self.p2, self.p3, self.p9]
        # Remember the scores we set
        initial_scores = {}
        for tp in t.tournamentplayer_set.all():
            initial_scores[tp] = tp.score
        # We need a finished Game in the Round so the Round is finished
        g = Game(name='newgame2',
                 started_at=r.start,
                 the_round=r,
                 is_finished=True,
                 the_set=self.set1)
        g.save()
        t.update_scores(player_list)
        # Score for specified TournamentPlayers should be updated
        # from the RoundPlayer scores
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                if tp.player in player_list:
                    try:
                        rp = RoundPlayer.objects.filter(player=tp.player,
                                                        the_round__tournament=t).get()
                        self.assertEqual(tp.score, rp.score)
                    except RoundPlayer.DoesNotExist:
                        self.assertEqual(tp.score, 0.0)
                else:
                        self.assertEqual(initial_scores[tp], tp.score)
        # Clean up
        t.delete()

    def test_tournament_update_scores_handicap(self):
        today = date.today()
        t = Tournament(name='t5',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       handicaps=True,
                       draw_secrecy=DrawSecrecy.SECRET)
        t.save()
        tp = TournamentPlayer(tournament=t, player=self.p1, score=1, handicap=10)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p2, score=2, handicap=10)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p3, score=3, handicap=10)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p4, score=4, handicap=20)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p5, score=5, handicap=20)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p6, score=6, handicap=20)
        tp.save()
        tp = TournamentPlayer(tournament=t, player=self.p7, score=7, handicap=10)
        tp.save()
        # Include a player who didn't play any games
        tp = TournamentPlayer(tournament=t, player=self.p8, score=8, handicap=30)
        tp.save()
        r = Round(tournament=t,
                  scoring_system='Sum of Squares',
                  dias=True,
                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r.save()
        rp = RoundPlayer(the_round=r, player=self.p1, score=7)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p2, score=6)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p3, score=5)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p4, score=4)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p5, score=3)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p6, score=2)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p7, score=1)
        rp.save()
        # We need a finished Game in the Round so the Round is finished
        g = Game(name='newgame2',
                 started_at=r.start,
                 the_round=r,
                 is_finished=False,
                 the_set=self.set1)
        g.save()
        t.update_scores()
        # Score for all TournamentPlayers should be updated
        # from the RoundPlayer scores but not handicaps
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                try:
                    rp = RoundPlayer.objects.filter(player=tp.player,
                                                    the_round__tournament=t).get()
                    self.assertEqual(tp.score, rp.score)
                except RoundPlayer.DoesNotExist:
                    self.assertEqual(tp.score, 0.0)
        # Now finish that Game and call update_scores() again
        g.is_finished = True
        g.save()
        t.update_scores()
        # Score for all TournamentPlayers should be updated
        # from the RoundPlayer scores and handicaps
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                try:
                    rp = RoundPlayer.objects.filter(player=tp.player,
                                                    the_round__tournament=t).get()
                    self.assertEqual(tp.score, rp.score + tp.handicap)
                except RoundPlayer.DoesNotExist:
                    self.assertEqual(tp.score, 0.0)
        # Note that this will also delete all other objects for the Tournament
        t.delete()

    def test_tournament_update_scores_awards(self):
        # Verify that best country awards get set
        today = date.today()
        t = Tournament(name='t5',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       is_finished=True,
                       draw_secrecy=DrawSecrecy.SECRET)
        t.save()
        t.awards.create(name='Best Austria', power=self.austria, description='')
        t.awards.create(name='Best England', power=self.england, description='')
        t.awards.create(name='Best France', power=self.france, description='')
        t.awards.create(name='Best Germany', power=self.germany, description='')
        t.awards.create(name='Best Italy', power=self.italy, description='')
        t.awards.create(name='Best Russia', power=self.russia, description='')
        t.awards.create(name='Best Turkey', power=self.turkey, description='')
        TournamentPlayer.objects.create(tournament=t, player=self.p1, score=1)
        TournamentPlayer.objects.create(tournament=t, player=self.p2, score=2)
        TournamentPlayer.objects.create(tournament=t, player=self.p3, score=3)
        TournamentPlayer.objects.create(tournament=t, player=self.p4, score=4)
        TournamentPlayer.objects.create(tournament=t, player=self.p5, score=5)
        TournamentPlayer.objects.create(tournament=t, player=self.p6, score=6)
        TournamentPlayer.objects.create(tournament=t, player=self.p7, score=7)
        # Include a player who didn't play any games
        TournamentPlayer.objects.create(tournament=t, player=self.p8, score=8)
        r = Round.objects.create(tournament=t,
                                 scoring_system='Sum of Squares',
                                 dias=True,
                                 is_finished=True,
                                 start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        RoundPlayer.objects.create(the_round=r, player=self.p1, score=7)
        RoundPlayer.objects.create(the_round=r, player=self.p2, score=6)
        RoundPlayer.objects.create(the_round=r, player=self.p3, score=5)
        RoundPlayer.objects.create(the_round=r, player=self.p4, score=4)
        RoundPlayer.objects.create(the_round=r, player=self.p5, score=3)
        RoundPlayer.objects.create(the_round=r, player=self.p6, score=2)
        RoundPlayer.objects.create(the_round=r, player=self.p7, score=1)
        # We need a finished Game in the Round so the Round is finished
        g = Game.objects.create(name='newgame2',
                                started_at=r.start,
                                the_round=r,
                                is_finished=True,
                                the_set=self.set1)
        GamePlayer.objects.create(game=g, player=self.p1, power=self.italy, score=7)
        GamePlayer.objects.create(game=g, player=self.p2, power=self.russia, score=6)
        GamePlayer.objects.create(game=g, player=self.p3, power=self.turkey, score=5)
        GamePlayer.objects.create(game=g, player=self.p4, power=self.england, score=4)
        GamePlayer.objects.create(game=g, player=self.p5, power=self.france, score=3)
        GamePlayer.objects.create(game=g, player=self.p6, power=self.austria, score=2)
        GamePlayer.objects.create(game=g, player=self.p7, power=self.germany, score=1)

        t.update_scores()

        # Awards should be given to the corresponding TournamentPlayers
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                try:
                    # Each player of the game should get the corresponding Best Country award
                    gp = GamePlayer.objects.get(player=tp.player, game=g)
                    self.assertEqual(tp.awards.count(), 1)
                    self.assertEqual(tp.awards.first().power, gp.power)
                except GamePlayer.DoesNotExist:
                    self.assertEqual(tp.awards.count(), 0)

        # Clean up
        for a in t.awards.all():
            a.delete()
        # Note that this will also delete all other objects for the Tournament
        t.delete()

    # Tournament.update_team_scores()
    def test_tournament_update_team_scores_no_list(self):
        """no player list"""
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save(update_fields=['team_size'])
        r1 = t.round_numbered(1)
        r1.is_team_round = True
        r1.save(update_fields=['is_team_round'])
        tm = Team.objects.create(tournament=t,
                                 score=10.0,
                                 name='Test team')
        tm.players.add(self.p3)
        tm.players.add(self.p4)
        t.update_team_scores()
        tm.refresh_from_db()
        self.assertAlmostEqual(tm.score, 1.1 + 1.2 + 2.3 + 2.1)
        # Cleanup
        tm.delete()
        t.team_size = None
        t.save()
        r1.is_team_round = False
        r1.save()

    def test_tournament_update_team_scores_some_team_members(self):
        """with player list including only some team members"""
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save(update_fields=['team_size'])
        r1 = t.round_numbered(1)
        r1.is_team_round = True
        r1.save(update_fields=['is_team_round'])
        tm = Team.objects.create(tournament=t,
                                 score=10.0,
                                 name='Test team')
        tm.players.add(self.p3)
        tm.players.add(self.p4)
        t.update_team_scores(for_players=[self.p3, self.p6])
        tm.refresh_from_db()
        self.assertAlmostEqual(tm.score, 1.1 + 1.2 + 2.3 + 2.1)
        # Cleanup
        tm.delete()
        t.team_size = None
        t.save()
        r1.is_team_round = False
        r1.save()

    def test_tournament_update_team_scores_no_team_members(self):
        """no team gameplayers"""
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save(update_fields=['team_size'])
        r1 = t.round_numbered(1)
        r1.is_team_round = True
        r1.save(update_fields=['is_team_round'])
        tm = Team.objects.create(tournament=t,
                                 score=10.0,
                                 name='Test team')
        tm.players.add(self.p3)
        tm.players.add(self.p4)
        t.update_team_scores(for_players=[self.p1, self.p6])
        tm.refresh_from_db()
        # Score should be unchanged
        self.assertAlmostEqual(tm.score, 10.0)
        # Cleanup
        tm.delete()
        t.team_size = None
        t.save()
        r1.is_team_round = False
        r1.save()

    # Tournament.round_numbered()
    def test_tournament_round_numbered_negative(self):
        t = Tournament.objects.get(name='t1')
        self.assertRaises(Round.DoesNotExist, t.round_numbered, -1)

    def test_tournament_round_numbered_3(self):
        t = Tournament.objects.get(name='t1')
        self.assertEqual(t.round_numbered(3).number(), 3)

    # Tournament.team_rounds()
    def test_tournament_team_rounds(self):
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save()
        r1 = t.round_numbered(1)
        r1.is_team_round = True
        r1.save()
        r3 = t.round_numbered(3)
        r3.is_team_round = True
        r3.save()
        rds = t.team_rounds()
        self.assertEqual(len(rds), 2)
        for r in rds:
            self.assertTrue(r.is_team_round)
        # Cleanup
        t.team_size = None
        t.save()
        r1.is_team_round = False
        r1.save()
        r3.is_team_round = False
        r3.save()

    def test_tournament_team_rounds_none(self):
        t = Tournament.objects.get(name='t1')
        rds = t.team_rounds()
        self.assertEqual(len(rds), 0)

    # Tournament.team_rounds_finished()
    def test_tournament_team_rounds_finished_all_done(self):
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save()
        r1 = t.round_numbered(1)
        self.assertFalse(r1.is_finished)
        r1.is_finished = True
        r1.is_team_round = True
        r1.save()
        r3 = t.round_numbered(3)
        self.assertTrue(r3.is_finished)
        r3.is_team_round = True
        r3.save()
        rds = t.team_rounds()
        self.assertTrue(t.team_rounds_finished())
        # Cleanup
        t.team_size = None
        t.save()
        r1.is_team_round = False
        r1.is_finished = False
        r1.save()
        r3.is_team_round = False
        r3.save()

    def test_tournament_team_rounds_finished_some_done(self):
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save()
        r1 = t.round_numbered(1)
        self.assertFalse(r1.is_finished)
        r1.is_team_round = True
        r1.save()
        r3 = t.round_numbered(3)
        self.assertTrue(r3.is_finished)
        r3.is_team_round = True
        r3.save()
        rds = t.team_rounds()
        self.assertFalse(t.team_rounds_finished())
        # Cleanup
        t.team_size = None
        t.save()
        r1.is_team_round = False
        r1.save()
        r3.is_team_round = False
        r3.save()

    def test_tournament_team_rounds_finished_none_done(self):
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save()
        r1 = t.round_numbered(1)
        self.assertFalse(r1.is_finished)
        r1.is_team_round = True
        r1.save()
        r3 = t.round_numbered(3)
        self.assertTrue(r3.is_finished)
        r3.is_finished = False
        r3.is_team_round = True
        r3.save()
        rds = t.team_rounds()
        self.assertFalse(t.team_rounds_finished())
        # Cleanup
        t.team_size = None
        t.save()
        r1.is_team_round = False
        r1.save()
        r3.is_team_round = False
        r3.is_finished = True
        r3.save()

    def test_tournament_team_rounds_finished_none(self):
        """team_round_finished() in non-team tournament"""
        t = Tournament.objects.get(name='t1')
        self.assertTrue(t.team_rounds_finished())

    # Tournament.best_countries()
    def validate_best_countries_by_score(self, value):
        """Check dict returned by best_countries()"""
        # Result should be a dict, keyed by GreatPower, of lists of GamePlayers
        self.assertEqual(len(value), 7)
        for power in GreatPower.objects.all():
            with self.subTest(power=power):
                best_gps = value[power].pop(0)
                best_score = best_gps[0].score
                for gp in best_gps:
                    self.assertEqual(best_score, gp.score)
                for gps in value[power]:
                    if len(gps) == 1:
                        if not gps[0].tournamentplayer().unranked:
                            self.assertTrue(best_score >= gps[0].score)
                    else:
                        score = gps[0].score
                        self.assertTrue(best_score >= score)
                        for gp in gps:
                            if not gp.tournamentplayer().unranked:
                                self.assertEqual(score, gp.score)

    def test_tournament_best_countries_with_games(self):
        # TODO modify GamePlayer scores so they're not all zero
        t = Tournament.objects.get(name='t1')
        bc = t.best_countries(whole_list=True)
        self.validate_best_countries_by_score(bc)

    def test_tournament_best_countries_without_games(self):
        t = Tournament.objects.get(name='t3')
        self.assertEqual({}, t.best_countries())

    def test_tournament_best_countries_without_powers(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        # Remember the power assignments for g11, and unset them all
        powers = {}
        for gp in g.gameplayer_set.all():
            powers[gp.player] = gp.power
            gp.power = None
            gp.save(update_fields=['power'])
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        bc = t.best_countries(whole_list=True)
        self.validate_best_countries_by_score(bc)
        # Restore power assignments
        for gp in g.gameplayer_set.all():
            gp.power = powers[gp.player]
            gp.save(update_fields=['power'])

    def test_tournament_best_countries_with_unranked(self):
        t = Tournament.objects.get(name='t1')
        bc = t.best_countries()
        # The German solo should not be included
        for gp in bc[self.germany]:
            with self.subTest(power=gp.power):
                self.assertFalse(gp.player == self.p5)

    def test_best_countries_after_round(self):
        t = Tournament.objects.get(name='t1')
        bc = t.best_countries(after_round_num=1)
        # All the best countries should come from g12 except when a player is unranked
        for power in GreatPower.objects.all():
            with self.subTest(power=power):
                best = bc[power]
                # We only asked for the best, not the full ranking
                self.assertEqual(len(best), 1)
                gp = best[0]
                self.assertFalse(gp.tournamentplayer().unranked)
                if power == self.france:
                    self.assertEqual(gp.game.name, 'g11')
                else:
                    self.assertEqual(gp.game.name, 'g12')

    def _rank_of(self, gp, in_lists):
        """Find the list in in_lists that contains the gp and return its index"""
        for n, l in enumerate(in_lists):
            if gp in l:
                return n
        raise IndexError

    def test_tournament_best_countries_by_dots(self):
        t = Tournament.objects.get(name='t1')
        g12 = Game.objects.get(name='g12')
        g14 = Game.objects.get(name='g14')
        # Check that we only have the "1900" CentreCounts for the Games we're using
        self.assertEqual(g12.centrecount_set.count(), 7)
        self.assertEqual(g14.centrecount_set.count(), 7)
        # Switch game scoring system to sum of squares for both games
        round_scoring1 = g12.the_round.scoring_system
        g12.the_round.scoring_system = 'Sum of Squares'
        g12.the_round.save(update_fields=['scoring_system'])
        round_scoring2 = g14.the_round.scoring_system
        g14.the_round.scoring_system = 'Sum of Squares'
        g14.the_round.save(update_fields=['scoring_system'])
        # Ensure all players are ranked
        gp_list = list(t.tournamentplayer_set.filter(unranked=True))
        for gp in gp_list:
            gp.unranked = False
            gp.save(update_fields=['unranked'])
        # Add some CentreCounts to two Games
        # to give higher score with lower dot count and vice versa
        CentreCount.objects.create(power=self.austria, game=g12, year=1905, count=9)
        CentreCount.objects.create(power=self.england, game=g12, year=1905, count=9)
        CentreCount.objects.create(power=self.france, game=g12, year=1905, count=9)
        CentreCount.objects.create(power=self.germany, game=g12, year=1905, count=7)
        CentreCount.objects.create(power=self.italy, game=g12, year=1905, count=0)
        CentreCount.objects.create(power=self.russia, game=g12, year=1905, count=0)
        CentreCount.objects.create(power=self.turkey, game=g12, year=1905, count=0)
        CentreCount.objects.create(power=self.austria, game=g14, year=1905, count=8)
        CentreCount.objects.create(power=self.england, game=g14, year=1905, count=5)
        CentreCount.objects.create(power=self.france, game=g14, year=1905, count=4)
        CentreCount.objects.create(power=self.germany, game=g14, year=1905, count=4)
        CentreCount.objects.create(power=self.italy, game=g14, year=1905, count=5)
        CentreCount.objects.create(power=self.russia, game=g14, year=1905, count=3)
        CentreCount.objects.create(power=self.turkey, game=g14, year=1905, count=5)
        # calculate scores for both Games
        g12.update_scores(update_round=False)
        g14.update_scores(update_round=False)
        # Check best countries with criterion of score
        bc = t.best_countries(whole_list=True)
        for power in GreatPower.objects.all():
            with self.subTest(criterion=BestCountryCriteria.SCORE, power=power):
                gp1 = g12.gameplayer_set.get(power=power)
                gp2 = g14.gameplayer_set.get(power=power)
                if gp1.score > gp2.score:
                    self.assertTrue(self._rank_of(gp1, bc[power]) < self._rank_of(gp2, bc[power]))
                if gp1.score < gp2.score:
                    self.assertTrue(self._rank_of(gp1, bc[power]) > self._rank_of(gp2, bc[power]))
        # Change the Tournament to rank best countries by dot count
        t.best_country_criterion = BestCountryCriteria.DOTS
        t.save(update_fields=['best_country_criterion'])
        # Now best countries should be different
        bc = t.best_countries(whole_list=True)
        for power in GreatPower.objects.all():
            with self.subTest(criterion=BestCountryCriteria.DOTS, power=power):
                gp1 = g12.gameplayer_set.get(power=power)
                gp2 = g14.gameplayer_set.get(power=power)
                if gp1.final_sc_count() > gp2.final_sc_count():
                    self.assertTrue(self._rank_of(gp1, bc[power]) < self._rank_of(gp2, bc[power]))
                if gp1.final_sc_count() < gp2.final_sc_count():
                    self.assertTrue(self._rank_of(gp1, bc[power]) > self._rank_of(gp2, bc[power]))
        # Clean up
        t.best_country_criterion = BestCountryCriteria.SCORE
        t.save(update_fields=['best_country_criterion'])
        for gp in gp_list:
            gp.unranked = True
            gp.save(update_fields=['unranked'])
        g12.the_round.scoring_system = round_scoring1
        g12.the_round.save(update_fields=['scoring_system'])
        g14.the_round.scoring_system = round_scoring2
        g14.the_round.save(update_fields=['scoring_system'])
        g12.centrecount_set.filter(year=1905).delete()
        g14.centrecount_set.filter(year=1905).delete()

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

    def test_tournament_background_series(self):
        s = Series(name="Test Series", description="Text")
        s.save()
        t1 = Tournament.objects.get(name='t1')
        t3 = Tournament.objects.get(name='t3')
        s.tournaments.add(t1)
        s.tournaments.add(t3)
        t1.background()
        # Clean up
        s.delete()

    # Tournament.game_set()
    def test_tournament_game_set(self):
        t = Tournament.objects.get(name='t3')
        self.assertEqual(t.game_set().count(), 2)

    # Tournament.current_round()
    def test_tournament_current_round_none(self):
        # All games in t3 are finished
        t = Tournament.objects.get(name='t3')
        self.assertIsNone(t.current_round())

    def test_tournament_current_round(self):
        t = Tournament.objects.get(name='t1')
        r = t.current_round()
        rounds = t.round_set.count()
        # All earlier rounds should be finished or in progress
        for i in range(1, r.number()):
            with self.subTest(round_number=i):
                self.assertTrue(t.round_numbered(i).is_finished or t.round_numbered(i).in_progress(),
                                'round %d' % i)
        # All later rounds should be not in progress
        for i in range(r.number() + 1, rounds + 1):
            with self.subTest(round_number=i):
                self.assertFalse(t.round_numbered(i).in_progress(), 'round %d' % i)
        # This round should be unfinished
        self.assertFalse(r.is_finished)

    # Tournament.set_is_finished()
    def test_tourney_set_is_finished_some_rounds_over(self):
        t = Tournament.objects.get(name='t1')
        t.set_is_finished()
        self.assertFalse(t.is_finished)

    def test_tourney_set_is_finished_no_rounds_over(self):
        t = Tournament.objects.get(name='t2')
        t.set_is_finished()
        self.assertFalse(t.is_finished)

    def test_tourney_set_is_finished_all_rounds_over(self):
        t = Tournament.objects.get(name='t3')
        t.set_is_finished()
        self.assertTrue(t.is_finished)

    def test_tourney_set_is_finished_no_rounds(self):
        today = date.today()
        t = Tournament.objects.create(name='Roundless',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name)
        t.set_is_finished()
        self.assertFalse(t.is_finished)

    # Tournament.in_progress()
    def test_tourney_in_progress_some_rounds_over(self):
        t = Tournament.objects.get(name='t1')
        self.assertTrue(t.in_progress())

    def test_tourney_in_progress_no_rounds_over(self):
        t = Tournament.objects.get(name='t2')
        self.assertTrue(t.in_progress())

    def test_tourney_in_progress_all_rounds_over(self):
        t = Tournament.objects.get(name='t3')
        self.assertFalse(t.in_progress())

    def test_tourney_in_progress_no_rounds(self):
        today = date.today()
        t = Tournament.objects.create(name='Roundless',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name)
        self.assertFalse(t.in_progress())

    def test_tourney_in_progress_rounds_not_started(self):
        today = date.today()
        t = Tournament.objects.create(name='Preparing',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name)
        t.save()
        r = Round.objects.create(tournament=t,
                                 scoring_system=s1,
                                 dias=True,
                                 start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r.save()
        self.assertFalse(t.in_progress())
        # Clean-up
        t.delete()

    # Tournament.wdd_url()
    def test_tournament_wdd_url(self):
        t = Tournament.objects.get(name='t3')
        t.wdd_tournament_id = 7
        self.assertTrue(t.wdd_url().endswith('?id_tournament=7'))

    def test_tournament_wdd_url_none(self):
        t = Tournament.objects.get(name='t3')
        self.assertEqual('', t.wdd_url())

    # Tournament.wdr_url()
    def test_tournament_wdr_url(self):
        t = Tournament.objects.get(name='t3')
        t.wdr_tournament_id = 7
        self.assertTrue(t.wdr_url().endswith('tournaments/7'))

    def test_tournament_wdr_url_none(self):
        t = Tournament.objects.get(name='t3')
        self.assertEqual('', t.wdr_url())

    # Tournament.get_absolute_url()
    def test_tournament_get_absolute_url(self):
        t = Tournament.objects.get(name='t3')
        t.get_absolute_url()

    # Tournament.clean()
    def test_tournament_clean_sum_1(self):
        today = date.today()
        t = Tournament(name='Test tournament',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system="None",
                       tournament_scoring_system="Sum best 2 rounds",
                       draw_secrecy=DrawSecrecy.SECRET)
        self.assertRaises(ValidationError, t.clean)

    def test_tournament_clean_sum_2(self):
        today = date.today()
        t = Tournament(name='Test tournament',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system="Add all game scores",
                       tournament_scoring_system="Sum best 2 rounds",
                       draw_secrecy=DrawSecrecy.SECRET)
        t.clean()

    def test_tournament_clean_sum_games_1(self):
        today = date.today()
        t = Tournament(name='Test tournament',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system="None",
                       tournament_scoring_system="Best single game result",
                       draw_secrecy=DrawSecrecy.SECRET)
        t.clean()

    def test_tournament_clean_sum_games_2(self):
        today = date.today()
        t = Tournament(name='Test tournament',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system="Best game counts",
                       tournament_scoring_system="Best single game result",
                       draw_secrecy=DrawSecrecy.SECRET)
        self.assertRaises(ValidationError, t.clean)

    # Tournament.save()
    # On save(), all round scores and the tournament score should be recalculated
    def test_tournament_save(self):
        t = Tournament.objects.get(name='t1')
        # Remember the current scores
        scores = {}
        for tp in t.tournamentplayer_set.all():
            for rp in tp.roundplayers():
                scores[rp] = rp.score
            scores[tp] = tp.score
        # save() should recalculate all RoundPlayer and TournamentPlayer scores
        t.save()
        # Verify and cleanup
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                self.assertNotAlmostEqual(tp.score, scores[tp])
                tp.score = scores[tp]
                tp.save()
                for rp in tp.roundplayers():
                    with self.subTest(player=rp.player, round_num=rp.the_round.number()):
                        self.assertNotAlmostEqual(rp.score, scores[rp])
                        rp.score = scores[rp]
                        rp.save()


@override_settings(HOSTNAME='example.com')
class TournamentPlayerTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       is_finished=True,
                                       draw_secrecy=DrawSecrecy.COUNTS)
        Tournament.objects.create(name='t4',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       power_assignment=PowerAssignMethods.PREFERENCES)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=8, tzinfo=timezone.utc)))
        r12 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=r11.start + HOURS_8)
        Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=r11.start + HOURS_16)
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=r11.start + HOURS_24)
        # Add Rounds to t3
        r31 = Round.objects.create(tournament=t3,
                                   scoring_system=s1,
                                   dias=True,
                                   is_finished=True,
                                   start=datetime.combine(t3.start_date, time(hour=8, tzinfo=timezone.utc)),
                                   final_year=1907)
        cls.r32 = Round.objects.create(tournament=t3,
                                       scoring_system=s1,
                                       dias=True,
                                       is_finished=True,
                                       start=r31.start + HOURS_8,
                                       earliest_end_time=r31.start + HOURS_8,
                                       latest_end_time=r31.start + HOURS_9)

        # Add finished Games to r31
        Game.objects.create(name='g311',
                            started_at=r31.start,
                            the_round=r31,
                            is_finished=True,
                            the_set=cls.set1)
        Game.objects.create(name='g312',
                            started_at=r31.start,
                            the_round=r31,
                            is_finished=True,
                            the_set=cls.set1)
        # Add Games to r32
        Game.objects.create(name='g32',
                            started_at=cls.r32.start,
                            the_round=cls.r32,
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

        # And RoundPlayers
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
        TournamentPlayer.objects.create(player=cls.p2, tournament=t1, backstabbr_username='nobody')
        TournamentPlayer.objects.create(player=cls.p3, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p5, tournament=t1, unranked=True)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t1, location='The Moon')
        TournamentPlayer.objects.create(player=cls.p8, tournament=t1)

        # Add TournamentPlayers to t3
        TournamentPlayer.objects.create(player=cls.p5, tournament=t3, score=147.3)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t3, score=47.3)
        # Add RoundPlayers to r31
        RoundPlayer.objects.create(player=cls.p5, the_round=r31, score=0.0)
        RoundPlayer.objects.create(player=cls.p7, the_round=r31, score=0.0)
        # Add RoundPlayers to r32
        RoundPlayer.objects.create(player=cls.p5, the_round=cls.r32, score=47.3)
        RoundPlayer.objects.create(player=cls.p7, the_round=cls.r32, score=47.3)

    # TournamentPlayer.score_is_final()
    def test_tournamentplayer_score_is_final_afterwards(self):
        t = Tournament.objects.get(name='t3')
        self.assertTrue(t.is_finished)
        tp = t.tournamentplayer_set.first()
        self.assertTrue(tp.score_is_final())

    def test_tournamentplayer_score_is_final_before_last_round(self):
        # TODO More round(s) to go
        pass

    def test_tournamentplayer_score_is_final_not_playing_last_round(self):
        # TODO Final round in progress, but this person isn't playing in it
        pass

    def test_tournamentplayer_score_is_final_playing_last_round(self):
        # TODO Final round in progress, and this person is playing in it
        pass

    def test_tournamentplayer_score_is_final_handicap_not_finished(self):
        # TODO Check that a TP whose score would otherwise be final is not
        # if there's a handicap and any game is still ongoing
        pass

    def test_tournamentplayer_score_is_final_sum_games(self):
        # TODO Tournament using TScoringSumGames scoring system
        pass

    # TournamentPlayer.score_to_show()
    def test_tournamentplayer_score_to_show_finished(self):
        """score_to_show() with finished tournament"""
        t = Tournament.objects.get(name='t3')
        self.assertTrue(t.is_finished)
        self.assertTrue(t.show_current_scores)
        t.show_current_scores = False
        t.save()
        tp = t.tournamentplayer_set.get(player=self.p5)
        score = tp.score_to_show()
        # TODO set scores so we can tell that we got the right one
        self.assertEqual(score, tp.score)
        # Cleanup
        t.show_current_scores = True
        t.save()

    def test_tournamentplayer_score_to_show_current(self):
        """score_to_show() with tournament.show_current_scores True"""
        t = Tournament.objects.get(name='t3')
        self.assertTrue(t.is_finished)
        self.assertTrue(t.show_current_scores)
        t.is_finished = False
        t.save()
        tp = t.tournamentplayer_set.get(player=self.p5)
        score = tp.score_to_show()
        # TODO set scores so we can tell that we got the right one
        self.assertEqual(score, tp.score)
        # Cleanup
        t.is_finished = True
        t.save()

    def test_tournamentplayer_score_to_show_last_round(self):
        """score_to_show() with ongoing Tournament, show_current_scores False"""
        t = Tournament.objects.get(name='t3')
        self.assertTrue(t.is_finished)
        self.assertTrue(t.show_current_scores)
        t.is_finished = False
        t.show_current_scores = False
        t.save()
        tp = t.tournamentplayer_set.get(player=self.p5)
        score = tp.score_to_show()
        rp = tp.roundplayers().filter(the_round__is_finished=True).last()
        # TODO set scores so we can tell that we got the right one
        self.assertEqual(score, rp.tournament_score)
        # Cleanup
        t.is_finished = True
        t.show_current_scores = True
        t.save()

    # TODO In an ongoing Tournament with show_current_scores False, if there are no finished rounds,
    #       it should return zero

    # TournamentPlayer.position()
    def test_tournamentplayer_position_finished(self):
        t = Tournament.objects.get(name='t3')
        tp1 = t.tournamentplayer_set.get(player=self.p5)
        self.assertEqual(tp1.score, 147.3)
        tp2 = t.tournamentplayer_set.get(player=self.p7)
        self.assertEqual(tp2.score, 47.3)
        self.assertEqual(tp1.position(), 1)
        self.assertEqual(tp2.position(), 2)

    # TournamentPlayer.roundplayers()
    def test_tournamentplayer_roundplayers(self):
        t = Tournament.objects.get(name='t3')
        tp = t.tournamentplayer_set.first()
        rps = tp.roundplayers()
        self.assertEqual(rps.count(), 2)

    # TournamentPlayer.gameplayers()
    def test_tournamentplayer_roundplayers(self):
        t = Tournament.objects.get(name='t3')
        tp = t.tournamentplayer_set.first()
        # Add GamePlayers
        gp = GamePlayer.objects.create(player=tp.player,
                                       game=t.round_numbered(1).game_set.first())
        gps = tp.gameplayers()
        self.assertEqual(gps.count(), 1)
        # Cleanup
        gp.delete()

    # TournamentPlayer.rounds_played()
    def test_tournamentplayer_rounds_played_none(self):
        t = Tournament.objects.get(name='t3')
        tp = t.tournamentplayer_set.first()
        rounds = tp.rounds_played()
        self.assertEqual(rounds, 0)

    def test_tournamentplayer_rounds_played_multiple_games_per_round(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_numbered(1)
        g1 = r.game_set.first()
        g2 = r.game_set.last()
        self.assertNotEqual(g1, g2)
        tp = t.tournamentplayer_set.first()
        gp1 = GamePlayer.objects.create(player=tp.player,
                                        game=g1)
        gp2 = GamePlayer.objects.create(player=tp.player,
                                        game=g2)
        rounds = tp.rounds_played()
        self.assertEqual(rounds, 1)
        # Cleanup
        gp1.delete()
        gp2.delete()

    def test_tournamentplayer_rounds_played_normal(self):
        t = Tournament.objects.get(name='t3')
        g1 = Game.objects.last()
        self.assertEqual(g1.the_round.tournament, t)
        tp = t.tournamentplayer_set.first()
        gp1 = GamePlayer.objects.create(player=tp.player,
                                        game=g1)
        rounds = tp.rounds_played()
        self.assertEqual(rounds, 1)
        # Cleanup
        gp1.delete()

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
        for i, power in enumerate([self.austria,
                                   self.england,
                                   self.france,
                                   self.germany,
                                   self.italy], 1):
            with self.subTest(power=power):
                pref = prefs.pop(0)
                self.assertEqual(pref.ranking, i)
                self.assertEqual(pref.power, power)
        self.assertEqual(tp.prefs_string(), 'AEFGI')
        tp.preference_set.all().delete()

    def test_tp_create_preferences_from_string_lowercase(self):
        tp = TournamentPlayer.objects.first()
        self.assertEqual(tp.preference_set.count(), 0)
        tp.create_preferences_from_string('triafge')
        self.assertEqual(tp.preference_set.count(), 7)
        # Check that the Preferences are correct
        prefs = list(tp.preference_set.all())
        for i, power in enumerate([self.turkey,
                                   self.russia,
                                   self.italy,
                                   self.austria,
                                   self.france,
                                   self.germany,
                                   self.england], 1):
            with self.subTest(power=power):
                pref = prefs.pop(0)
                self.assertEqual(pref.ranking, i)
                self.assertEqual(pref.power, power)
        self.assertEqual(tp.prefs_string(), 'TRIAFGE')
        tp.preference_set.all().delete()

    def test_tp_create_preferences_from_string_uppercase(self):
        tp = TournamentPlayer.objects.first()
        self.assertEqual(tp.preference_set.count(), 0)
        tp.create_preferences_from_string('TRIAFGE')
        self.assertEqual(tp.preference_set.count(), 7)
        # Check that the Preferences are correct
        prefs = list(tp.preference_set.all())
        for i, power in enumerate([self.turkey,
                                   self.russia,
                                   self.italy,
                                   self.austria,
                                   self.france,
                                   self.germany,
                                   self.england], 1):
            with self.subTest(power=power):
                pref = prefs.pop(0)
                self.assertEqual(pref.ranking, i)
                self.assertEqual(pref.power, power)
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
        t = tp.tournament
        old_pa = t.power_assignment
        t.power_assignment = PowerAssignMethods.PREFERENCES
        t.save(update_fields=['power_assignment'])
        tp._generate_uuid()
        self.assertIn('https://', tp.get_prefs_url())
        # Clean up
        t.power_assignment = old_pa
        t.save(update_fields=['power_assignment'])

    def test_tp_get_prefs_url_no_uuid(self):
        # A TournamentPlayer without a uuid_str
        tp = TournamentPlayer.objects.filter(uuid_str='').first()
        t = tp.tournament
        old_pa = t.power_assignment
        t.power_assignment = PowerAssignMethods.PREFERENCES
        t.save(update_fields=['power_assignment'])
        self.assertIn('https://', tp.get_prefs_url())
        # Clean up
        t.power_assignment = old_pa
        t.save(update_fields=['power_assignment'])

    def test_tp_get_prefs_url_wrong_tournament(self):
        # A Tournament where powers are not assigned by preferences
        tp = TournamentPlayer.objects.filter(uuid_str='').first()
        self.assertNotEqual(tp.tournament.power_assignment,
                            PowerAssignMethods.PREFERENCES)
        self.assertRaises(InvalidPowerAssignmentMethod, tp.get_prefs_url)

    # TODO TournamentPlayer.send_prefs_email()

    # TournamentPlayer.get_absolute_url()
    def test_tournamentplayer_get_absolute_url(self):
        tp = TournamentPlayer.objects.first()
        tp.get_absolute_url()

    # TournamentPlayer.__str__()
    def test_tournamentplayer_str(self):
        tp = TournamentPlayer.objects.first()
        # TODO Validate result
        str(tp)

    # TournamentPlayer.save()
    def test_new_tp_set_uuid(self):
        # New TournamentPlayer for Player with email in Tournament with prefs should get uuid_str set
        self.assertEqual(len(self.p1.email), 0)
        self.p1.email = 'example@example.com'
        self.p1.save(update_fields=['email'])
        t = Tournament.objects.get(name='t4')
        self.assertEqual(t.powers_assigned_from_prefs(), True)
        tp = TournamentPlayer(tournament=t,
                              player=self.p1)
        tp.save()
        self.assertNotEqual(len(tp.uuid_str), 0)
        # Clean up
        tp.delete()
        self.p1.email = ''
        self.p1.save(update_fields=['email'])

    def test_new_tp_no_set_uuid(self):
        # New TournamentPlayer in Tournament without prefs should not get uuid_str,
        # even for Player with email
        self.assertEqual(len(self.p1.email), 0)
        self.p1.email = 'example@example.com'
        self.p1.save(update_fields=['email'])
        t = Tournament.objects.get(name='t3')
        self.assertEqual(t.powers_assigned_from_prefs(), False)
        tp = TournamentPlayer(tournament=t,
                              player=self.p1)
        tp.save()
        self.assertEqual(len(tp.uuid_str), 0)
        # Clean up
        tp.delete()
        self.p1.email = ''
        self.p1.save(update_fields=['email'])

    def test_new_tp_copy_bs_username(self):
        # New TournamentPlayer should get backstabbr_username copied over from Player
        t = Tournament.objects.get(name='t3')
        self.assertEqual(len(self.p1.backstabbr_username), 0)
        self.p1.backstabbr_username = 'My_username'
        self.p1.save(update_fields=['backstabbr_username'])
        tp = TournamentPlayer(tournament=t,
                              player=self.p1)
        tp.save()
        self.assertEqual(tp.backstabbr_username, self.p1.backstabbr_username)
        # Clean up
        tp.delete()
        self.p1.backstabbr_username = ''
        self.p1.save(update_fields=['backstabbr_username'])

    def test_new_tp_override_bs_username(self):
        # Can specify different backstabbr_username for new TP
        # and Player will be updated
        t = Tournament.objects.get(name='t3')
        self.assertEqual(len(self.p1.backstabbr_username), 0)
        self.p1.backstabbr_username = 'My_username'
        self.p1.save(update_fields=['backstabbr_username'])
        new_username = 'Different'
        tp = TournamentPlayer(tournament=t,
                              player=self.p1,
                              backstabbr_username=new_username)
        tp.save()
        self.assertEqual(tp.backstabbr_username, new_username)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.backstabbr_username, new_username)
        # Clean up
        tp.delete()
        self.p1.backstabbr_username = ''
        self.p1.save(update_fields=['backstabbr_username'])

    def test_save_tp_leave_bs_username(self):
        # Existing TournamentPlayer should not get backstabbr_username changed
        t = Tournament.objects.get(name='t1')
        tp = t.tournamentplayer_set.get(player=self.p3)
        self.assertEqual(len(self.p3.backstabbr_username), 0)
        self.assertEqual(len(tp.backstabbr_username), 0)
        # Add a backstabbr_username to the Player
        self.p3.backstabbr_username = 'My_username'
        self.p3.save(update_fields=['backstabbr_username'])
        # Save the TournamentPlayer
        tp.save()
        # TournamentPlayer backstabbr_username should remain the same
        self.assertEqual(len(tp.backstabbr_username), 0)
        # Clean up
        self.p3.backstabbr_username = ''
        self.p3.save(update_fields=['backstabbr_username'])

    # TODO New TournamentPlayer should be unranked if they're a manager
    # TODO New TournamentPlayer should not be unranked if they're not a manager
    # TODO Background objects should be generated for new TournamentPlayer
    # TODO Background objects should not be generated for existing TournamentPlayer
    # TODO Existing TournamentPlayer should not have unranked cleared when saved
    # TODO Existing TournamentPlayer should not have unranked set when saved


class SeederBiasTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.COUNTS)

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

        # And TournamentPlayers
        TournamentPlayer.objects.create(player=cls.p1, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p2, tournament=t1, backstabbr_username='nobody')
        TournamentPlayer.objects.create(player=cls.p3, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p5, tournament=t1, unranked=True)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t1, location='The Moon')
        TournamentPlayer.objects.create(player=cls.p8, tournament=t1)

        # Add TournamentPlayers to t3
        TournamentPlayer.objects.create(player=cls.p5, tournament=t3, score=147.3)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t3, score=47.3)

    # SeederBias.clean()
    def test_seederbias_clean_mixup(self):
        '''Two players from different tournaments'''
        t = Tournament.objects.get(name='t1')
        tp1 = t.tournamentplayer_set.first()
        t = Tournament.objects.get(name='t3')
        tp2 = t.tournamentplayer_set.first()
        sb = SeederBias(player1=tp1,
                        player2=tp2)
        self.assertRaises(ValidationError, sb.clean)

    def test_seederbias_clean_ok(self):
        t = Tournament.objects.get(name='t1')
        tp1 = t.tournamentplayer_set.first()
        tp2 = t.tournamentplayer_set.last()
        sb = SeederBias(player1=tp1,
                        player2=tp2)
        sb.clean()

    # SeederBias.__str__()
    def test_seederbias_str(self):
        t = Tournament.objects.get(name='t1')
        tp1 = t.tournamentplayer_set.first()
        tp2 = t.tournamentplayer_set.last()
        sb = SeederBias(player1=tp1,
                        player2=tp2)
        # TODO Validate result
        str(sb)


class PreferenceTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)

        # Create a player
        # Avoid hitting the WDD by not providing a WDD id
        cls.p1 = Player.objects.create(first_name='Abbey', last_name='Brown')

        # And TournamentPlayer
        TournamentPlayer.objects.create(player=cls.p1, tournament=t1)

    # Preference._str__()
    def test_preference_str(self):
        tp = TournamentPlayer.objects.first()
        self.assertEqual(tp.preference_set.count(), 0)
        tp.create_preferences_from_string('TRIAFGE')
        p = Preference.objects.first()
        # TODO Validate result
        str(p)
        tp.preference_set.all().delete()


class RoundTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)
        t2 = Tournament.objects.create(name='t2',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       is_finished=True,
                                       draw_secrecy=DrawSecrecy.COUNTS)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1,
                                   scoring_system=s2,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=8, tzinfo=timezone.utc)))
        r12 = Round.objects.create(tournament=t1,
                                   scoring_system=s2,
                                   dias=True,
                                   start=r11.start + HOURS_8)
        r13 = Round.objects.create(tournament=t1,
                                   scoring_system=s2,
                                   dias=True,
                                   is_finished=True,
                                   start=r11.start + HOURS_16)
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=r11.start + HOURS_24)
        # Add Rounds to t2
        r21 = Round.objects.create(tournament=t2,
                                   scoring_system=s1,
                                   dias=False,
                                   start=datetime.combine(t2.start_date, time(hour=8, tzinfo=timezone.utc)))
        Round.objects.create(tournament=t2,
                                   scoring_system=s1,
                                   dias=False,
                                   start=r21.start + HOURS_8)
        # Add Rounds to t3
        r31 = Round.objects.create(tournament=t3,
                                   scoring_system=s1,
                                   dias=True,
                                   is_finished=True,
                                   start=datetime.combine(t3.start_date, time(hour=8, tzinfo=timezone.utc)),
                                   final_year=1907)
        cls.r32 = Round.objects.create(tournament=t3,
                                       scoring_system=s1,
                                       dias=True,
                                       is_finished=True,
                                       start=r31.start + HOURS_8,
                                       earliest_end_time=r31.start + HOURS_8,
                                       latest_end_time=r31.start + HOURS_9)

        # Add Games to r11
        cls.g11 = Game.objects.create(name='g11',
                                      started_at=r11.start,
                                      the_round=r11,
                                      the_set=cls.set1)
        cls.g12 = Game.objects.create(name='g12',
                                      started_at=r11.start,
                                      the_round=r11,
                                      the_set=cls.set1)
        # Add Games to r12
        cls.g13 = Game.objects.create(name='g13',
                                      started_at=r12.start,
                                      the_round=r12,
                                      is_finished=True,
                                      the_set=cls.set1)
        cls.g14 = Game.objects.create(name='g14',
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
        # Add Games to r31
        Game.objects.create(name='g31',
                            started_at=r31.start,
                            the_round=r31,
                            is_finished=True,
                            the_set=cls.set1)
        # Add Games to r32
        Game.objects.create(name='g32',
                            started_at=cls.r32.start,
                            the_round=cls.r32,
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
        # These two are deliberately not in any tournaments
        cls.p9 = Player.objects.create(first_name='Queenie', last_name='Radiation')
        cls.p10 = Player.objects.create(first_name='Sebastian', last_name='Twinkie')
        # The remainder are not used in this method but are available for use in tests
        cls.p11 = Player.objects.create(first_name='Ursula', last_name='Vampire')

        # And some corresponding GamePlayers
        GamePlayer.objects.create(player=cls.p2, game=cls.g11, score=3.0, power=cls.austria)
        GamePlayer.objects.create(player=cls.p3, game=cls.g11, score=3.0, power=cls.england)
        GamePlayer.objects.create(player=cls.p4, game=cls.g11, score=3.0, power=cls.france)
        GamePlayer.objects.create(player=cls.p5, game=cls.g11, score=3.0, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=cls.g11, score=3.0, power=cls.italy)
        GamePlayer.objects.create(player=cls.p7, game=cls.g11, score=3.0, power=cls.russia)
        GamePlayer.objects.create(player=cls.p8, game=cls.g11, score=3.0, power=cls.turkey)
        GamePlayer.objects.create(player=cls.p2, game=cls.g12, score=3.0, power=cls.austria)
        GamePlayer.objects.create(player=cls.p3, game=cls.g12, score=3.0, power=cls.england)
        GamePlayer.objects.create(player=cls.p4, game=cls.g12, score=3.0, power=cls.france)
        GamePlayer.objects.create(player=cls.p5, game=cls.g12, score=3.0, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=cls.g12, score=3.0, power=cls.italy)
        GamePlayer.objects.create(player=cls.p7, game=cls.g12, score=3.0, power=cls.russia)
        GamePlayer.objects.create(player=cls.p8, game=cls.g12, score=3.0, power=cls.turkey)
        GamePlayer.objects.create(player=cls.p2, game=cls.g13, score=3.0, power=cls.austria)
        GamePlayer.objects.create(player=cls.p3, game=cls.g13, score=3.0, power=cls.england)
        GamePlayer.objects.create(player=cls.p4, game=cls.g13, score=3.0, power=cls.france)
        GamePlayer.objects.create(player=cls.p5, game=cls.g13, score=3.0, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=cls.g13, score=3.0, power=cls.italy)
        GamePlayer.objects.create(player=cls.p7, game=cls.g13, score=3.0, power=cls.russia)
        GamePlayer.objects.create(player=cls.p8, game=cls.g13, score=3.0, power=cls.turkey)
        GamePlayer.objects.create(player=cls.p2, game=cls.g14, score=3.0, power=cls.austria)
        GamePlayer.objects.create(player=cls.p3, game=cls.g14, score=3.0, power=cls.england)
        GamePlayer.objects.create(player=cls.p4, game=cls.g14, score=3.0, power=cls.france)
        GamePlayer.objects.create(player=cls.p5, game=cls.g14, score=3.0, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=cls.g14, score=3.0, power=cls.italy)
        GamePlayer.objects.create(player=cls.p7, game=cls.g14, score=3.0, power=cls.russia)
        GamePlayer.objects.create(player=cls.p8, game=cls.g14, score=3.0, power=cls.turkey)
        # And the corresponding RoundPlayers
        RoundPlayer.objects.create(player=cls.p1, the_round=r11, score=30.0)
        RoundPlayer.objects.create(player=cls.p2, the_round=r11, score=30.0)
        RoundPlayer.objects.create(player=cls.p3, the_round=r11, score=30.0)
        RoundPlayer.objects.create(player=cls.p4, the_round=r11, score=30.0)
        RoundPlayer.objects.create(player=cls.p5, the_round=r11, score=30.0)
        RoundPlayer.objects.create(player=cls.p6, the_round=r11, score=30.0)
        RoundPlayer.objects.create(player=cls.p7, the_round=r11, score=30.0)
        RoundPlayer.objects.create(player=cls.p8, the_round=r11, score=30.0)
        RoundPlayer.objects.create(player=cls.p1, the_round=r12, score=30.0)
        RoundPlayer.objects.create(player=cls.p2, the_round=r12, score=30.0)
        RoundPlayer.objects.create(player=cls.p3, the_round=r12, score=30.0)
        RoundPlayer.objects.create(player=cls.p4, the_round=r12, score=30.0)
        RoundPlayer.objects.create(player=cls.p5, the_round=r12, score=30.0)
        RoundPlayer.objects.create(player=cls.p6, the_round=r12, score=30.0)
        RoundPlayer.objects.create(player=cls.p7, the_round=r12, score=30.0)
        RoundPlayer.objects.create(player=cls.p8, the_round=r12, score=30.0)
        RoundPlayer.objects.create(player=cls.p4, the_round=r13, score=30.0)
        # And TournamentPlayers
        TournamentPlayer.objects.create(player=cls.p1, tournament=t1, score=300.0)
        TournamentPlayer.objects.create(player=cls.p2, tournament=t1, score=300.0, backstabbr_username='nobody')
        TournamentPlayer.objects.create(player=cls.p3, tournament=t1, score=300.0)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t1, score=300.0)
        TournamentPlayer.objects.create(player=cls.p5, tournament=t1, score=300.0, unranked=True)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t1, score=300.0)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t1, score=300.0, location='The Moon')
        TournamentPlayer.objects.create(player=cls.p8, tournament=t1, score=300.0)

        # Add TournamentPlayers to t3
        TournamentPlayer.objects.create(player=cls.p5, tournament=t3, score=147.3)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t3, score=47.3)
        # Add RoundPlayers to r31
        RoundPlayer.objects.create(player=cls.p5, the_round=r31, score=0.0)
        RoundPlayer.objects.create(player=cls.p7, the_round=r31, score=0.0)
        # Add RoundPlayers to r32
        RoundPlayer.objects.create(player=cls.p5, the_round=cls.r32, score=47.3)
        RoundPlayer.objects.create(player=cls.p7, the_round=cls.r32, score=47.3)

    # Round uniqueness
    def test_two_rounds_same_start(self):
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        today = date.today()
        t = Tournament.objects.create(name='Round Scoring Test',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      non_player_round_score=4005,
                                      non_player_round_score_once=True,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        # Check that we got the right scoring system
        self.assertIn("Best", t.round_scoring_system)
        # Two Rounds
        r = Round.objects.create(tournament=t,
                                 scoring_system=s,
                                 dias=False,
                                 start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        self.assertRaises(IntegrityError,
                          Round.objects.create,
                          tournament=t,
                          scoring_system=s,
                          dias=False,
                          start=r.start)
        # Clean up
        # For some reason, this gives an error
        #t.delete()

    # Round.scores()
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
        r.scores()

    def test_round_scores_with_unplayed(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # Add a RoundPlayer who didn't play
        rp = RoundPlayer(player=self.p9, the_round=r)
        rp.save()
        self.assertIn(self.p9, r.scores())
        rp.delete()

    # Round.update_scores()
    def test_round_update_scores_invalid(self):
        today = date.today()
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=today,
                                                      end_date=today + HOURS_24,
                                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                      round_scoring_system='Invalid System')
        r = Round.objects.create(tournament=t,
                                 scoring_system=G_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        self.assertRaises(InvalidScoringSystem, r.update_scores)

    def test_round_update_scores(self):
        today = date.today()
        t = Tournament(name='t5',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=DrawSecrecy.SECRET)
        t.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p1)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p2)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p3)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p4)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p5)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p6)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p7)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p8)
        tp.save()
        # We need a round with a finished game
        r = Round(tournament=t,
                  scoring_system='Sum of Squares',
                  dias=True,
                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r.save()
        rp = RoundPlayer(the_round=r, player=self.p1, score=40.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p2, score=35.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p3, score=30.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p4, score=25.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p5, score=20.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p6, score=15.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p7, score=10.0)
        rp.save()
        # One RoundPlayer who didn't play
        rp = RoundPlayer(the_round=r, player=self.p8, score=5.0)
        rp.save()
        g = Game(name='newgame1',
                 started_at=r.start,
                 the_round=r,
                 is_finished=True,
                 the_set=self.set1)
        g.save()
        gp = GamePlayer(game=g, player=self.p1, power=self.austria, score=1)
        gp.save()
        gp = GamePlayer(game=g, player=self.p2, power=self.england, score=2)
        gp.save()
        gp = GamePlayer(game=g, player=self.p3, power=self.france, score=3)
        gp.save()
        gp = GamePlayer(game=g, player=self.p4, power=self.germany, score=4)
        gp.save()
        gp = GamePlayer(game=g, player=self.p5, power=self.italy, score=5)
        gp.save()
        gp = GamePlayer(game=g, player=self.p6, power=self.russia, score=6)
        gp.save()
        gp = GamePlayer(game=g, player=self.p7, power=self.turkey, score=7)
        gp.save()
        r.update_scores()
        for rp in r.roundplayer_set.all():
            with self.subTest(player=rp.player):
                try:
                    gp = GamePlayer.objects.filter(game=g, player=rp.player).get()
                except GamePlayer.DoesNotExist:
                    self.assertEqual(rp.score, 0.0)
                else:
                    self.assertEqual(rp.score, gp.score)
        # Clean up
        t.delete()

    def test_round_update_scores_for_players(self):
        today = date.today()
        t = Tournament(name='t5',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=DrawSecrecy.SECRET)
        t.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p1)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p2)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p3)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p4)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p5)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p6)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p7)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p8)
        tp.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p9)
        tp.save()
        # We need a round with a finished game
        r = Round(tournament=t,
                  scoring_system='Sum of Squares',
                  dias=True,
                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r.save()
        rp = RoundPlayer(the_round=r, player=self.p1, score=40.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p2, score=35.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p3, score=30.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p4, score=25.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p5, score=20.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p6, score=15.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p7, score=10.0)
        rp.save()
        # Two RoundPlayers who didn't play
        rp = RoundPlayer(the_round=r, player=self.p8, score=5.0)
        rp.save()
        rp = RoundPlayer(the_round=r, player=self.p9, score=45.0)
        rp.save()
        # Which players to update - include some but not all who
        # played and some but not all who didn't
        player_list = [self.p2, self.p3, self.p9]
        # Remember the scores we set
        initial_scores = {}
        for rp in r.roundplayer_set.all():
            initial_scores[rp] = rp.score
        g = Game(name='newgame1',
                 started_at=r.start,
                 the_round=r,
                 is_finished=True,
                 the_set=self.set1)
        g.save()
        gp = GamePlayer(game=g, player=self.p1, power=self.austria, score=1)
        gp.save()
        gp = GamePlayer(game=g, player=self.p2, power=self.england, score=2)
        gp.save()
        gp = GamePlayer(game=g, player=self.p3, power=self.france, score=3)
        gp.save()
        gp = GamePlayer(game=g, player=self.p4, power=self.germany, score=4)
        gp.save()
        gp = GamePlayer(game=g, player=self.p5, power=self.italy, score=5)
        gp.save()
        gp = GamePlayer(game=g, player=self.p6, power=self.russia, score=6)
        gp.save()
        gp = GamePlayer(game=g, player=self.p7, power=self.turkey, score=7)
        gp.save()
        r.update_scores(player_list)
        for rp in r.roundplayer_set.all():
            with self.subTest(player=rp.player):
                if rp.player in player_list:
                    # Score should have been updated
                    try:
                        gp = GamePlayer.objects.filter(game=g, player=rp.player).get()
                    except GamePlayer.DoesNotExist:
                        self.assertEqual(rp.score, 0.0)
                    else:
                        self.assertEqual(rp.score, gp.score)
                else:
                    # Score should have been left as-is
                    self.assertEqual(initial_scores[rp], rp.score)
        # Clean up
        t.delete()

    # Round.set_is_finished()
    def test_round_set_is_finished_no_games_over(self):
        t = Tournament.objects.get(name='t1')
        r1 = t.round_numbered(1)
        r1.set_is_finished()
        self.assertFalse(r1.is_finished)

    def test_round_set_is_finished_some_games_over(self):
        t = Tournament.objects.get(name='t1')
        r2 = t.round_numbered(2)
        r2.set_is_finished()
        self.assertFalse(r2.is_finished)

    def test_round_set_is_finished_all_games_over(self):
        t = Tournament.objects.get(name='t1')
        r3 = t.round_numbered(3)
        r3.set_is_finished()
        self.assertTrue(r3.is_finished)

    def test_round_set_is_finished_no_games(self):
        """
        Rounds with no games can't have started, let alone finished
        """
        t = Tournament.objects.get(name='t1')
        r4 = t.round_numbered(4)
        r4.set_is_finished()
        self.assertFalse(r4.is_finished)

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

    # Round.show_scores()
    def test_round_show_scores_round_finished(self):
        """
        Return True if the Round is finished
        """
        t = Tournament.objects.get(name='t1')
        self.assertTrue(t.show_current_scores)
        t.show_current_scores = False
        t.save()
        r = t.round_numbered(3)
        self.assertTrue(r.is_finished)
        self.assertTrue(r.show_scores())
        # Cleanup
        t.show_current_scores = True
        t.save()

    def test_round_show_scores_show_current_scores(self):
        """
        Should return True if the Tournament has show_current_scores set
        """
        t = Tournament.objects.get(name='t1')
        self.assertTrue(t.show_current_scores)
        r = t.round_numbered(4)
        self.assertFalse(r.is_finished)
        self.assertTrue(r.show_scores())

    def test_round_show_scores_round_not_finished(self):
        """
        Return False otherwise
        """
        t = Tournament.objects.get(name='t1')
        self.assertTrue(t.show_current_scores)
        t.show_current_scores = False
        t.save()
        r = t.round_numbered(4)
        self.assertFalse(r.is_finished)
        self.assertFalse(r.show_scores())
        # Cleanup
        t.show_current_scores = True
        t.save()

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

    # Round.board_call_msg()
    def test_round_board_call_msg(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(3)
        for g in r.game_set.all():
            self.assertEqual(g.gameplayer_set.count(), 0)
            GamePlayer.objects.create(game=g,
                                      player=self.p1,
                                      power=self.austria)
            GamePlayer.objects.create(game=g,
                                      player=self.p2,
                                      power=self.england)
            GamePlayer.objects.create(game=g,
                                      player=self.p3,
                                      power=self.france)
            GamePlayer.objects.create(game=g,
                                      player=self.p4,
                                      power=self.germany)
            GamePlayer.objects.create(game=g,
                                      player=self.p5,
                                      power=self.italy)
            GamePlayer.objects.create(game=g,
                                      player=self.p6,
                                      power=self.russia)
            GamePlayer.objects.create(game=g,
                                      player=self.p7,
                                      power=self.turkey)
        msg = r.board_call_msg()
        # TODO Validate results
        # Cleanup
        for g in r.game_set.all():
            g.gameplayer_set.all().delete()

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
    def test_round_clean_team_round_wrong_tournament(self):
        t = Tournament.objects.get(name='t1')
        self.assertIsNone(t.team_size)
        r = t.round_set.first()
        r.is_team_round = True
        self.assertRaises(ValidationError, r.clean)

    def test_round_clean_team_round_ok(self):
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save()
        r = t.round_set.first()
        r.is_team_round = True
        r.clean()
        # Cleanup
        t.team_size = None
        t.save()

    # Round constraints (full_clean())
    def test_round_clean_missing_earliest_end(self):
        t = Tournament.objects.get(name='t1')
        s1 = G_SCORING_SYSTEMS[0].name
        start = datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc))
        r = Round(tournament=t,
                  scoring_system=s1,
                  dias=True,
                  start=start,
                  latest_end_time=start + HOURS_10)
        self.assertRaises(ValidationError, r.full_clean)

    def test_round_clean_missing_latest_end(self):
        t = Tournament.objects.get(name='t1')
        s1 = G_SCORING_SYSTEMS[0].name
        start = datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc))
        r = Round(tournament=t,
                  scoring_system=s1,
                  dias=True,
                  start=start,
                  earliest_end_time=start + HOURS_9)
        self.assertRaises(ValidationError, r.full_clean)

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

    # Round.save()
    # On save(), the scores for all Games in the round, the round itself, and the tournament should be updated
    def test_round_save(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(2)
        # Remember the current scores
        scores = {}
        for tp in t.tournamentplayer_set.all():
            for rp in tp.roundplayers():
                scores[rp] = rp.score
                for gp in rp.gameplayers():
                    scores[gp] = gp.score
            scores[tp] = tp.score
        # save() should recalculate relevant GamePlayer, RoundPlayer and TournamentPlayer scores
        r.save()
        # Verify and cleanup
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
                # Did this player play the newly-saved Round?
                if GamePlayer.objects.filter(player=tp.player, game__the_round=r).exists():
                    self.assertNotAlmostEqual(tp.score, scores[tp])
                    tp.score = scores[tp]
                    tp.save()
                else:
                    # Tournament score should be unchanged
                    self.assertEqual(tp.score, scores[tp])
                for rp in tp.roundplayers():
                    with self.subTest(player=rp.player, round_num=rp.the_round.number()):
                        if rp.the_round == r:
                            # Scores for everyone who played in this round should have changed
                            # No Round attribute can affect the score of someone who didn't play that round
                            if rp.gameplayers().exists():
                                self.assertNotAlmostEqual(rp.score, scores[rp])
                                rp.score = scores[rp]
                                rp.save()
                            else:
                                self.assertEqual(rp.score, scores[rp])
                            for gp in rp.gameplayers():
                                with self.subTest(player=gp.player, game_name=gp.game.name):
                                    self.assertNotAlmostEqual(gp.score, scores[gp])
                                    gp.score = scores[gp]
                                    gp.save()
                        else:
                            # Other rounds should be unchanged
                            self.assertEqual(rp.score, scores[rp])
                            for gp in rp.gameplayers():
                                with self.subTest(player=gp.player, game_name=gp.game.name):
                                    self.assertEqual(gp.score, scores[gp])


class GameTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')
        cls.set2 = GameSet.objects.get(name='Gibsons')

        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.COUNTS)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=8, tzinfo=timezone.utc)))
        r12 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=r11.start + HOURS_8)
        Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=r11.start + HOURS_16)
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=r11.start + HOURS_24)
        # Add Rounds to t3
        r31 = Round.objects.create(tournament=t3,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t3.start_date, time(hour=8, tzinfo=timezone.utc)),
                                   final_year=1907)
        cls.r32 = Round.objects.create(tournament=t3,
                                       scoring_system=s1,
                                       dias=True,
                                       start=r31.start + HOURS_8,
                                       earliest_end_time=r31.start + HOURS_8,
                                       latest_end_time=r31.start + HOURS_9)

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
        # Add Games to r31
        Game.objects.create(name='g31',
                            started_at=r31.start,
                            the_round=r31,
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

        # Eliminate Italy in 1903
        CentreCount.objects.create(power=cls.austria, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.england, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1903, count=10)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1903, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1903, count=4)

        # Solo victory for Germany in 1904
        CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=18)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=0)
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
        # These two are deliberately not in any tournaments
        cls.p9 = Player.objects.create(first_name='Queenie', last_name='Radiation')
        cls.p10 = Player.objects.create(first_name='Sebastian', last_name='Twinkie')
        # The remainder are not used in this method but are available for use in tests
        cls.p11 = Player.objects.create(first_name='Ursula', last_name='Vampire')

        # Tournament.news() will call Game.news() for all games in the current round,
        # which will need a player for every country
        # TODO These should really error out with no corresponding RoundPlayer. I guess clean() is not called ?
        # Add GamePlayers to g11
        GamePlayer.objects.create(player=cls.p1,
                                  game=g11,
                                  power=cls.austria)
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
                                  power=cls.austria)
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
        TournamentPlayer.objects.create(player=cls.p1,
                                        tournament=t1,
                                        backstabbr_username='AbbeyBrown')
        TournamentPlayer.objects.create(player=cls.p2,
                                        tournament=t1,
                                        backstabbr_username='nobody')
        TournamentPlayer.objects.create(player=cls.p3, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p5,
                                        tournament=t1,
                                        unranked=True)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p7,
                                        tournament=t1,
                                        location='The Moon')
        TournamentPlayer.objects.create(player=cls.p8, tournament=t1)

    # Game.backstabbr_game()
    @tag('backstabbr')
    def test_game_backstabbr_game(self):
        g = Game(name='newgame1',
                 started_at=self.r32.start,
                 the_round=self.r32,
                 is_finished=True,
                 the_set=self.set1,
                 external_url = 'https://www.backstabbr.com/game/4917371326693376')
        self.assertNotEqual(g.backstabbr_game(), None)

    def test_game_backstabbr_game_empty_external_url(self):
        g = Game(name='newgame1',
                 started_at=self.r32.start,
                 the_round=self.r32,
                 is_finished=True,
                 the_set=self.set1)
        self.assertRaises(backstabbr.InvalidGameUrl, g.backstabbr_game)

    def test_game_backstabbr_game_non_bs_url(self):
        g = Game(name='newgame1',
                 started_at=self.r32.start,
                 the_round=self.r32,
                 is_finished=True,
                 the_set=self.set1,
                 external_url='https://webdiplomacy.net/board.php?gameID=436906')
        self.assertRaises(backstabbr.InvalidGameUrl, g.backstabbr_game)

    # Game.webdiplomacy_game()
    @skip('WebDip parsing is broken')
    def test_game_webdiplomacy_game(self):
        g = Game(name='newgame1',
                 started_at=self.r32.start,
                 the_round=self.r32,
                 is_finished=True,
                 the_set=self.set1,
                 external_url='https://webdiplomacy.net/board.php?gameID=436906')
        self.assertNotEqual(g.webdiplomacy_game(), None)

    def test_game_webdiplomacy_game_empty_external_url(self):
        g = Game(name='newgame1',
                 started_at=self.r32.start,
                 the_round=self.r32,
                 is_finished=True,
                 the_set=self.set1)
        self.assertRaises(webdip.InvalidGameUrl, g.webdiplomacy_game)

    def test_game_webdiplomacy_game_non_wd_url(self):
        g = Game(name='newgame1',
                 started_at=self.r32.start,
                 the_round=self.r32,
                 is_finished=True,
                 the_set=self.set1,
                 external_url = 'https://www.backstabbr.com/game/4917371326693376')
        self.assertRaises(webdip.InvalidGameUrl, g.webdiplomacy_game)

    # Game.assign_powers_from_prefs()
    def test_game_assign_powers_from_prefs(self):
        scores = {
            self.p1: 30.0,
            self.p2: 25.0,
            self.p3: 20.0,
            self.p4: 10.0,
            self.p5: 7.0,
            self.p6: 7.0,
            self.p7: 1.0,
        }
        today = date.today()
        t = Tournament(name='t5',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=DrawSecrecy.SECRET)
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
                   start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r1.save()
        g1 = Game(name='newgame1',
                  started_at=r1.start,
                  the_round=r1,
                  is_finished=True,
                  the_set=self.set1)
        g1.save()
        rp = RoundPlayer(the_round=r1, player=self.p1)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p2)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p3)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p4)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p5)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p6)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p7)
        rp.save()
        # Now we can do the round for the game we want to seed
        r2 = Round(tournament=t,
                   scoring_system='Sum of Squares',
                   dias=True,
                   start=r1.start + HOURS_24)
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
        # Set the TournamentPlayer scores as we need them
        for tp in t.tournamentplayer_set.all():
            tp.score = scores[tp.player]
            tp.save()
        # Now add preferences for some players
        p = Preference(player=tp1, power=self.austria, ranking=1)
        p.save()
        p = Preference(player=tp1, power=self.italy, ranking=2)
        p.save()
        p = Preference(player=tp3, power=self.austria, ranking=1)
        p.save()
        p = Preference(player=tp3, power=self.italy, ranking=2)
        p.save()
        p = Preference(player=tp4, power=self.austria, ranking=1)
        p.save()
        p = Preference(player=tp4, power=self.england, ranking=2)
        p.save()
        p = Preference(player=tp4, power=self.france, ranking=3)
        p.save()
        p = Preference(player=tp4, power=self.germany, ranking=4)
        p.save()
        p = Preference(player=tp5, power=self.england, ranking=1)
        p.save()
        p = Preference(player=tp5, power=self.france, ranking=2)
        p.save()
        p = Preference(player=tp6, power=self.england, ranking=1)
        p.save()
        p = Preference(player=tp6, power=self.france, ranking=2)
        p.save()
        p = Preference(player=tp7, power=self.austria, ranking=1)
        p.save()
        g2.assign_powers_from_prefs()
        # We need to retrieve the GamePlayers from the database to see the updates
        # No powers taken - get first preference
        gp = GamePlayer.objects.get(game=g2, player=self.p7)
        self.assertEqual(gp.power, self.austria)
        # Players 5 and 6 are tied, with the same prefs. 1 gets E, the other F
        gp = GamePlayer.objects.get(game=g2, player=self.p6)
        self.assertIn(gp.power, [self.england, self.france])
        gp = GamePlayer.objects.get(game=g2, player=self.p5)
        self.assertIn(gp.power, [self.england, self.france])
        # First three preferences gone, but fourth available, should get that
        gp = GamePlayer.objects.get(game=g2, player=self.p4)
        self.assertEqual(gp.power, self.germany)
        # First preference gone, but second available, should get that
        gp = GamePlayer.objects.get(game=g2, player=self.p3)
        self.assertEqual(gp.power, self.italy)
        # Others have no preferences, and all prefs gone
        # Note that this will also delete everything associated with the Tournament
        t.delete()
        self.assertEqual(Preference.objects.count(), 0)

    def test_assign_powers_from_prefs_already_done(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertTrue(g.gameplayer_set.filter(power__isnull=False).exists())
        self.assertRaises(PowerAlreadyAssigned, g.assign_powers_from_prefs)

    # Game.set_is_finished()
    def test_game_set_is_finished_solo(self):
        # Game is finished because somebody won
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertFalse(g.is_finished)
        g.set_is_finished()
        self.assertTrue(g.is_finished)
        # Cleanup
        g.is_finished = False
        g.save(update_fields=['is_finished'])

    def test_game_set_is_finished_reached(self):
        # Game is finished because it reached the final year
        t = Tournament.objects.get(name='t3')
        r = t.round_numbered(1)
        y = r.final_year
        g = r.game_set.get(name='g31')
        self.assertTrue(g.is_finished)
        g.is_finished = False
        g.save(update_fields=['is_finished'])
        g.set_is_finished(y)
        self.assertTrue(g.is_finished)
        # No cleanup needed

    def test_game_set_is_finished_not_reached(self):
        # Game is not finished because it didn't yet reach the final year
        t = Tournament.objects.get(name='t3')
        r = t.round_numbered(1)
        y = r.final_year
        g = r.game_set.get(name='g31')
        self.assertTrue(g.is_finished)
        g.is_finished = False
        g.save(update_fields=['is_finished'])
        g.set_is_finished(y - 1)
        self.assertFalse(g.is_finished)
        # Cleanup
        g.is_finished = True
        g.save(update_fields=['is_finished'])

    def test_game_set_is_finished_unlimited(self):
        # Game not finished because there is no final year
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        self.assertFalse(g.is_finished)
        g.set_is_finished(1999)
        self.assertFalse(g.is_finished)
        # No cleanup needed


    # Game.create_or_update_sc_counts_from_ownerships
    def test_create_sc_count_invalid(self):
        # Arbitrary game
        g = Game.objects.first()
        self.assertRaises(SCOwnershipsNotFound,
                          g.create_or_update_sc_counts_from_ownerships,
                          1901)

    def test_create_sc_count(self):
        # Arbitrary game
        g = Game.objects.first()
        YEAR = 1920
        self.assertFalse(g.supplycentreownership_set.filter(year=YEAR).exists())
        self.assertFalse(g.centrecount_set.filter(year=YEAR).exists())
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
                  self.england : 0,
                  self.france : 0,
                  self.germany : 0,
                  self.italy : 0,
                  self.russia : 0,
                  self.turkey : 0,
              }
        # Add some SC ownerships for a far off year
        for k, v in test_data.items():
            sco = SupplyCentreOwnership(sc=k, owner=v, year=YEAR, game=g)
            sco.save()
            res[v] += 1
        g.create_or_update_sc_counts_from_ownerships(YEAR)
        ccs = g.centrecount_set.filter(year=YEAR)
        # We should always have CentreCounts for all powers
        self.assertEqual(len(ccs), 7)
        self.assertEqual(ccs.aggregate(Sum('count'))['count__sum'], len(test_data))
        for cc in ccs:
            with self.subTest(power=cc.power):
                self.assertEqual(cc.count, res[cc.power])
        # Remove everything we added to the database
        g.supplycentreownership_set.filter(year=YEAR).delete()
        ccs.delete()

    def test_update_sc_count(self):
        # Arbitrary game
        g = Game.objects.first()
        YEAR = 1920
        self.assertFalse(g.supplycentreownership_set.filter(year=YEAR).exists())
        self.assertFalse(g.centrecount_set.filter(year=YEAR).exists())
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
                  self.england : 0,
                  self.france : 0,
                  self.germany : 0,
                  self.italy : 0,
                  self.russia : 0,
                  self.turkey : 0,
              }
        # Add some SC ownerships for a far off year
        scos = []
        for k, v in test_data.items():
            sco = SupplyCentreOwnership(sc=k, owner=v, year=YEAR, game=g)
            sco.save()
            scos.append(sco)
            res[v] += 1
        # Add some CentreCounts to be updated by the method being tested
        cc = CentreCount(power=self.england, game=g, year=YEAR, count=17)
        cc = CentreCount(power=self.turkey, game=g, year=YEAR, count=17)
        g.create_or_update_sc_counts_from_ownerships(YEAR)
        ccs = g.centrecount_set.filter(year=YEAR)
        # We should always have CentreCounts for all powers
        self.assertEqual(len(ccs), 7)
        self.assertEqual(ccs.aggregate(Sum('count'))['count__sum'], len(test_data))
        for cc in ccs:
            with self.subTest(power=cc.power):
                self.assertEqual(cc.count, res[cc.power])
        # Remove everything we added to the database
        g.supplycentreownership_set.filter(year=YEAR).delete()
        ccs.delete()

    # Game.compare_sc_counts_and_ownerships()
    def test_game_compare_sc_counts_and_ownerships(self):
        # Arbitrary game
        g = Game.objects.first()
        YEAR = 1920
        self.assertFalse(g.supplycentreownership_set.filter(year=YEAR).exists())
        self.assertFalse(g.centrecount_set.filter(year=YEAR).exists())
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
        # Add some SC ownerships for a far off year
        for k,v in test_data.items():
            sco = SupplyCentreOwnership(sc=k, owner=v, year=YEAR, game=g)
            sco.save()
        g.create_or_update_sc_counts_from_ownerships(YEAR)
        ccs = g.centrecount_set.filter(year=YEAR)
        # Hopefully everything matches!
        self.assertEqual([], g.compare_sc_counts_and_ownerships(YEAR))
        # Now modify one SupplyCentreOwnership to create a mismatch
        sco.owner = self.england
        sco.save(update_fields=['owner'])
        # That should give us two mismatches (the old and new owners)
        self.assertEqual(2, len(g.compare_sc_counts_and_ownerships(YEAR)))
        # Remove everything we added to the database
        g.supplycentreownership_set.filter(year=YEAR).delete()
        ccs.delete()

    # TODO Game.compare_sc_counts_and_ownerships() raises SCOwnershipsNotFound

    # TODO Game.compare_sc_counts_and_ownerships() with missing CentreCount

    # TODO Game._calc_scores()

    # Game.scores()
    def test_scores_no_powers_assigned(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        gps = g.gameplayer_set.all()
        self.assertGreater(len(gps), 0)
        power_map = {}
        for gp in gps:
            power_map[gp] = gp.power
            gp.power = None
            gp.save(update_fields=['power'])
        scores = g.scores()
        # TODO validate results
        # Cleanup
        for gp in gps:
            gp.power = power_map[gp]
            gp.save(update_fields=['power'])

    # Game.update_scores()
    def test_game_update_scores_invalid(self):
        today = date.today()
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=today,
                                                      end_date=today + HOURS_24,
                                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                      round_scoring_system=R_SCORING_SYSTEMS[0].name)
        r = Round.objects.create(tournament=t,
                                 scoring_system='Invalid System',
                                 dias=True,
                                 start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        g = Game.objects.create(name='gamey', started_at=r.start, the_round=r, the_set=self.set1)
        self.assertRaises(InvalidScoringSystem, g.update_scores)

    def test_game_update_scores_no_powers_assigned(self):
        # Test Game.update_scores() with no powers assigned
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        power_map = {}
        for gp in g.gameplayer_set.all():
            power_map[gp] = gp.power
            gp.power = None
            gp.save(update_fields=['power'])
        g.update_scores()
        # Cleanup
        for gp in g.gameplayer_set.all():
            gp.power = power_map[gp]
            gp.save(update_fields=['power'])

    def test_game_update_scores(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        for gp in g.gameplayer_set.all():
            self.assertEqual(gp.score, 0.0)
        for rp in g.the_round.roundplayer_set.all():
            self.assertEqual(rp.score, 0.0)
        g.update_scores()
        # GamePlayer.score and RoundPlayer.score should be updated
        # p5 should get 100, others zero
        # Cleanup at the same time
        for gp in g.gameplayer_set.all():
            with self.subTest(player=gp.player):
                if gp.player == self.p5:
                    self.assertEqual(gp.score, 100.0)
                    gp.score = 0.0
                    gp.save()
                else:
                    self.assertEqual(gp.score, 0.0)
        for rp in g.the_round.roundplayer_set.all():
            with self.subTest(player=rp.player):
                if rp.player == self.p5:
                    self.assertEqual(rp.score, 100.0)
                    rp.score = 0.0
                    rp.save()
                else:
                    self.assertEqual(rp.score, 0.0)

    def test_game_update_scores_no_propagate(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        for gp in g.gameplayer_set.all():
            self.assertEqual(gp.score, 0.0)
        for rp in g.the_round.roundplayer_set.all():
            self.assertEqual(rp.score, 0.0)
        g.update_scores(update_round=False)
        # GamePlayer but not RoundPlayer.score should be updated
        # p5 should get 100, others zero
        # Cleanup at the same time
        for gp in g.gameplayer_set.all():
            with self.subTest(player=gp.player):
                if gp.player == self.p5:
                    self.assertEqual(gp.score, 100.0)
                    gp.score = 0.0
                    gp.save()
                else:
                    self.assertEqual(gp.score, 0.0)
        for rp in g.the_round.roundplayer_set.all():
            with self.subTest(player=rp.player):
                self.assertEqual(rp.score, 0.0)

    # Game.positions()
    def test_game_positions(self):
        g = Game.objects.first()
        # TODO Validate results
        g.positions()

    # Game.is_dias()
    def test_game_is_dias(self):
        for g in Game.objects.all():
            with self.subTest(game=g):
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
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.SPRING,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        self.assertIsNone(g.passed_draw())
        dp.delete()

    def test_game_passed_draw_other_game(self):
        t = Tournament.objects.get(name='t1')
        g2 = t.round_numbered(2).game_set.get(name='g13')
        g1 = t.round_numbered(2).game_set.get(name='g14')
        dp = DrawProposal.objects.create(game=g1,
                                         year=1905,
                                         season=Seasons.SPRING,
                                         passed=True,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        self.assertIsNone(g2.passed_draw())
        dp.delete()

    def test_game_passed_draw_one(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.SPRING,
                                         passed=True,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        self.assertEqual(g.passed_draw(), dp)
        dp.delete()

    def test_game_passed_draw_two(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp1 = DrawProposal.objects.create(game=g,
                                          year=1905,
                                          season=Seasons.SPRING,
                                          passed=False,
                                          proposer=self.austria)
        dp1.drawing_powers.add(self.austria)
        dp1.drawing_powers.add(self.england)
        dp1.drawing_powers.add(self.france)
        dp1.drawing_powers.add(self.germany)
        dp1.drawing_powers.add(self.italy)
        dp1.drawing_powers.add(self.russia)
        dp1.drawing_powers.add(self.turkey)
        dp2 = DrawProposal.objects.create(game=g,
                                          year=1905,
                                          season=Seasons.FALL,
                                          passed=True,
                                          proposer=self.austria)
        dp2.drawing_powers.add(self.austria)
        dp2.drawing_powers.add(self.england)
        dp2.drawing_powers.add(self.france)
        dp2.drawing_powers.add(self.germany)
        dp2.drawing_powers.add(self.italy)
        dp2.drawing_powers.add(self.russia)
        dp2.drawing_powers.add(self.turkey)
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
        self.assertEqual(len(g.survivors()), 5)

    def test_game_survivors_year_1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(len(g.survivors(1901)), 7)

    def test_game_survivors_year_2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        # survivors() just returns surviving players, regardless of whether they
        # lost to a solo or were excluded from a draw
        self.assertEqual(len(g.survivors(1904)), 5)

    def test_game_survivors_invalid_year(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        # As the Game has not yeat reached 1905, we should get the most recent state
        self.assertEqual(len(g.survivors(1905)), len(g.survivors()))

    # Game.board_call_msg()
    def test_game_board_call_msg(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        # TODO validate results
        g.board_call_msg()

    def test_game_board_call_msg_external_url(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(len(g.external_url), 0)
        URL = 'www.example.com/nonsense'
        g.external_url = URL
        g.save(update_fields=['external_url'])
        msg = g.board_call_msg()
        self.assertIn(URL, msg)
        # Cleanup
        g.external_url = ''
        g.save(update_fields=['external_url'])

    def test_game_board_call_msg_notes(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(len(g.notes), 0)
        NOTES = 'Actual notes go here'
        g.notes = NOTES
        g.save(update_fields=['notes'])
        msg = g.board_call_msg()
        self.assertIn(NOTES, msg)
        # Cleanup
        g.notes = ''
        g.save(update_fields=['notes'])

    def test_game_board_call_msg_virtual(self):
        # Ensure some, but not all, players have backstabbr usernames
        t = Tournament.objects.get(name='t1')
        self.assertFalse(t.is_virtual())
        t.format = Formats.VFTF
        t.save(update_fields=['format'])
        g = t.round_numbered(1).game_set.get(name='g11')
        msg = g.board_call_msg()
        self.assertNotIn('  ', msg)
        self.assertNotIn('()', msg)
        # Check for backstabbr username
        self.assertIn('(AbbeyBrown)', msg)
        # Cleanup
        t.format = Formats.FTF
        t.save(update_fields=['format'])

    def test_game_board_call_msg_no_powers(self):
        t = Tournament.objects.get(name='t1')
        self.assertFalse(t.is_virtual())
        g = t.round_numbered(1).game_set.get(name='g11')
        powers = {}
        for gp in g.gameplayer_set.all():
            self.assertIsNotNone(gp.power)
            powers[gp] = gp.power
            gp.power = None
            gp.save(update_fields=['power'])
        msg = g.board_call_msg()
        self.assertIn('Power TBD', msg)
        # Cleanup
        for gp in g.gameplayer_set.all():
            gp.power = powers[gp]
            gp.save(update_fields=['power'])

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
        dp = DrawProposal.objects.create(game=g,
                                         year=1901,
                                         season=Seasons.SPRING,
                                         passed=True,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        self.assertIn('Vote passed ', g.result_str())
        dp.delete()

    def test_game_result_str_conceded(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g,
                                         year=1901,
                                         season=Seasons.SPRING,
                                         passed=True,
                                         proposer=self.england)
        dp.drawing_powers.add(self.england)
        self.assertIn('conceded ', g.result_str())
        dp.delete()

    def test_game_result_str_failed_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp = DrawProposal.objects.create(game=g,
                                         year=1901,
                                         season=Seasons.SPRING,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        # Game is still ongoing
        self.assertIsNone(g.result_str())
        dp.delete()

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

    def test_game_clean_non_unique_name_2(self):
        g1 = Game.objects.first()
        g1.clean()

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
        g1.save(update_fields=['the_set'])
        # TODO Verify that the initial image has been updated

    @tag('slow')
    def test_game_save_end_of_game(self):
        today = date.today()
        t = Tournament(name='t5',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=DrawSecrecy.SECRET)
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
                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
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
        self.assertFalse(r.is_finished)
        self.assertFalse(t.is_finished)
        g1.is_finished = True
        g1.save(update_fields=['is_finished'])
        self.assertFalse(r.is_finished)
        self.assertFalse(t.is_finished)
        # Note that this will also delete all associated objects
        t.delete()

    @tag('slow')
    def test_game_save_end_of_round(self):
        today = date.today()
        t = Tournament(name='t5',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=DrawSecrecy.SECRET)
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
        r1 = Round(tournament=t,
                   scoring_system='Sum of Squares',
                   dias=True,
                   start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r1.save()
        rp = RoundPlayer(the_round=r1, player=self.p1)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p2)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p3)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p4)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p5)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p6)
        rp.save()
        rp = RoundPlayer(the_round=r1, player=self.p7)
        rp.save()
        r2 = Round(tournament=t,
                   scoring_system='Sum of Squares',
                   dias=True,
                   start=datetime.combine(t.start_date, time(hour=16, tzinfo=timezone.utc)))
        r2.save()
        g1 = Game(name='newgame1',
                  started_at=r1.start,
                  the_round=r1,
                  is_finished=True,
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
                  started_at=r1.start,
                  the_round=r1,
                  is_finished=False,
                  the_set=self.set1)
        g2.save()
        self.assertFalse(r1.is_finished)
        self.assertFalse(t.is_finished)
        g2.is_finished = True
        g2.save(update_fields=['is_finished'])
        # Round but not Tournament should now be flagged as finished
        self.assertTrue(r1.is_finished)
        self.assertFalse(t.is_finished)
        # Note that this will also delete all associated objects
        t.delete()

    @tag('slow')
    def test_game_save_end_of_tournament(self):
        today = date.today()
        t = Tournament(name='t5',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=DrawSecrecy.SECRET)
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
                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
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
        self.assertFalse(r.is_finished)
        self.assertFalse(t.is_finished)
        g1.is_finished = True
        g1.save(update_fields=['is_finished'])
        # Round and Tournament should now be flagged as finished
        self.assertTrue(r.is_finished)
        self.assertTrue(t.is_finished)
        # Note that this will also delete all associated objects
        t.delete()

    # Game.get_absolute_url()
    def test_game_get_absolute_url(self):
        g = Game.objects.first()
        g.get_absolute_url()


class SupplyCentreOwnershipTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=8, tzinfo=timezone.utc)))

        # Add Games to r11
        Game.objects.create(name='g11',
                                  started_at=r11.start,
                                  the_round=r11,
                                  the_set=cls.set1)

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')

    # SupplyCentreOwnership.__str__()
    def test_supplycentreownership_str(self):
        g = Game.objects.first()
        sc = SupplyCentre.objects.get(abbreviation='Mun')
        sco = SupplyCentreOwnership.objects.create(sc=sc, owner=self.austria, year=1909, game=g)
        # TODO validate result
        str(sco)


class DrawProposalTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.COUNTS)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=8, tzinfo=timezone.utc)))
        r12 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=r11.start + HOURS_8)
        Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=r11.start + HOURS_16)
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=r11.start + HOURS_24)
        # Add Rounds to t3
        r31 = Round.objects.create(tournament=t3,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t3.start_date, time(hour=8, tzinfo=timezone.utc)),
                                   final_year=1907)
        cls.r32 = Round.objects.create(tournament=t3,
                                       scoring_system=s1,
                                       dias=True,
                                       start=r31.start + HOURS_8,
                                       earliest_end_time=r31.start + HOURS_8,
                                       latest_end_time=r31.start + HOURS_9)

        # Add Games to r11
        g11 = Game.objects.create(name='g11',
                                  started_at=r11.start,
                                  the_round=r11,
                                  the_set=cls.set1)
        # Add Games to r31
        Game.objects.create(name='g31',
                            started_at=r31.start,
                            the_round=r31,
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

        # Eliminate Italy in 1903
        CentreCount.objects.create(power=cls.austria, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.england, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1903, count=10)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1903, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1903, count=4)

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
        # These two are deliberately not in any tournaments
        cls.p9 = Player.objects.create(first_name='Queenie', last_name='Radiation')
        cls.p10 = Player.objects.create(first_name='Sebastian', last_name='Twinkie')
        # The remainder are not used in this method but are available for use in tests
        cls.p11 = Player.objects.create(first_name='Ursula', last_name='Vampire')

        # Tournament.news() will call Game.news() for all games in the current round,
        # which will need a player for every country
        # TODO These should really error out with no corresponding RoundPlayer. I guess clean() is not called ?
        # Add GamePlayers to g11
        GamePlayer.objects.create(player=cls.p1,
                                  game=g11,
                                  power=cls.austria)
        GamePlayer.objects.create(player=cls.p3, game=g11, power=cls.england)
        GamePlayer.objects.create(player=cls.p4, game=g11, power=cls.france)
        GamePlayer.objects.create(player=cls.p5, game=g11, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=g11, power=cls.italy)
        GamePlayer.objects.create(player=cls.p7, game=g11, power=cls.russia)
        GamePlayer.objects.create(player=cls.p8, game=g11, power=cls.turkey)
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
        TournamentPlayer.objects.create(player=cls.p2, tournament=t1, backstabbr_username='nobody')
        TournamentPlayer.objects.create(player=cls.p3, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p5, tournament=t1, unranked=True)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t1, location='The Moon')
        TournamentPlayer.objects.create(player=cls.p8, tournament=t1)

        # Add TournamentPlayers to t3
        TournamentPlayer.objects.create(player=cls.p5, tournament=t3, score=147.3)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t3, score=47.3)
        # Add RoundPlayers to r31
        RoundPlayer.objects.create(player=cls.p5, the_round=r31, score=0.0)
        RoundPlayer.objects.create(player=cls.p7, the_round=r31, score=0.0)
        # Add RoundPlayers to r32
        RoundPlayer.objects.create(player=cls.p5, the_round=cls.r32, score=47.3)
        RoundPlayer.objects.create(player=cls.p7, the_round=cls.r32, score=47.3)

    # DrawProposal.draw_size()
    def test_draw_proposal_concession(self):
        g = Game.objects.first()
        dp = DrawProposal.objects.create(game=g,
                                         year=1910,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        self.assertEqual(dp.draw_size(), 1)
        dp.delete()

    def test_draw_proposal_draw_size_all(self):
        g = Game.objects.first()
        dp = DrawProposal.objects.create(game=g,
                                         year=1910,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        self.assertEqual(dp.draw_size(), 7)
        dp.delete()

    # DrawProposal.powers()
    def test_draw_proposal_powers_one(self):
        g = Game.objects.first()
        dp = DrawProposal.objects.create(game=g,
                                         year=1910,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        self.assertEqual(len(dp.powers()), 1)
        dp.delete()

    def test_draw_proposal_powers_all(self):
        g = Game.objects.first()
        dp = DrawProposal.objects.create(game=g,
                                         year=1910,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        self.assertEqual(len(dp.powers()), 7)
        dp.delete()

    # DrawProposal.power_is_part()
    def test_draw_proposal_power_is_part_one(self):
        g = Game.objects.first()
        dp = DrawProposal.objects.create(game=g,
                                         year=1910,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        with self.subTest(power=self.austria):
            self.assertEqual(dp.power_is_part(self.austria), True)
        for power in [self.england,
                      self.france,
                      self.germany,
                      self.italy,
                      self.russia,
                      self.turkey]:
            with self.subTest(power=power):
                self.assertEqual(dp.power_is_part(power), False)
        dp.delete()

    def test_draw_proposal_power_is_part_all(self):
        g = Game.objects.first()
        dp = DrawProposal.objects.create(game=g,
                                         year=1910,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        for power in [self.austria,
                      self.england,
                      self.france,
                      self.germany,
                      self.italy,
                      self.russia,
                      self.turkey]:
            with self.subTest(power=power):
                self.assertEqual(dp.power_is_part(self.austria), True)
        dp.delete()

    # DrawProposal.votes_against()
    def test_draw_proposal_votes_against_none(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal.objects.create(game=g,
                                         year=1910,
                                         season=Seasons.FALL,
                                         votes_in_favour=7,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        self.assertEqual(dp.votes_against(), 0)
        dp.delete()

    def test_draw_proposal_votes_against_some(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal.objects.create(game=g,
                                         year=1910,
                                         season=Seasons.FALL,
                                         votes_in_favour=2,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        self.assertEqual(dp.votes_against(), 5)
        dp.delete()

    def test_draw_proposal_votes_against_exception(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g,
                                         year=1910,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        self.assertRaises(TypeError, dp.votes_against)
        dp.delete()

    # DrawProposal.clean()
    def test_draw_proposal_clean_with_duplicates(self):
        g = Game.objects.first()
        dp = DrawProposal.objects.create(game=g,
                                         year=1910,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.austria)
        self.assertRaises(ValidationError, dp.clean)
        dp.delete()

    def test_draw_proposal_clean_with_gap(self):
        g = Game.objects.first()
        dp = DrawProposal.objects.create(game=g,
                                         year=1910,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        self.assertRaises(ValidationError, dp.clean)
        dp.delete()

    def test_draw_proposal_with_dead_powers(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.SPRING,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        self.assertRaises(ValidationError, dp.clean)
        dp.delete()

    def test_draw_proposal_missing_power_dias(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g,
                                         year=1901,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        self.assertRaises(ValidationError, dp.clean)
        dp.delete()

    def test_draw_proposal_too_late(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g,
                                         year=1903,
                                         season=Seasons.FALL,
                                         passed=True,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        self.assertRaises(ValidationError, dp.clean)
        dp.delete()

    def test_draw_proposal_multiple_successful(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        done = g.is_finished
        dp1 = DrawProposal.objects.create(game=g,
                                          year=1901,
                                          season=Seasons.FALL,
                                          passed=True,
                                          proposer=self.austria)
        dp1.drawing_powers.add(self.austria)
        dp1.drawing_powers.add(self.england)
        dp1.drawing_powers.add(self.france)
        dp1.drawing_powers.add(self.germany)
        dp1.drawing_powers.add(self.italy)
        dp1.drawing_powers.add(self.russia)
        dp1.drawing_powers.add(self.turkey)
        dp2 = DrawProposal(game=g,
                           year=1902,
                           season=Seasons.FALL,
                           passed=True,
                           proposer=self.austria)
        self.assertRaises(ValidationError, dp2.clean)
        # Clean up
        dp1.delete()
        g.is_finished = done
        g.save(update_fields=['is_finished'])

    def test_draw_proposal_clean_passed_not_set(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.FALL,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        self.assertRaises(ValidationError, dp.clean)
        dp.delete()

    def test_draw_proposal_clean_passed_false(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        # This one should be fine
        dp.clean()
        dp.delete()

    def test_draw_proposal_clean_passed_true(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.FALL,
                                         passed=True,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        # This one should be fine
        dp.clean()
        dp.delete()

    def test_draw_proposal_clean_votes_in_favour_seven(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.FALL,
                                         votes_in_favour=7,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        dp.drawing_powers.add(self.austria)
        # This one should be fine
        dp.clean()
        dp.delete()

    def test_draw_proposal_clean_votes_in_favour_zero(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.FALL,
                                         votes_in_favour=0,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        dp.drawing_powers.add(self.austria)
        # This one should be fine
        dp.clean()
        dp.delete()

    # DrawProposal.clean() after Game has been won
    def test_draw_proposal_clean_after_win(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertFalse(g.centrecount_set.filter(year=1904).exists())
        CentreCount.objects.create(power=self.austria, game=g, year=1904, count=0)
        CentreCount.objects.create(power=self.england, game=g, year=1904, count=4)
        CentreCount.objects.create(power=self.france, game=g, year=1904, count=4)
        CentreCount.objects.create(power=self.germany, game=g, year=1904, count=18)
        CentreCount.objects.create(power=self.italy, game=g, year=1904, count=0)
        CentreCount.objects.create(power=self.russia, game=g, year=1904, count=3)
        CentreCount.objects.create(power=self.turkey, game=g, year=1904, count=5)
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.FALL,
                                         passed=True,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        # This one should be fine
        self.assertRaises(ValidationError, dp.clean)
        # Clean up
        g.centrecount_set.filter(year=1904).delete()

    def test_draw_proposal_clean_votes_in_favour_not_set(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.FALL,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        dp.drawing_powers.add(self.austria)
        self.assertRaises(ValidationError, dp.clean)
        dp.delete()

    def test_draw_proposal_clean_votes_in_favour_too_late(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        self.assertEqual(CentreCount.objects.filter(game=g, year=1901).count(), 0)
        self.assertEqual(g.final_year(), 1900)
        # We need to add some SupplyCentreCounts to the Game
        scs = {self.austria: 5,
               self.england: 4,
               self.france: 5,
               self.germany: 6,
               self.italy: 4,
               self.russia: 6,
               self.turkey: 4}
        for p, c in scs.items():
            CentreCount.objects.create(power=p,
                                       game=g,
                                       year=1901,
                                       count=c)
        dp = DrawProposal.objects.create(game=g,
                                         year=1901,
                                         season=Seasons.FALL,
                                         proposer=self.austria,
                                         votes_in_favour=7)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        dp.drawing_powers.add(self.austria)
        self.assertRaises(ValidationError, dp.clean)
        # Clean up
        CentreCount.objects.filter(game=g, year=1901).delete()
        dp.delete()

    def test_draw_proposal_clean_votes_in_favour_multiple_successful(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp1 = DrawProposal.objects.create(game=g,
                                          year=1901,
                                          season=Seasons.FALL,
                                          proposer=self.austria,
                                          votes_in_favour=7)
        dp1.drawing_powers.add(self.england)
        dp1.drawing_powers.add(self.france)
        dp1.drawing_powers.add(self.germany)
        dp1.drawing_powers.add(self.italy)
        dp1.drawing_powers.add(self.russia)
        dp1.drawing_powers.add(self.turkey)
        dp1.drawing_powers.add(self.austria)
        self.assertTrue(dp1.passed)
        dp2 = DrawProposal(game=g,
                           year=1902,
                           season=Seasons.FALL,
                           proposer=self.austria,
                           votes_in_favour=7)
        self.assertRaises(ValidationError, dp2.clean)
        dp1.delete()

    # Test DrawProposal.clean() when votes_in_favour is > number of surviving powers
    def test_draw_proposal_clean_votes_in_favour_too_many(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        self.assertEqual(CentreCount.objects.filter(game=g, year=1903).count(), 0)
        self.assertEqual(g.final_year(), 1900)
        # We need to add some SupplyCentreCounts to the Game
        scs = {self.austria: 4,
               self.england: 0,
               self.france: 7,
               self.germany: 7,
               self.italy: 4,
               self.russia: 7,
               self.turkey: 5}
        for p, c in scs.items():
            CentreCount.objects.create(power=p,
                                       game=g,
                                       year=1903,
                                       count=c)
        dp = DrawProposal.objects.create(game=g,
                                         year=1904,
                                         season=Seasons.FALL,
                                         proposer=self.austria,
                                         votes_in_favour=7)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        dp.drawing_powers.add(self.austria)
        self.assertRaises(ValidationError, dp.clean)
        # Clean up
        CentreCount.objects.filter(game=g, year=1903).delete()
        dp.delete()

    # DrawProposal.save()

    def test_draw_proposal_save_vote_passed(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        # Modify the game to not yet be finished
        g.is_finished = False
        g.save(update_fields=['is_finished'])
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.FALL,
                                         votes_in_favour=7,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        dp.drawing_powers.add(self.austria)
        self.assertTrue(dp.passed)
        self.assertTrue(g.is_finished)
        # Cleanup
        dp.delete()

    def test_draw_proposal_save_sets_passed_to_true(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        # Modify the game to not yet be finished
        g.is_finished = False
        g.save(update_fields=['is_finished'])
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.FALL,
                                         votes_in_favour=6,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        dp.drawing_powers.add(self.austria)
        self.assertFalse(dp.passed)
        self.assertFalse(g.is_finished)
        # Cleanup
        dp.delete()
        g.is_finished = True
        g.save(update_fields=['is_finished'])

    def test_draw_proposal_two_successful(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        # Modify the game to not yet be finished
        g.is_finished = False
        g.save(update_fields=['is_finished'])
        dp = DrawProposal.objects.create(game=g,
                                         year=1905,
                                         season=Seasons.SPRING,
                                         votes_in_favour=7,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        dp.drawing_powers.add(self.austria)
        dp2 = DrawProposal(game=g,
                           year=1905,
                           season=Seasons.FALL,
                           votes_in_favour=7,
                           proposer=self.austria)
        # Full clean should object to two passed draws for the same Game
        self.assertRaises(ValidationError, dp2.full_clean)
        # Cleanup
        dp.delete()

    # DrawProposal.__str__()
    def test_drawproposal_str(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g,
                                         year=1901,
                                         season=Seasons.FALL,
                                         passed=True,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.germany)
        dp.drawing_powers.add(self.italy)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.turkey)
        # TODO Validate result
        str(dp)
        dp.delete()


class RoundPlayerTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=8, tzinfo=timezone.utc)))
        r12 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=r11.start + HOURS_8)
        r13 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   is_finished=True,
                                   start=r11.start + HOURS_16)
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=r11.start + HOURS_24)

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

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

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
        # These two are deliberately not in any tournaments
        cls.p9 = Player.objects.create(first_name='Queenie', last_name='Radiation')
        cls.p10 = Player.objects.create(first_name='Sebastian', last_name='Twinkie')
        # The remainder are not used in this method but are available for use in tests
        cls.p11 = Player.objects.create(first_name='Ursula', last_name='Vampire')

        # Tournament.news() will call Game.news() for all games in the current round,
        # which will need a player for every country
        # TODO These should really error out with no corresponding RoundPlayer. I guess clean() is not called ?
        # Add GamePlayers to g11
        GamePlayer.objects.create(player=cls.p1,
                                  game=g11,
                                  power=cls.austria)
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
                                  power=cls.austria)
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
        TournamentPlayer.objects.create(player=cls.p2, tournament=t1, backstabbr_username='nobody')
        TournamentPlayer.objects.create(player=cls.p3, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p5, tournament=t1, unranked=True)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t1, location='The Moon')
        TournamentPlayer.objects.create(player=cls.p8, tournament=t1)

    # RoundPlayer.score_is_final()
    def test_roundplayer_score_is_final_round_finished(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(3)
        self.assertTrue(r.is_finished)
        rp = RoundPlayer(the_round=r,
                         player=self.p1,
                         score=7)
        self.assertTrue(rp.score_is_final())

    def test_roundplayer_score_is_final_round_not_started(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(1)
        self.assertFalse(r.is_finished)
        rp = r.roundplayer_set.first()
        self.assertFalse(rp.score_is_final())

    def test_roundplayer_score_is_final_round_mixed(self):
        # Player playing two games, one of which is done
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(2)
        self.assertFalse(r.is_finished)
        rp = r.roundplayer_set.first()
        self.assertEqual(rp.gameplayers().count(), 2)
        self.assertFalse(rp.score_is_final())

    # TODO RoundPlayer.score_is_final() for player playing two games,
    #      both of which are finished, in a round that is still going

    def test_roundplayer_score_is_final_sum_games(self):
        # Score can change if there are more rounds that haven't started,
        # or more rounds that the player is playing in that haven't finished
        # unless they didn't play any games this round
        # For now, let's make sure it gets called for a TScoringSumGames tournament
        t = Tournament.objects.get(name='t1')
        sys = t.tournament_scoring_system
        t.tournament_scoring_system = T_SCORING_SYSTEMS[6].name
        t.save()
        self.assertFalse(t.tournament_scoring_system_obj().uses_round_scores)
        r = t.round_numbered(1)
        rp = r.roundplayer_set.get(player=self.p8)
        self.assertTrue(rp.score_is_final())
        # Cleanup
        t.tournament_scoring_system = sys
        t.save()

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

    def test_roundplayer_clean_ok(self):
        tp = TournamentPlayer.objects.first()
        rp = tp.roundplayers().first()
        rp.clean()

    # RoundPlayer.__str__()
    def test_roundplayer_str(self):
        rp = RoundPlayer.objects.first()
        # TODO Validate result
        str(rp)

    # RoundPlayer deletion
    def test_roundplayer_delete(self):
        # Chris
        today = date.today()
        # Single Round Tournament, with points for sitting out a round
        s = 'Best game counts'
        t = Tournament.objects.create(name='rp_test',
                                      start_date=today,
                                      end_date=today + HOURS_24,
                                      round_scoring_system=s,
                                      non_player_round_score=4005,
                                      non_player_round_score_once=False,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        r = Round.objects.create(tournament=t,
                                 scoring_system=s1,
                                 dias=True,
                                 start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        g = Game.objects.create(name='g11',
                                started_at=r.start,
                                the_round=r,
                                the_set=self.set1)
        # 10 TournamentPlayers and RoundPlayers
        # Three RoundPlayers present but sitting out
        TournamentPlayer.objects.create(player=self.p1, tournament=t)
        TournamentPlayer.objects.create(player=self.p2, tournament=t)
        TournamentPlayer.objects.create(player=self.p3, tournament=t)
        TournamentPlayer.objects.create(player=self.p4, tournament=t)
        TournamentPlayer.objects.create(player=self.p5, tournament=t)
        TournamentPlayer.objects.create(player=self.p6, tournament=t)
        TournamentPlayer.objects.create(player=self.p7, tournament=t)
        TournamentPlayer.objects.create(player=self.p8, tournament=t)
        TournamentPlayer.objects.create(player=self.p9, tournament=t)
        TournamentPlayer.objects.create(player=self.p10, tournament=t)
        RoundPlayer.objects.create(player=self.p1, the_round=r)
        RoundPlayer.objects.create(player=self.p2, the_round=r)
        RoundPlayer.objects.create(player=self.p3, the_round=r)
        RoundPlayer.objects.create(player=self.p4, the_round=r)
        RoundPlayer.objects.create(player=self.p5, the_round=r)
        RoundPlayer.objects.create(player=self.p6, the_round=r)
        RoundPlayer.objects.create(player=self.p7, the_round=r)
        RoundPlayer.objects.create(player=self.p8, the_round=r)
        RoundPlayer.objects.create(player=self.p9, the_round=r)
        RoundPlayer.objects.create(player=self.p10, the_round=r)
        GamePlayer.objects.create(player=self.p1, game=g, power=self.austria)
        GamePlayer.objects.create(player=self.p3, game=g, power=self.england)
        GamePlayer.objects.create(player=self.p4, game=g, power=self.france)
        GamePlayer.objects.create(player=self.p5, game=g, power=self.germany)
        GamePlayer.objects.create(player=self.p6, game=g, power=self.italy)
        GamePlayer.objects.create(player=self.p7, game=g, power=self.russia)
        GamePlayer.objects.create(player=self.p8, game=g, power=self.turkey)

        # Initialise scores
        r.update_scores()

        CentreCount.objects.create(power=self.austria, game=g, year=1903, count=5)
        CentreCount.objects.create(power=self.england, game=g, year=1903, count=5)
        CentreCount.objects.create(power=self.france, game=g, year=1903, count=5)
        CentreCount.objects.create(power=self.germany, game=g, year=1903, count=10)
        CentreCount.objects.create(power=self.italy, game=g, year=1903, count=0)
        CentreCount.objects.create(power=self.russia, game=g, year=1903, count=5)
        CentreCount.objects.create(power=self.turkey, game=g, year=1903, count=4)

        # Calculate the scores
        g.update_scores()

        # Now we have Games, we can give sitters their score
        r.update_scores()

        # Check that we have the scores we expect
        tp1 = t.tournamentplayer_set.get(player=self.p2)
        self.assertEqual(tp1.score, 4005)

        # Now delete one RoundPlayer who's sitting out, using the delete() method
        rp = r.roundplayer_set.get(player=self.p2)
        rp.delete()

        # Validate their score
        tp1.refresh_from_db()
        self.assertEqual(tp1.score, 0)

        # This next block will only work in Django 4.1 and above,
        # where we can use signals
        if False:
            # Check that we have the scores we expect
            tp1 = t.tournamentplayer_set.get(player=self.p9)
            self.assertEqual(tp1.score, 4005)
            tp2 = t.tournamentplayer_set.get(player=self.p10)
            self.assertEqual(tp2.score, 4005)

            # Delete the other two RoundPlayers who are sitting out, using QuerySet.delete()
            qs = r.roundplayer_set.filter(score=4005)
            self.assertEqual(len(qs), 2)
            qs.delete()

            # Validate their scores
            tp1.refresh_from_db()
            self.assertEqual(tp1.score, 0)
            tp2.refresh_from_db()
            self.assertEqual(tp2.score, 0)

        # Clean up
        t.delete()


class GamePlayerTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1,
                                   scoring_system=s2,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=8, tzinfo=timezone.utc)))
        r12 = Round.objects.create(tournament=t1,
                                   scoring_system=s2,
                                   dias=True,
                                   start=r11.start + HOURS_8)

        # Add Games to r11
        g11 = Game.objects.create(name='g11',
                                  started_at=r11.start,
                                  the_round=r11,
                                  the_set=cls.set1)
        Game.objects.create(name='g12',
                                  started_at=r11.start,
                                  the_round=r11,
                                  the_set=cls.set1)
        # Add Games to r12
        g13 = Game.objects.create(name='g13',
                                  started_at=r12.start,
                                  the_round=r12,
                                  is_finished=True,
                                  the_set=cls.set1)
        Game.objects.create(name='g14',
                                  started_at=r12.start,
                                  the_round=r12,
                                  the_set=cls.set1)

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # Eliminate Italy in 1903
        CentreCount.objects.create(power=cls.austria, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.england, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1903, count=10)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1903, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1903, count=4)

        # Solo victory for Germany in 1904
        CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=18)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=0)
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
        # These two are deliberately not in any tournaments
        cls.p9 = Player.objects.create(first_name='Queenie', last_name='Radiation')
        cls.p10 = Player.objects.create(first_name='Sebastian', last_name='Twinkie')
        # The remainder are not used in this method but are available for use in tests
        cls.p11 = Player.objects.create(first_name='Ursula', last_name='Vampire')

        # Tournament.news() will call Game.news() for all games in the current round,
        # which will need a player for every country
        # TODO These should really error out with no corresponding RoundPlayer. I guess clean() is not called ?
        # Add GamePlayers to g11
        GamePlayer.objects.create(player=cls.p1, game=g11, power=cls.austria)
        GamePlayer.objects.create(player=cls.p3, game=g11, power=cls.england)
        GamePlayer.objects.create(player=cls.p4, game=g11, power=cls.france)
        GamePlayer.objects.create(player=cls.p5, game=g11, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=g11, power=cls.italy)
        GamePlayer.objects.create(player=cls.p7, game=g11, power=cls.russia)
        GamePlayer.objects.create(player=cls.p8, game=g11, power=cls.turkey)
        # Add GamePlayers to g13
        GamePlayer.objects.create(player=cls.p1, game=g13, power=cls.austria)
        GamePlayer.objects.create(player=cls.p3, game=g13, power=cls.england)
        GamePlayer.objects.create(player=cls.p4, game=g13, power=cls.france)
        GamePlayer.objects.create(player=cls.p5, game=g13, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=g13, power=cls.italy)
        GamePlayer.objects.create(player=cls.p7, game=g13, power=cls.russia)
        GamePlayer.objects.create(player=cls.p8, game=g13, power=cls.turkey)
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
        TournamentPlayer.objects.create(player=cls.p2, tournament=t1, backstabbr_username='nobody')
        TournamentPlayer.objects.create(player=cls.p3, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p5, tournament=t1, unranked=True)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t1, location='The Moon')
        TournamentPlayer.objects.create(player=cls.p8, tournament=t1)

        # Set some scores to work with
        for g in Game.objects.filter(the_round__tournament=t1):
            g.update_scores()

    # GamePlayer.team()
    def test_gameplayer_team(self):
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save()
        gp = self.p3.gameplayer_set.filter(game__the_round__tournament=t).first()
        r = gp.game.the_round
        r.is_team_round = True
        r.save()
        tm = Team.objects.create(tournament=t,
                                 name='Test team')
        tm.players.add(self.p3)
        self.assertEqual(gp.team(), tm)
        # Cleanup
        tm.delete()
        r.is_team_round = False
        r.save()
        t.team_size = None
        t.save()

    def test_gameplayer_team_non_team_round(self):
        """GamePlayer in non-team round has no team"""
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save()
        tm = Team.objects.create(tournament=t,
                                 name='Test team')
        tm.players.add(self.p3)
        gp = self.p3.gameplayer_set.filter(game__the_round__tournament=t).first()
        self.assertEqual(gp.team(), None)
        # Cleanup
        tm.delete()
        t.team_size = None
        t.save()

    def test_gameplayer_team_no_team(self):
        """GamePlayer on no team"""
        t = Tournament.objects.get(name='t1')
        t.team_size = 2
        t.save()
        gp = self.p4.gameplayer_set.filter(game__the_round__tournament=t).first()
        r = gp.game.the_round
        r.is_team_round = True
        r.save()
        tm = Team.objects.create(tournament=t,
                                 name='Test team')
        tm.players.add(self.p3)
        self.assertEqual(gp.team(), None)
        # Cleanup
        tm.delete()
        r.is_team_round = False
        r.save()
        t.team_size = None
        t.save()

    # GamePlayer.score_is_final()
    def test_gameplayer_score_is_final_game_over(self):
        g = Game.objects.filter(is_finished=True).first()
        gp = g.gameplayer_set.first()
        self.assertTrue(gp.score_is_final())

    def test_gameplayer_score_is_final_game_ongoing(self):
        # player not eliminated in a game that's still going
        g = Game.objects.filter(is_finished=False).first()
        cc = g.survivors()[0]
        gp = g.gameplayer_set.get(power=cc.power)
        self.assertFalse(gp.score_is_final())

    def test_gameplayer_score_is_final_game_eliminated(self):
        # player eliminated in a game that's still going
        g = Game.objects.filter(is_finished=False).first()
        self.assertFalse(g.the_round.game_scoring_system_obj().dead_score_can_change)
        cc = g.centrecount_set.filter(count=0).first()
        gp = g.gameplayer_set.get(power=cc.power)
        self.assertTrue(gp.score_is_final())

    # GamePlayer.is_best_country()
    def test_gameplayer_is_best_country_unranked(self):
        t = Tournament.objects.get(name='t1')
        bc = t.best_countries(whole_list=True)
        gps = bc[self.germany][0]
        # Check test setup
        for gp in gps:
            tp = gp.tournamentplayer()
            self.assertTrue(tp.unranked)
            self.assertTrue(gp.is_best_country())
        gps = bc[self.germany][-1]
        # Check test setup
        for gp in gps:
            tp = gp.tournamentplayer()
            self.assertTrue(tp.unranked)
            self.assertFalse(gp.is_best_country())

    # TODO GamePlayer.is_best_country() for unranked player when they scored
    #      best but a ranked player played the same power

    def test_gameplayer_is_best_country_score(self):
        t = Tournament.objects.get(name='t1')
        self.assertEqual(t.best_country_criterion, BestCountryCriteria.SCORE)
        bc = t.best_countries(whole_list=True)
        gps = bc[self.austria][0]
        for gp in gps:
            self.assertTrue(gp.is_best_country())
        gps = bc[self.austria][-1]
        for gp in gps:
            self.assertFalse(gp.is_best_country())

    # TODO GamePlayer.is_best_country() with criteria SCORE where two players
    #      have equal scores and dots are used to tie break

    def test_gameplayer_is_best_country_dots(self):
        t = Tournament.objects.get(name='t1')
        self.assertEqual(t.best_country_criterion, BestCountryCriteria.SCORE)
        t.best_country_criterion = BestCountryCriteria.DOTS
        t.save(update_fields=['best_country_criterion'])
        bc = t.best_countries(whole_list=True)
        gps = bc[self.austria][0]
        for gp in gps:
            self.assertTrue(gp.is_best_country())
        gps = bc[self.austria][-1]
        for gp in gps:
            self.assertFalse(gp.is_best_country())
        # Cleanup
        t.best_country_criterion = BestCountryCriteria.SCORE
        t.save(update_fields=['best_country_criterion'])

    # TODO GamePlayer.is_best_country() with criteria DOTS where two players
    #      have equal dots and scores are used to tie break

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
    def test_gameplayer_elimination_year_not_eliminated(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        gp = g.gameplayer_set.get(power=self.england)
        self.assertEqual(gp.elimination_year(), None)

    # GamePlayer.final_sc_count()
    def test_gameplayer_final_sc_count_soloer(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        gp = g.gameplayer_set.get(power=self.germany)
        self.assertEqual(gp.final_sc_count(), 18)

    def test_gameplayer_final_sc_eliminated(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        gp = g.gameplayer_set.get(power=self.italy)
        self.assertEqual(gp.final_sc_count(), 0)

    def test_gameplayer_final_sc_count_lost_to_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        gp = g.gameplayer_set.get(power=self.england)
        self.assertEqual(gp.final_sc_count(), 4)

    # GamePlayer.set_power_from_prefs()
    def test_gameplayer_set_power_from_prefs(self):
        today = date.today()
        t = Tournament(name='t5',
                       start_date=today,
                       end_date=today + HOURS_24,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=DrawSecrecy.SECRET)
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
                  start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
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
        # Clean up
        # Note that this will also delete all associated objects
        t.delete()

    # TODO GamePlayer.result_str_long()

    # TODO GamePlayer.result_str(), including without power assigned

    # GamePlayer.clean()
    def test_gameplayer_clean_player_not_in_tournament(self):
        t = Tournament.objects.get(name='t1')
        p = Player.objects.first()
        self.assertFalse(t.tournamentplayer_set.filter(player=p).exists())
        g = t.round_numbered(2).game_set.get(name='g13')
        gp = GamePlayer(player=p, game=g, power=self.austria)
        self.assertRaises(ValidationError, gp.clean)

    def test_gameplayer_clean_ok(self):
        t = Tournament.objects.get(name='t1')
        p = t.tournamentplayer_set.first().player
        g = t.round_numbered(2).game_set.get(name='g13')
        gp = GamePlayer(player=p, game=g, power=self.austria)
        gp.clean()

    # GamePlayer.__str__()
    def test_gameplayer_str_with_power(self):
        gp = GamePlayer.objects.filter(power__isnull=False).first()
        # TODO Validate result
        str(gp)

    def test_gameplayer_str_no_power(self):
        g = Game.objects.first()
        gp = GamePlayer(player=self.p2, game=g)
        # TODO Validate result
        str(gp)

    # GamePlayer.get_aar_url()
    def test_gameplayer_get_aar_url(self):
        gp = GamePlayer.objects.first()
        # TODO Validate result
        gp.get_aar_url()


class GameImageTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=8, tzinfo=timezone.utc)))

        # Add Games to r11
        Game.objects.create(name='g11',
                                  started_at=r11.start,
                                  the_round=r11,
                                  the_set=cls.set1)
        Game.objects.create(name='g12',
                                  started_at=r11.start,
                                  the_round=r11,
                                  the_set=cls.set1)

    # GameImage.turn_str()
    def test_gameimage_turn_str(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        gi = GameImage.objects.get(game=g)
        self.assertEqual(gi.turn_str(), 'S1901M')

    # GameImage constraints(full_clean())
    def test_gameimage_clean(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        gi1 = GameImage.objects.get(game=g)
        gi2 = GameImage(game=g,
                        year=1902,
                        season=Seasons.SPRING,
                        phase=Phases.ADJUSTMENTS,
                        image=gi1.image)
        self.assertRaises(ValidationError, gi2.full_clean)

    # GameImage.get_absolute_url()
    def test_game_image_get_absolute_url(self):
        gi = GameImage.objects.first()
        gi.get_absolute_url()

    # GameImage.__str__()
    def test_gameimage_str(self):
        gi = GameImage.objects.first()
        # TODO Validate result
        str(gi)


class CentreCountTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        today = date.today()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=today,
                                       end_date=today + HOURS_24,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.COUNTS)

        # Add Rounds to t1
        r = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=8, tzinfo=timezone.utc)))
        Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=r.start + HOURS_8)
        Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=r.start + HOURS_16)
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=r.start + HOURS_24)
        # Add Rounds to t3
        r31 = Round.objects.create(tournament=t3,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t3.start_date, time(hour=8, tzinfo=timezone.utc)),
                                   final_year=1907)

        # Add Games to r31
        Game.objects.create(name='g31',
                            started_at=r31.start,
                            the_round=r31,
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

        # Create some players
        # Avoid hitting the WDD by not providing a WDD id
        cls.p1 = Player.objects.create(first_name='Abbey', last_name='Brown')
        cls.p2 = Player.objects.create(first_name='Charles', last_name='Dog')
        cls.p3 = Player.objects.create(first_name='Ethel', last_name='Frankenstein')
        cls.p4 = Player.objects.create(first_name='George', last_name='Hotel')
        cls.p5 = Player.objects.create(first_name='Iris', last_name='Jackson')
        cls.p6 = Player.objects.create(first_name='Kevin', last_name='Lame')
        cls.p7 = Player.objects.create(first_name='Michelle', last_name='Nobody')

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
        # Clean up
        cc1.delete()

    def test_centrecount_clean_more_than_double(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        cc1 = CentreCount(power=self.austria, game=g, year=1902, count=5)
        cc2 = CentreCount(power=self.austria, game=g, year=1903, count=11)
        cc1.save()
        self.assertRaises(ValidationError, cc2.clean)
        # Clean up
        cc1.delete()

    # Make sure that Issue #44 hasn't re-appeared
    # We should be able to save the CentreCounts for all 7 powers for the final game year
    def test_issue_44_1(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(4)
        r = Round.objects.create(tournament=t,
                                 scoring_system='Sum of Squares',
                                 dias=True,
                                 start=r.start + HOURS_24,
                                 final_year=1910)
        g = Game.objects.create(name='g41', started_at=r.start, the_round=r, the_set=self.set1)
        # TODO Remove reliance on primary keys
        GamePlayer.objects.create(player=Player.objects.get(pk=7), game=g, power=self.austria)
        GamePlayer.objects.create(player=Player.objects.get(pk=6), game=g, power=self.england)
        GamePlayer.objects.create(player=Player.objects.get(pk=5), game=g, power=self.france)
        GamePlayer.objects.create(player=Player.objects.get(pk=4), game=g, power=self.germany)
        GamePlayer.objects.create(player=Player.objects.get(pk=3), game=g, power=self.italy)
        GamePlayer.objects.create(player=Player.objects.get(pk=2), game=g, power=self.russia)
        GamePlayer.objects.create(player=Player.objects.get(pk=1), game=g, power=self.turkey)
        cc = CentreCount(game=g, count=0, power=self.austria, year=r.final_year - 1)
        cc.save()
        cc = CentreCount(game=g, count=0, power=self.austria, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=0, power=self.england, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=9, power=self.france, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=9, power=self.germany, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=2, power=self.italy, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=7, power=self.russia, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=7, power=self.turkey, year=r.final_year)
        cc.save()
        # We no longer expect CentreCount.save() to update Game.is_finished
        self.assertFalse(g.is_finished)
        r.delete()

    # We should be able to save the CentreCounts for all 7 powers for a game with a soloer
    def test_issue_44_2(self):
        t = Tournament.objects.get(name='t1')
        r = Round.objects.create(tournament=t,
                                 scoring_system='Sum of Squares',
                                 dias=True,
                                 start=datetime.combine(t.start_date, time(hour=10, tzinfo=timezone.utc)),
                                 final_year=1910)
        g = Game.objects.create(name='g41', started_at=r.start, the_round=r, the_set=self.set1)
        # TODO Remove reliance on primary keys
        GamePlayer.objects.create(player=Player.objects.get(pk=7), game=g, power=self.austria)
        GamePlayer.objects.create(player=Player.objects.get(pk=6), game=g, power=self.england)
        GamePlayer.objects.create(player=Player.objects.get(pk=5), game=g, power=self.france)
        GamePlayer.objects.create(player=Player.objects.get(pk=4), game=g, power=self.germany)
        GamePlayer.objects.create(player=Player.objects.get(pk=3), game=g, power=self.italy)
        GamePlayer.objects.create(player=Player.objects.get(pk=2), game=g, power=self.russia)
        GamePlayer.objects.create(player=Player.objects.get(pk=1), game=g, power=self.turkey)
        cc = CentreCount(game=g, count=0, power=self.austria, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=0, power=self.england, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=7, power=self.france, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=7, power=self.germany, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=2, power=self.italy, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=18, power=self.russia, year=r.final_year)
        cc.save()
        cc = CentreCount(game=g, count=0, power=self.turkey, year=r.final_year)
        cc.save()
        # We no longer expect CentreCount.save() to update Game.is_finished
        self.assertFalse(g.is_finished)
        # Clean up
        r.delete()

    # CentreCount.__str__()
    def test_centrecount_str(self):
        sc = CentreCount.objects.first()
        # TODO Validate result
        str(sc)
