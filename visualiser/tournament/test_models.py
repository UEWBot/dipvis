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
from django.db.utils import IntegrityError
from django.test import TestCase, tag, override_settings
from django.utils import timezone

from tournament.diplomacy import GreatPower, SupplyCentre, GameSet
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, Round, Game, DrawProposal, GameImage
from tournament.models import SupplyCentreOwnership, CentreCount, Preference
from tournament.models import validate_weight, SeederBias
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
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

        #s1 = G_SCORING_SYSTEMS[0].name
        s1 = "Solo or bust"

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
        t4 = Tournament.objects.create(name='t4',
                                       start_date=timezone.now(),
                                       end_date=timezone.now(),
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       power_assignment=Tournament.PREFERENCES)

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
        cls.p12 = Player.objects.create(first_name='Wilfred', last_name='Xylophone')
        cls.p13 = Player.objects.create(first_name='Yannis', last_name='Zygote')

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

    # RScoringBest.scores() without sitting-out bonus
    def test_r_scoring_best(self):
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        now = timezone.now()
        t = Tournament.objects.create(name='Round Scoring Test',
                                      start_date=now,
                                      end_date=now,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=Tournament.SECRET)
        # Check that we got the right scoring system
        self.assertNotIn("Sitters", t.round_scoring_system)
        # One Round
        r = Round.objects.create(tournament=t,
                                 scoring_system=s,
                                 dias=False,
                                 start=t.start_date)
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
        scores = r.scores(force_recalculation=True)
        for p, s in expected_results.items():
            with self.subTest(player=p):
                self.assertEqual(scores[p], s)

        # Clean up
        t.delete()

    # RScoringBest.scores() with sitting bonus
    def test_r_scoring_best_with_bonus(self):
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        now = timezone.now()
        t = Tournament.objects.create(name='Round Scoring Test',
                                      start_date=now,
                                      end_date=now,
                                      round_scoring_system=R_SCORING_SYSTEMS[1].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=Tournament.SECRET)
        # Check that we got the right scoring system
        self.assertIn("Sitters", t.round_scoring_system)
        self.assertNotIn("once", t.round_scoring_system)
        # One Round
        r = Round.objects.create(tournament=t,
                                 scoring_system=s,
                                 dias=False,
                                 start=t.start_date)
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
        scores = r.scores(force_recalculation=True)
        for p, s in expected_results.items():
            with self.subTest(player=p):
                self.assertEqual(scores[p], s)

        # Clean up
        t.delete()

    # RScoringBest.scores() with one-off sitting bonus
    def test_r_scoring_best_with_one_bonus(self):
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        now = timezone.now()
        t = Tournament.objects.create(name='Round Scoring Test',
                                      start_date=now,
                                      end_date=now,
                                      round_scoring_system=R_SCORING_SYSTEMS[2].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=Tournament.SECRET)
        # Check that we got the right scoring system
        self.assertIn("once", t.round_scoring_system)
        # Two Rounds
        r1 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=t.start_date)
        r2 = Round.objects.create(tournament=t,
                                  scoring_system=s,
                                  dias=False,
                                  start=t.start_date + HOURS_8)
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
        scores = r2.scores(force_recalculation=True)
        for p, s in expected_results.items():
            with self.subTest(player=p):
                self.assertEqual(scores[p], s)

        # Clean up
        t.delete()

    # RScoringAll.scores()
    def test_r_scoring_all(self):
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        now = timezone.now()
        t = Tournament.objects.create(name='Round Scoring Test',
                                      start_date=now,
                                      end_date=now,
                                      round_scoring_system=R_SCORING_SYSTEMS[3].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=Tournament.SECRET)
        # Check that we got the right scoring system
        self.assertNotIn("Sitters", t.round_scoring_system)
        # One Round
        r = Round.objects.create(tournament=t,
                                 scoring_system=s,
                                 dias=False,
                                 start=t.start_date)
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
        scores = r.scores(force_recalculation=True)
        for p, s in expected_results.items():
            with self.subTest(player=p):
                self.assertEqual(scores[p], s)

        # Clean up
        t.delete()

    # RScoringBest.__str__()
    def test_rscoringbest0_str(self):
        # TODO This depends on the ordering
        r = R_SCORING_SYSTEMS[0]
        r_str = str(r)
        self.assertIn('est game score', r_str)
        self.assertNotIn('out', r_str)
        self.assertNotIn('once', r_str)

    def test_rscoringbest1_str(self):
        # TODO This depends on the ordering
        r = R_SCORING_SYSTEMS[1]
        r_str = str(r)
        self.assertIn('est game score', r_str)
        self.assertIn('out', r_str)
        self.assertNotIn('once', r_str)

    def test_rscoringbest2_str(self):
        # TODO This depends on the ordering
        r = R_SCORING_SYSTEMS[2]
        r_str = str(r)
        self.assertIn('est game score', r_str)
        self.assertIn('out', r_str)
        self.assertIn('once', r_str)

    # RScoringSum.__str__()
    def test_rscoringsum_str(self):
        # TODO This depends on the ordering
        r = R_SCORING_SYSTEMS[3]
        r_str = str(r)
        self.assertIn('ll game scores', r_str)


    # TScoringSum.__str__()
    def test_tscoringsum0_str(self):
        # TODO This depends on the ordering
        t = T_SCORING_SYSTEMS[0]
        t_str = str(t)
        self.assertIn('best 2', t_str)

    def test_tscoringsum1_str(self):
        # TODO This depends on the ordering
        t = T_SCORING_SYSTEMS[1]
        t_str = str(t)
        self.assertIn('best 3', t_str)

    def test_tscoringsum2_str(self):
        # TODO This depends on the ordering
        t = T_SCORING_SYSTEMS[2]
        t_str = str(t)
        self.assertIn('best 4', t_str)

    # TODO TScoringSum.scores_detail()

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

    def test_tournament_powers_assigned_from_prefs_true(self):
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
        for r in t.round_set.all():
            # Solo or bust gives everyone the same score (0)
            self.assertEqual(r.scoring_system, 'Solo or bust')
        # Discard the round scores
        p_and_s = t.positions_and_scores()[0]
        # The unranked player should have a special position
        self.assertEqual(p_and_s[self.p5][0], Tournament.UNRANKED)
        # As everyone else has the same score, they should all be ranked (joint) first
        for k in p_and_s:
            if k != self.p5:
                with self.subTest(k=k):
                    self.assertEqual(p_and_s[k][0], 1)

    # Tournament.store_scores()
    def test_tourney_store_scores(self):
        now = timezone.now()
        t = Tournament(name='t5',
                       start_date=now,
                       end_date=now,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=Tournament.SECRET)
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
                  start=t.start_date)
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
        t.store_scores()
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
        g.delete()
        # Note that this will also delete all RoundPlayers for the Round
        r.delete()
        # Note that this will also delete all TournamentPlayers for the Tournament
        t.delete()

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
            with self.subTest(power=gp.power):
                self.assertFalse(gp.player == self.p5)

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
        g12.the_round.save()
        round_scoring2 = g14.the_round.scoring_system
        g14.the_round.scoring_system = 'Sum of Squares'
        g14.the_round.save()
        # Ensure all players are ranked
        gp_list = list(t.tournamentplayer_set.filter(unranked=True))
        for gp in gp_list:
            gp.unranked = False
            gp.save()
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
        # Check best countries with criterion of score
        bc = t.best_countries(True)
        for power in GreatPower.objects.all():
            with self.subTest(criterion=Tournament.SCORE, power=power):
                gp1 = g12.gameplayer_set.get(power=power)
                gp2 = g14.gameplayer_set.get(power=power)
                if gp1.score > gp2.score:
                    self.assertTrue(bc[power].index(gp1) < bc[power].index(gp2))
                if gp1.score < gp2.score:
                    self.assertTrue(bc[power].index(gp1) > bc[power].index(gp2))
        # Change the Tournament to rank best countries by dot count
        t.best_country_criterion = Tournament.DOTS
        t.save()
        # Now best countries should be different
        bc = t.best_countries(True)
        for power in GreatPower.objects.all():
            with self.subTest(criterion=Tournament.DOTS, power=power):
                gp1 = g12.gameplayer_set.get(power=power)
                gp2 = g14.gameplayer_set.get(power=power)
                if gp1.final_sc_count() > gp2.final_sc_count():
                    self.assertTrue(bc[power].index(gp1) < bc[power].index(gp2))
                if gp1.final_sc_count() < gp2.final_sc_count():
                    self.assertTrue(bc[power].index(gp1) > bc[power].index(gp2))
        # Clean up
        t.best_country_criterion = Tournament.SCORE
        t.save()
        for gp in gp_list:
            gp.unranked = True
            gp.save()
        g12.the_round.scoring_system = round_scoring1
        g12.the_round.save()
        g14.the_round.scoring_system = round_scoring2
        g14.the_round.save()
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
            with self.subTest(round_number=i):
                self.assertTrue(t.round_numbered(i).is_finished() or t.round_numbered(i).in_progress(),
                                'round %d' % i)
        # All later rounds should be not in progress
        for i in range(r.number() + 1, rounds + 1):
            with self.subTest(round_number=i):
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
        t.power_assignment = Tournament.PREFERENCES
        t.save()
        tp._generate_uuid()
        self.assertIn('https://', tp.get_prefs_url())
        # Clean up
        t.power_assignment = old_pa
        t.save()

    def test_tp_get_prefs_url_no_uuid(self):
        # A TournamentPlayer without a uuid_str
        tp = TournamentPlayer.objects.filter(uuid_str='').first()
        t = tp.tournament
        old_pa = t.power_assignment
        t.power_assignment = Tournament.PREFERENCES
        t.save()
        self.assertIn('https://', tp.get_prefs_url())
        # Clean up
        t.power_assignment = old_pa
        t.save()

    # TODO TournamentPlayer.send_prefs_email()

    # TODO TournamentPlayer.get_absolute_url()

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
        self.p1.save()
        t = Tournament.objects.get(name='t4')
        self.assertEqual(t.powers_assigned_from_prefs(), True)
        tp = TournamentPlayer(tournament=t,
                              player=self.p1)
        tp.save()
        self.assertNotEqual(len(tp.uuid_str), 0)
        # Clean up
        tp.delete()
        self.p1.email = ''
        self.p1.save()

    def test_new_tp_no_set_uuid(self):
        # New TournamentPlayer in Tournament without prefs should not get uuid_str,
        # even for Player with email
        self.assertEqual(len(self.p1.email), 0)
        self.p1.email = 'example@example.com'
        self.p1.save()
        t = Tournament.objects.get(name='t3')
        self.assertEqual(t.powers_assigned_from_prefs(), False)
        tp = TournamentPlayer(tournament=t,
                              player=self.p1)
        tp.save()
        self.assertEqual(len(tp.uuid_str), 0)
        # Clean up
        tp.delete()
        self.p1.email = ''
        self.p1.save()

    def test_new_tp_copy_bs_username(self):
        # New TournamentPlayer should get backstabbr_username copied over from Player
        t = Tournament.objects.get(name='t3')
        self.assertEqual(len(self.p1.backstabbr_username), 0)
        self.p1.backstabbr_username = 'My_username'
        self.p1.save()
        tp = TournamentPlayer(tournament=t,
                              player=self.p1)
        tp.save()
        self.assertEqual(tp.backstabbr_username, self.p1.backstabbr_username)
        # Clean up
        tp.delete()
        self.p1.backstabbr_username = ''
        self.p1.save()

    def test_new_tp_override_bs_username(self):
        # Can specify different backstabbr_username for new TP
        # and Player will be updated
        t = Tournament.objects.get(name='t3')
        self.assertEqual(len(self.p1.backstabbr_username), 0)
        self.p1.backstabbr_username = 'My_username'
        self.p1.save()
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
        self.p1.save()

    def test_save_tp_leave_bs_username(self):
        # Existing TournamentPlayer should not get backstabbr_username changed
        t = Tournament.objects.get(name='t1')
        tp = t.tournamentplayer_set.get(player=self.p3)
        self.assertEqual(len(self.p3.backstabbr_username), 0)
        self.assertEqual(len(tp.backstabbr_username), 0)
        # Add a backstabbr_username to the Player
        self.p3.backstabbr_username = 'My_username'
        self.p3.save()
        # Save the TournamentPlayer
        tp.save()
        # TournamentPlayer backstabbr_username should remain the same
        self.assertEqual(len(tp.backstabbr_username), 0)
        # Clean up
        self.p3.backstabbr_username = ''
        self.p3.save()

    # TODO New TournamentPlayer should be unranked if they're a manager
    # TODO New TournamentPlayer should not be unranked if they're not a manager
    # TODO Background objects should be generated for new TournamentPlayer
    # TODO Background objects should not be generated for existing TournamentPlayer
    # TODO Existing TournamentPlayer should not have unranked cleared when saved
    # TODO Existing TournamentPlayer should not have unranked set when saved

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

    # Round uniqueness
    def test_two_rounds_same_start(self):
        # New Tournament just for this test
        s = G_SCORING_SYSTEMS[0].name
        now = timezone.now()
        t = Tournament.objects.create(name='Round Scoring Test',
                                      start_date=now,
                                      end_date=now,
                                      round_scoring_system=R_SCORING_SYSTEMS[2].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=Tournament.SECRET)
        # Check that we got the right scoring system
        self.assertIn("once", t.round_scoring_system)
        # Two Rounds
        Round.objects.create(tournament=t,
                             scoring_system=s,
                             dias=False,
                             start=t.start_date)
        self.assertRaises(IntegrityError,
                          Round.objects.create,
                          tournament=t,
                          scoring_system=s,
                          dias=False,
                          start=t.start_date)
        # Clean up
        # For some reason, this gives an error
        #t.delete()

    # Round.scores()
    def test_round_scores_invalid(self):
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=timezone.now(),
                                                      end_date=timezone.now(),
                                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                      round_scoring_system='Invalid System')
        r = Round.objects.create(tournament=t,
                                 scoring_system=G_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 start=t.start_date)
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

    # Round.store_scores()
    def test_round_store_scores(self):
        now = timezone.now()
        t = Tournament(name='t5',
                       start_date=now,
                       end_date=now,
                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                       draw_secrecy=Tournament.SECRET)
        t.save()
        # We need a round with a finished game
        r = Round(tournament=t,
                  scoring_system='Sum of Squares',
                  dias=True,
                  start=t.start_date)
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
        r.store_scores()
        for rp in r.roundplayer_set.all():
            with self.subTest(player=rp.player):
                try:
                    gp = GamePlayer.objects.filter(game=g, player=rp.player).get()
                except GamePlayer.DoesNotExist:
                    self.assertEqual(rp.score, 0.0)
                else:
                    self.assertEqual(rp.score, gp.score)
        # Clean up
        g.delete()
        r.delete()
        t.delete()

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
        t = Tournament(name='t5',
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
                  self.england : 0,
                  self.france : 0,
                  self.germany : 0,
                  self.italy : 0,
                  self.russia : 0,
                  self.turkey : 0,
              }
        # Arbitrary game
        g = Game.objects.first()
        # Add some SC ownerships for a far off year
        YEAR = 1920
        scos = []
        for k, v in test_data.items():
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
            with self.subTest(power=cc.power):
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
                  self.england : 0,
                  self.france : 0,
                  self.germany : 0,
                  self.italy : 0,
                  self.russia : 0,
                  self.turkey : 0,
              }
        # Arbitrary game
        g = Game.objects.first()
        # Add some SC ownerships for a far off year
        YEAR = 1920
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
                  self.england : 0,
                  self.france : 0,
                  self.germany : 0,
                  self.italy : 0,
                  self.russia : 0,
                  self.turkey : 0,
              }
        # Arbitrary game
        g = Game.objects.first()
        # Add some SC ownerships for a far off year
        YEAR = 1920
        scos = []
        for k, v in test_data.items():
            sco = SupplyCentreOwnership(sc=k, owner=v, year=YEAR, game=g)
            sco.save()
            scos.append(sco)
            res[v] += 1
        # Quickly check that no CentreCounts exist already
        self.assertEqual(0, g.centrecount_set.filter(year=YEAR).count())
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
        r = Round.objects.create(tournament=t,
                                 scoring_system='Invalid System',
                                 dias=True,
                                 start=t.start_date)
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
        dp = DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertIn('Vote passed ', g.result_str())
        dp.delete()

    def test_game_result_str_conceded(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.england,
                                         power_1=self.england)
        self.assertIn('conceded ', g.result_str())
        dp.delete()

    def test_game_result_str_failed_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp = DrawProposal.objects.create(game=g, year=1901, season='S', passed=False, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
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
        t = Tournament(name='t5',
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
            with self.subTest(player=gp.player):
                if gp.power == self.russia:
                    self.assertAlmostEqual(gp.score, 100.0 * 16 / 70)
                else:
                    self.assertAlmostEqual(gp.score, 100.0 * 9 / 70)
        # But not for the Round
        for rp in r.roundplayer_set.all():
            with self.subTest(player=rp.player):
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
        t = Tournament(name='t5',
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
            with self.subTest(player=gp.player):
                if gp.power == self.russia:
                    self.assertAlmostEqual(gp.score, 100.0 * 16 / 70)
                else:
                    self.assertAlmostEqual(gp.score, 100.0 * 9 / 70)
        # And for the Round
        for rp in r.roundplayer_set.all():
            with self.subTest(player=rp.player):
                if rp.player == self.p6:
                    self.assertAlmostEqual(rp.score, 100.0 * 16 / 70)
                else:
                    self.assertAlmostEqual(rp.score, 100.0 * 9 / 70)
        # And for the Tournament
        for tp in t.tournamentplayer_set.all():
            with self.subTest(player=tp.player):
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
        t = Tournament(name='t5',
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
            with self.subTest(player=gp.player):
                if gp.power == self.russia:
                    self.assertAlmostEqual(gp.score, 100.0 * 16 / 70)
                else:
                    self.assertAlmostEqual(gp.score, 100.0 * 9 / 70)
        # But not for the Round
        for rp in r.roundplayer_set.all():
            with self.subTest(player=rp.player):
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
        with self.subTest(power=self.austria):
            self.assertEqual(dp.power_is_part(self.austria), True)
        for power in [self.england, self.france, self.germany, self.italy, self.russia, self.turkey]:
            with self.subTest(power=power):
                self.assertEqual(dp.power_is_part(power), False)

    def test_draw_proposal_power_is_part_all(self):
        g = Game.objects.first()
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        for power in [self.austria, self.england, self.france, self.germany, self.italy, self.russia, self.turkey]:
            with self.subTest(power=power):
                self.assertEqual(dp.power_is_part(self.austria), True)

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
        done = g.is_finished
        dp1 = DrawProposal.objects.create(game=g, year=1901, season='F', passed=True, proposer=self.austria,
                                          power_1=self.austria, power_2=self.england, power_3=self.france,
                                          power_4=self.germany, power_5=self.italy, power_6=self.russia,
                                          power_7=self.turkey)
        dp2 = DrawProposal(game=g, year=1902, season='F', passed=True, proposer=self.austria,
                           power_1=self.austria, power_2=self.england, power_3=self.france,
                           power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertRaises(ValidationError, dp2.clean)
        # Clean up
        dp1.delete()
        g.is_finished = done
        g.save()

    def test_draw_proposal_clean_passed_not_set(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1905, season='F', proposer=self.austria,
                          power_1=self.england, power_2=self.france,
                          power_3=self.germany, power_4=self.italy, power_5=self.russia,
                          power_6=self.turkey)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_clean_passed_false(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1905, season='F', passed=False, proposer=self.austria,
                          power_1=self.england, power_2=self.france,
                          power_3=self.germany, power_4=self.russia,
                          power_5=self.turkey)
        # This one should be fine
        dp.clean()

    def test_draw_proposal_clean_passed_true(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1905, season='F', passed=True, proposer=self.austria,
                          power_1=self.england, power_2=self.france,
                          power_3=self.germany, power_4=self.russia,
                          power_5=self.turkey)
        # This one should be fine
        dp.clean()

    def test_draw_proposal_clean_votes_in_favour_seven(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal(game=g, year=1905, season='F', votes_in_favour=7, proposer=self.austria,
                          power_1=self.england, power_2=self.france,
                          power_3=self.germany, power_4=self.italy, power_5=self.russia,
                          power_6=self.turkey, power_7=self.austria)
        # This one should be fine
        dp.clean()

    def test_draw_proposal_clean_votes_in_favour_zero(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal(game=g, year=1905, season='F', votes_in_favour=0, proposer=self.austria,
                          power_1=self.england, power_2=self.france,
                          power_3=self.germany, power_4=self.italy, power_5=self.russia,
                          power_6=self.turkey, power_7=self.austria)
        # This one should be fine
        dp.clean()

    def test_draw_proposal_clean_votes_in_favour_not_set(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal(game=g, year=1905, season='F', proposer=self.austria,
                          power_1=self.england, power_2=self.france,
                          power_3=self.germany, power_4=self.italy, power_5=self.russia,
                          power_6=self.turkey, power_7=self.austria)
        self.assertRaises(ValidationError, dp.clean)

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
        print(g.final_year())
        dp = DrawProposal(game=g, year=1901, season='F', proposer=self.austria,
                          votes_in_favour=7,
                          power_1=self.england, power_2=self.france,
                          power_3=self.germany, power_4=self.italy, power_5=self.russia,
                          power_6=self.turkey, power_7=self.austria)
        self.assertRaises(ValidationError, dp.clean)
        # Clean up
        CentreCount.objects.filter(game=g, year=1901).delete()

    def test_draw_proposal_clean_votes_in_favour_multiple_successful(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp1 = DrawProposal.objects.create(game=g, year=1901, season='F', proposer=self.austria,
                                          votes_in_favour=7,
                                          power_1=self.england, power_2=self.france,
                                          power_3=self.germany, power_4=self.italy, power_5=self.russia,
                                          power_6=self.turkey, power_7=self.austria)
        self.assertTrue(dp1.passed)
        dp2 = DrawProposal(game=g, year=1902, season='F', proposer=self.austria,
                           votes_in_favour=7,
                           power_1=self.england, power_2=self.france,
                           power_3=self.germany, power_4=self.italy, power_5=self.russia,
                           power_6=self.turkey, power_7=self.austria)
        self.assertRaises(ValidationError, dp2.clean)
        dp1.delete()

    # DrawProposal.save()

    def test_draw_proposal_save_vote_passed(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        # Modify the game to not yet be finished
        g.is_finished = False
        g.save()
        dp = DrawProposal(game=g, year=1905, season='F', votes_in_favour=7, proposer=self.austria,
                          power_1=self.england, power_2=self.france,
                          power_3=self.germany, power_4=self.italy, power_5=self.russia,
                          power_6=self.turkey, power_7=self.austria)
        dp.save()
        self.assertTrue(dp.passed)
        self.assertTrue(g.is_finished)
        # Cleanup
        dp.delete()

    def test_draw_proposal_save_sets_passed_to_true(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        # Modify the game to not yet be finished
        g.is_finished = False
        g.save()
        dp = DrawProposal(game=g, year=1905, season='F', votes_in_favour=6, proposer=self.austria,
                          power_1=self.england, power_2=self.france,
                          power_3=self.germany, power_4=self.italy, power_5=self.russia,
                          power_6=self.turkey, power_7=self.austria)
        dp.save()
        self.assertFalse(dp.passed)
        self.assertFalse(g.is_finished)
        # Cleanup
        dp.delete()
        g.is_finished = True
        g.save()

    # DrawProposal.__str__()
    def test_drawproposal_str(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1901, season='F', passed=True, proposer=self.austria,
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
        now = timezone.now()
        t = Tournament(name='t5',
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

    # TODO GamePlayer.result_str()

    # GamePlayer.clean()
    def test_gameplayer_clean_player_not_in_tournament(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        gp = GamePlayer(player=Player.objects.first(),
                        game=g,
                        power=self.austria)
        self.assertRaises(ValidationError, gp.clean)

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
