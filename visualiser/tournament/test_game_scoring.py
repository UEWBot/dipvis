# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2020 Chris Brand
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
from math import floor

from django.test import TestCase

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.values.diplomacy_values import TOTAL_SCS
from tournament.game_scoring import InvalidYear, G_SCORING_SYSTEMS
from tournament.game_scoring_system_views import SimpleGameState
from tournament.models import Tournament, Round, Game, DrawProposal, CentreCount
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import DrawSecrecy, Seasons
from tournament.models import find_game_scoring_system
from tournament.tournament_game_state import TournamentGameState

HOURS_24 = timedelta(hours=24)


class GameScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        set1 = GameSet.objects.get(name='Avalon Hill')

        s1 = G_SCORING_SYSTEMS[0].name

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
                                   start=datetime.combine(t1.start_date, time(hour=12, tzinfo=timezone.utc)))
        r13 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=16, tzinfo=timezone.utc)))
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=datetime.combine(t1.start_date, time(hour=20, tzinfo=timezone.utc)))

        # Add Games to r11
        g11 = Game.objects.create(name='g11', started_at=r11.start, the_round=r11, the_set=set1)
        Game.objects.create(name='g12', started_at=r11.start, the_round=r11, the_set=set1)
        # Add Games to r12
        Game.objects.create(name='g13', started_at=r12.start, the_round=r12, is_finished=True, the_set=set1)
        Game.objects.create(name='g14', started_at=r12.start, the_round=r12, the_set=set1)
        # Add Games to r13
        Game.objects.create(name='g15', started_at=r13.start, the_round=r13, is_finished=True, the_set=set1)
        Game.objects.create(name='g16', started_at=r13.start, the_round=r13, is_finished=True, the_set=set1)

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

        CentreCount.objects.create(power=cls.austria, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.england, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1902, count=6)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=8)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1904, count=8)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1905, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1905, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1905, count=13)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1905, count=4)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1905, count=6)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1906, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1906, count=17)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1906, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1906, count=7)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1907, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1907, count=18)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1907, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1907, count=7)
        # SimpleGameStates for two Games
        cls.three_way_tie = SimpleGameState(sc_counts={cls.austria: 1,
                                                       cls.england: 10,
                                                       cls.france: 1,
                                                       cls.germany: 1,
                                                       cls.italy: 10,
                                                       cls.russia: 10,
                                                       cls.turkey: 1},
                                            final_year=1907,
                                            elimination_years={},
                                            draw=None)
        cls.three_survivors = SimpleGameState(sc_counts={cls.austria: 0,
                                                         cls.england: 17,
                                                         cls.france: 0,
                                                         cls.germany: 0,
                                                         cls.italy: 16,
                                                         cls.russia: 1,
                                                         cls.turkey: 0},
                                              final_year=1907,
                                              elimination_years={cls.austria: 1903,
                                                                 cls.france: 1907,
                                                                 cls.germany: 1905,
                                                                 cls.turkey: 1905},
                                              draw=None)

    def check_score_order(self, scores):
        """Check that the scores appear in GreatPower order when iterated through"""
        EXPECT = [p for p in GreatPower.objects.all()]
        order = [k for k in scores.keys()]
        self.assertEqual(EXPECT, order)

    def test_no_corruption(self):
        # Ensure that calls to calculate scores are independent
        # Essentially a test for issue #188
        system = find_game_scoring_system('CDiplo 80')
        scores = system.scores(self.three_way_tie)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = self.three_way_tie.dot_count(p)
            # 3 powers equal on 10 SCs, and 4 equal on 1 SC
            if sc == 1:
                self.assertEqual(s, 1)
            else:
                self.assertEqual(s, (25 + 14 + 7) / 3 + 10)
        self.assertEqual(sum(scores.values()), 80)
        scores = system.scores(self.three_survivors)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = self.three_survivors.dot_count(p)
            if sc == 17:
                self.assertEqual(s, 17 + 25)
            elif sc == 16:
                self.assertEqual(s, 16 + 14)
            elif sc == 1:
                self.assertEqual(s, 1 + 7)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 80)

    # description
    def test_description(self):
        for system in G_SCORING_SYSTEMS:
            with self.subTest(system=system.name):
                desc = system.description
                # TODO verify desc

    # dead_score_can_change() for a system
    def test_score_changes(self):
        # Compare score for eliminated power before and after a solo
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs1 = g.centrecount_set.filter(year__lte=1906)
        tgs1 = TournamentGameState(scs1)
        scs2 = g.centrecount_set.filter(year__lte=1907)
        tgs2 = TournamentGameState(scs2)
        for system in G_SCORING_SYSTEMS:
            with self.subTest(system=system.name):
                scores1 = system.scores(tgs1)
                scores2 = system.scores(tgs2)
                changes = scores1[self.france] != scores2[self.france]
                self.assertEqual(changes, system.dead_score_can_change)

    # Some tests for TournamentGameState
    def test_concession_is_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        # Add a passed draw
        dp = DrawProposal.objects.create(game=g,
                                         year=1901,
                                         season=Seasons.SPRING,
                                         passed=True,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.france)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Solo or bust')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.france:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(tgs.solo_year(), dp.year)
        # Clean up
        dp.delete()

    def test_draw_is_not_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        # Add a passed draw
        dp = DrawProposal.objects.create(game=g,
                                         year=1901,
                                         season=Seasons.SPRING,
                                         passed=True,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.france)
        dp.drawing_powers.add(self.turkey)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Solo or bust')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for s in scores.values():
            self.assertEqual(s, 0)
        self.assertIsNone(tgs.solo_year())
        # Clean up
        dp.delete()

    def test_solo_year_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        self.assertIsNone(tgs.solo_year())

    def test_dot_count_invalid_year(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        self.assertRaises(InvalidYear, tgs.dot_count, self.france, year=1899)

    def test_year_eliminated_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        self.assertIsNone(tgs.year_eliminated(self.france))

    # GScoringSolos
    def test_g_scoring_solos_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Solo or bust')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for s in scores.values():
            self.assertEqual(s, 0)
        self.check_score_order(scores)

    def test_g_scoring_solos_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Solo or bust')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)
        self.check_score_order(scores)


    # GScoringDrawSize
    def test_g_scoring_draws_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for s in scores.values():
            self.assertEqual(s, 100.0/7)
        self.assertAlmostEqual(sum(scores.values()), 100)
        self.check_score_order(scores)

    def test_g_scoring_draws_7way_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
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
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for s in scores.values():
            self.assertEqual(s, 100.0/7)
        self.assertAlmostEqual(sum(scores.values()), 100)
        self.check_score_order(scores)

    def test_g_scoring_draws_4way_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g,
                                         year=1901,
                                         season=Seasons.SPRING,
                                         passed=True,
                                         proposer=self.austria)
        dp.drawing_powers.add(self.austria)
        dp.drawing_powers.add(self.england)
        dp.drawing_powers.add(self.russia)
        dp.drawing_powers.add(self.germany)
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p in GreatPower.objects.all():
            if (p == self.austria) or (p == self.england) or (p == self.russia) or (p == self.germany):
                self.assertEqual(scores[p], 100.0/4)
            else:
                self.assertEqual(scores[p], 0.0)
        # 2 neutrals don't matter
        self.assertEqual(sum(scores.values()), 100)
        # Clean up
        dp.delete()
        self.check_score_order(scores)

    def test_g_scoring_draws_eliminations(self):
        """No draw, no solo, but with powers eliminated"""
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p in GreatPower.objects.all():
            if p == self.austria:
                self.assertEqual(scores[p], 0.0)
            else:
                self.assertEqual(scores[p], 100.0/6)
        self.assertAlmostEqual(sum(scores.values()), 100)
        self.check_score_order(scores)

    def test_g_scoring_draws_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)
        self.check_score_order(scores)

    # GScoringCDiplo
    def test_g_scoring_cdiplo_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('CDiplo 100')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sc.count == 4:
                self.assertEqual(s, 1 + 4)
            else:
                self.assertEqual(s, 1 + (38 + 14 + 7) / 4 + 5)
        # With 2 neutrals, the total of all scores should be 100-2=98
        self.assertEqual(sum(scores.values()), 100 - 2)
        self.check_score_order(scores)

    def test_g_scoring_cdiplo_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('CDiplo 100')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)
        self.check_score_order(scores)

    def test_g_scoring_cdiplo80_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('CDiplo 80')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sc.count == 4:
                self.assertEqual(s, 4)
            else:
                self.assertEqual(s, (25 + 14 + 7) / 4 + 5)
        # With 2 neutrals, the total of all scores should be 80-2=78
        self.assertEqual(sum(scores.values()), 80 - 2)
        self.check_score_order(scores)

    def test_g_scoring_cdiplo80_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('CDiplo 80')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            if sc.count == 18:
                self.assertEqual(s, 80)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 80)
        self.check_score_order(scores)

    # GScoringSumOfSquares
    def test_g_scoring_squares_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Sum of Squares')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sc.count == 4:
                self.assertEqual(s, 100.0 * 16 / 148)
            else:
                self.assertEqual(s, 100.0 * 25 / 148)
        # Total of all scores should always be very close to 100
        self.assertAlmostEqual(sum(scores.values()), 100)
        self.check_score_order(scores)

    def test_g_scoring_squares_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Sum of Squares')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)
        self.check_score_order(scores)

    # GScoringTribute
    def test_g_scoring_tribute_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Tribute')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
                if sc.count == 4:
                    self.assertEqual(s, 66 / 7 + 4)
                else:
                    self.assertEqual(s, 66 / 7 + 5)
        # Total of all scores should be 100 minus 2 (neutrals)
        self.assertAlmostEqual(sum(scores.values()), 98)
        self.check_score_order(scores)

    def test_g_scoring_tribute_tied_top(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1904)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Tribute')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 0)
                elif sc.count == 4:
                    self.assertEqual(s, 4 + 66/6 - 2)
                elif sc.count == 5:
                    self.assertEqual(s, 5 + 66/6 - 2)
                else:
                    self.assertEqual(s, 8 + 66/6 + 2 * 4 / 2)
        # Total of all scores should be 100
        self.assertAlmostEqual(sum(scores.values()), 100)
        self.check_score_order(scores)

    def test_g_scoring_tribute_no_solo_2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Tribute')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 0)
                elif sc.count == 3:
                    self.assertEqual(s, 3 + 66/6 - 7)
                elif sc.count == 4:
                    self.assertEqual(s, 4 + 66/6 - 7)
                elif sc.count == 5:
                    self.assertEqual(s, 5 + 66/6 - 7)
                elif sc.count == 6:
                    self.assertEqual(s, 6 + 66/6 - 7)
                else:
                    self.assertEqual(s, 13 + 66/6 + 7 * 5)
        # Total of all scores should be 100
        self.assertAlmostEqual(sum(scores.values()), 100)
        self.check_score_order(scores)

    def test_g_scoring_tribute_no_solo_3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Tribute')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 0)
                elif sc.count == 5:
                    self.assertEqual(s, 5 + 66/4 - 11)
                elif sc.count == 7:
                    self.assertEqual(s, 7 + 66/4 - 11)
                else:
                    self.assertEqual(s, 17 + 66/4 + 11*3)
        # Total of all scores should be 100
        self.assertAlmostEqual(sum(scores.values()), 100)
        self.check_score_order(scores)

    def test_g_scoring_tribute_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Tribute')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 18:
                    self.assertEqual(s, 100)
                else:
                    self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)
        self.check_score_order(scores)

    # GScoringHaight
    def test_g_scoring_haight_no_solo1(self):
        example_a = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 10,
                                               self.france: 9,
                                               self.germany: 8,
                                               self.italy: 5,
                                               self.russia: 0,
                                               self.turkey: 2},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.russia: 1908},
                                    draw=None)
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_a)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 171)
                elif p == self.france:
                    self.assertEqual(s, 145)
                elif p == self.germany:
                    self.assertEqual(s, 124)
                elif p == self.italy:
                    self.assertEqual(s, 83)
                elif p == self.russia:
                    self.assertEqual(s, (8 + 11))
                else:
                    # Turkey
                    self.assertEqual(s, 42)
        self.check_score_order(scores)

    def test_g_scoring_haight_no_solo2(self):
        example_b = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 17,
                                               self.france: 0,
                                               self.germany: 10,
                                               self.italy: 4,
                                               self.russia: 0,
                                               self.turkey: 3},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_b)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 271)
                elif p == self.france:
                    self.assertEqual(s, (8 + 11))
                elif p == self.germany:
                    self.assertEqual(s, 155)
                elif p == self.italy:
                    self.assertEqual(s, 84)
                elif p == self.russia:
                    self.assertEqual(s, (8 + 11))
                else:
                    # Turkey
                    self.assertEqual(s, 63)
        self.check_score_order(scores)

    def test_g_scoring_haight_no_solo3(self):
        example_c = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 11,
                                               self.france: 0,
                                               self.germany: 11,
                                               self.italy: 11,
                                               self.russia: 0,
                                               self.turkey: 1},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_c)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 154)
                elif p == self.france:
                    self.assertEqual(s, (8 + 11))
                elif p == self.germany:
                    self.assertEqual(s, 154)
                elif p == self.italy:
                    self.assertEqual(s, 154)
                elif p == self.russia:
                    self.assertEqual(s, (8 + 11))
                else:
                    # Turkey
                    self.assertEqual(s, 43)
        self.check_score_order(scores)

    def test_g_scoring_haight_no_solo4(self):
        example_d = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 12,
                                               self.france: 0,
                                               self.germany: 11,
                                               self.italy: 11,
                                               self.russia: 0,
                                               self.turkey: 0},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1907,
                                                       self.turkey: 1907},
                                    draw=None)
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_d)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 191)
                elif p == self.france:
                    self.assertEqual(s, (8 + 33))
                elif p == self.germany:
                    self.assertEqual(s, 154)
                elif p == self.italy:
                    self.assertEqual(s, 154)
                elif p == self.russia:
                    self.assertEqual(s, (7 + 11))
                else:
                    # Turkey
                    self.assertEqual(s, (7 + 11))
        self.check_score_order(scores)

    def test_g_scoring_haight_no_solo5(self):
        example_e = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 12,
                                               self.france: 0,
                                               self.germany: 10,
                                               self.italy: 10,
                                               self.russia: 0,
                                               self.turkey: 2},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_e)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 196)
                elif p == self.france:
                    self.assertEqual(s, (8 + 11))
                elif p == self.germany:
                    self.assertEqual(s, 144)
                elif p == self.italy:
                    self.assertEqual(s, 144)
                elif p == self.russia:
                    self.assertEqual(s, (8 + 11))
                else:
                    # Turkey
                    self.assertEqual(s, 53)
        self.check_score_order(scores)

    def test_g_scoring_haight_solo(self):
        example_f = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 18,
                                               self.france: 0,
                                               self.germany: 10,
                                               self.italy: 4,
                                               self.russia: 0,
                                               self.turkey: 2},
                                    final_year=1911,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        system = find_game_scoring_system('Haight v1.0')
        scores = system.scores(example_f)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 4)
                elif p == self.england:
                    self.assertEqual(s, 451)
                elif p == self.france:
                    self.assertEqual(s, 8)
                elif p == self.germany:
                    self.assertEqual(s, 50)
                elif p == self.italy:
                    self.assertEqual(s, 20)
                elif p == self.russia:
                    self.assertEqual(s, 8)
                else:
                    # Turkey
                    # Note that this differs from the document because the document
                    # assumes the game end in 1910 or earlier but I want to test the
                    # "or number of years played, if greater" part
                    self.assertEqual(s, 11)
        self.check_score_order(scores)

    # GScoringOpenTribute
    def test_g_scoring_opentribute_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('OpenTribute')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
                if sc.count == 4:
                    self.assertEqual(s, 34 + 3 * 4 - 1)
                else:
                    self.assertEqual(s, 34 + 3 * 5 + floor((1 + 1 + 1) / 4 ** 2))
        self.check_score_order(scores)

    def test_g_scoring_opentribute_tied_top(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1904)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('OpenTribute')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 0)
                elif sc.count == 4:
                    self.assertEqual(s, 34 + 3 * 4 - 4)
                elif sc.count == 5:
                    self.assertEqual(s, 34 + 3 * 5 - 3)
                else:
                    self.assertEqual(s, 34 + 3 * 8 + floor((8 + 4 + 4 + 3 + 3) / 2 ** 2))
        self.check_score_order(scores)

    def test_g_scoring_opentribute_no_solo_2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('OpenTribute')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 0)
                elif sc.count == 3:
                    self.assertEqual(s, 34 + 3 * 3 - 10)
                elif sc.count == 4:
                    self.assertEqual(s, 34 + 3 * 4 - 9)
                elif sc.count == 5:
                    self.assertEqual(s, 34 + 3 * 5 - 8)
                elif sc.count == 6:
                    self.assertEqual(s, 34 + 3 * 6 - 7)
                else:
                    self.assertEqual(s, 34 + 3 * 13 + (13 + 10 + 10 + 9 + 8 + 7))
        # 6 players alive, with a total of 34 dots. Tribute of 57, unshared
        # one power eliminated contributes tribute of 13
        self.assertAlmostEqual(sum(scores.values()), 34 * 6 + 34 * 3 - 57 + 57 + 13)
        self.check_score_order(scores)

    def test_g_scoring_opentribute_no_solo_3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('OpenTribute')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 0)
                elif sc.count == 5:
                    self.assertEqual(s, 34 + 3 * 5 - 12)
                elif sc.count == 7:
                    self.assertEqual(s, 34 + 3 * 7 - 10)
                else:
                    self.assertEqual(s, 34 + 3 * 17 + (17 + 17 + 17 + 12 + 12 + 10))
        # 4 players alive, with a total of 34 dots. Tribute of 85, unshared
        # Three powers eliminated contribute tribute of 17 each
        self.assertAlmostEqual(sum(scores.values()), 34 * 4 + 34 * 3 - 85 + 85 + 3 * 17)
        self.check_score_order(scores)

    def test_g_scoring_opentribute_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('OpenTribute')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 18:
                    self.assertEqual(s, 340)
                else:
                    self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 340)
        self.check_score_order(scores)

    # GScoringOMG
    def test_g_scoring_omg_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('OMG')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
                if sc.count == 4:
                    self.assertEqual(s, (4 * 1.5) + 9 + 0)
                else:
                    self.assertEqual(s, (5 * 1.5) + 9 + (4.5 + 3 + 1.5) / 4)
        self.check_score_order(scores)

    def test_g_scoring_omg_tied_top(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1904)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('OMG')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 0)
                elif sc.count == 4:
                    self.assertEqual(s, (4 * 1.5) + 9 + 0)
                elif sc.count == 5:
                    self.assertEqual(s, (5 * 1.5) + 9 + (1.5 + 0) / 2)
                else:
                    self.assertEqual(s, (8 * 1.5) + 9 + (4.5 + 3) / 2)
        self.check_score_order(scores)

    def test_g_scoring_omg_no_solo_2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('OMG')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 0)
                elif sc.count == 3:
                    self.assertEqual(s, ((3 * 1.5) + 9 + 0) / 2)
                elif sc.count == 4:
                    self.assertEqual(s, (4 * 1.5) + 9 + 0 - 7)
                elif sc.count == 5:
                    self.assertEqual(s, (5 * 1.5) + 9 + 1.5 - 7)
                elif sc.count == 6:
                    self.assertEqual(s, (6 * 1.5) + 9 + 3 - 7)
                else:
                    self.assertEqual(s, (13 * 1.5) + 9 + 4.5 + (7 * 3) + (6.75 * 2))
        self.check_score_order(scores)

    def test_g_scoring_omg_no_solo_3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('OMG')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 0)
                elif sc.count == 5:
                    self.assertEqual(s, ((5 * 1.5) + 9 + (1.5 + 0) / 2) / 2)
                elif sc.count == 7:
                    self.assertEqual(s, (7 * 1.5) + 9 + 3 - 10)
                else:
                    self.assertEqual(s, (17 * 1.5) + 9 + 4.5 + (10  + 8.625 * 2))
        self.check_score_order(scores)

    def test_g_scoring_omg_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('OMG')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 18:
                    self.assertEqual(s, 100)
                else:
                    self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)
        self.check_score_order(scores)


    # GScoringBangkok
    def test_g_Scoring_bangkok_no_solo1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1904)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Bangkok')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 4:
                    self.assertAlmostEqual(s, 4 + 0 + 3)
                elif sc.count == 5:
                    self.assertAlmostEqual(s, 5 + 0 + 3)
                elif sc.count == 8:
                    self.assertAlmostEqual(s, 8 + 6 + 3)
                else:
                    self.assertAlmostEqual(s, 0.9)
        self.check_score_order(scores)

    def test_g_scoring_bangkok_no_solo2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Bangkok')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 3:
                    self.assertAlmostEqual(s, 3 + 0 + 3)
                elif sc.count == 4:
                    self.assertAlmostEqual(s, 4 + 0 + 3)
                elif sc.count == 5:
                    self.assertAlmostEqual(s, 5 + 0 + 3)
                elif sc.count == 6:
                    self.assertAlmostEqual(s, 6 + 0 + 3)
                elif sc.count == 13:
                    self.assertAlmostEqual(s, 13 + 12 + 3)
                else:
                    self.assertAlmostEqual(s, 0.9)
        self.check_score_order(scores)

    def test_g_scoring_bangkok_no_solo3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Bangkok')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 5:
                    self.assertAlmostEqual(s, 5 + 0 + 3)
                elif sc.count == 7:
                    self.assertAlmostEqual(s, 7 + 0 + 3)
                elif sc.count == 17:
                    self.assertAlmostEqual(s, 17 + 12 + 3)
                else:
                    if sc.power == self.austria:
                        self.assertAlmostEqual(s, 0.9)
                    elif sc.power == self.france:
                        self.assertAlmostEqual(s, 1.5)
                    else:
                        # Italy
                        self.assertAlmostEqual(s, 1.5)
        self.check_score_order(scores)

    def test_g_scoring_bangkok_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Bangkok')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 18:
                    self.assertEqual(s, 41)
                else:
                    self.assertAlmostEqual(s, 0.5 * sc.count)
        self.check_score_order(scores)

    # GScoringManorCon
    def test_g_scoring_manorcon_no_solo1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1904)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 458)
                elif sc.count == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 458)
                elif sc.count == 8:
                    self.assertAlmostEqual(s, 100 * 112 / 458)
                else:
                    self.assertAlmostEqual(s, 0.3)
        self.check_score_order(scores)

    def test_g_scoring_manorcon_no_solo2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 3:
                    self.assertAlmostEqual(s, 100 * 37 / 512)
                elif sc.count == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 512)
                elif sc.count == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 512)
                elif sc.count == 6:
                    self.assertAlmostEqual(s, 100 * 76 / 512)
                elif sc.count == 13:
                    self.assertAlmostEqual(s, 100 * 237 / 512)
                else:
                    self.assertAlmostEqual(s, 0.3)
        self.check_score_order(scores)

    def test_g_scoring_manorcon_no_solo3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 636)
                elif sc.count == 7:
                    self.assertAlmostEqual(s, 100 * 93 / 636)
                elif sc.count == 17:
                    self.assertAlmostEqual(s, 100 * 373 / 636)
                else:
                    if sc.power == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif sc.power == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        # Italy
                        self.assertAlmostEqual(s, 0.5)
        self.check_score_order(scores)

    def test_g_scoring_manorcon_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 18:
                    self.assertEqual(s, 75)
                else:
                    if sc.power == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif sc.power == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    elif sc.power == self.italy:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        self.assertAlmostEqual(s, 0.6)
        self.check_score_order(scores)

    def test_g_scoring_manorcon2_no_solo1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1904)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Original ManorCon')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 458)
                elif sc.count == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 458)
                elif sc.count == 8:
                    self.assertAlmostEqual(s, 100 * 112 / 458)
                else:
                    self.assertAlmostEqual(s, 0.3)
        self.check_score_order(scores)

    def test_g_scoring_manorcon2_no_solo2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Original ManorCon')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 3:
                    self.assertAlmostEqual(s, 100 * 37 / 512)
                elif sc.count == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 512)
                elif sc.count == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 512)
                elif sc.count == 6:
                    self.assertAlmostEqual(s, 100 * 76 / 512)
                elif sc.count == 13:
                    self.assertAlmostEqual(s, 100 * 237 / 512)
                else:
                    self.assertAlmostEqual(s, 0.3)
        self.check_score_order(scores)

    def test_g_scoring_manorcon2_no_solo3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Original ManorCon')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 636)
                elif sc.count == 7:
                    self.assertAlmostEqual(s, 100 * 93 / 636)
                elif sc.count == 17:
                    self.assertAlmostEqual(s, 100 * 373 / 636)
                else:
                    if sc.power == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif sc.power == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        # Italy
                        self.assertAlmostEqual(s, 0.5)
        self.check_score_order(scores)

    def test_g_scoring_manorcon2_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Original ManorCon')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 18:
                    self.assertEqual(s, 100)
                else:
                    if sc.power == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif sc.power == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    elif sc.power == self.italy:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        self.assertAlmostEqual(s, 0.6)
        self.check_score_order(scores)

    def test_g_scoring_manorconv2_no_solo1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1904)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('ManorCon v2')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 442)
                elif sc.count == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 442)
                elif sc.count == 8:
                    self.assertAlmostEqual(s, 100 * 112 / 442)
                else:
                    self.assertAlmostEqual(s, 0.3)
        self.check_score_order(scores)

    def test_g_scoring_manorconv2_no_solo2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('ManorCon v2')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 3:
                    self.assertAlmostEqual(s, 100 * 37 / 496)
                elif sc.count == 4:
                    self.assertAlmostEqual(s, 100 * 48 / 496)
                elif sc.count == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 496)
                elif sc.count == 6:
                    self.assertAlmostEqual(s, 100 * 76 / 496)
                elif sc.count == 13:
                    self.assertAlmostEqual(s, 100 * 237 / 496)
                else:
                    self.assertAlmostEqual(s, 0.3)
        self.check_score_order(scores)

    def test_g_scoring_manorconv2_no_solo3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('ManorCon v2')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 5:
                    self.assertAlmostEqual(s, 100 * 61 / 588)
                elif sc.count == 7:
                    self.assertAlmostEqual(s, 100 * 93 / 588)
                elif sc.count == 17:
                    self.assertAlmostEqual(s, 100 * 373 / 588)
                else:
                    if sc.power == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif sc.power == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        # Italy
                        self.assertAlmostEqual(s, 0.5)
        self.check_score_order(scores)

    def test_g_scoring_manorconv2_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('ManorCon v2')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 18:
                    self.assertEqual(s, 100)
                else:
                    if sc.power == self.austria:
                        self.assertAlmostEqual(s, 0.3)
                    elif sc.power == self.france:
                        self.assertAlmostEqual(s, 0.5)
                    elif sc.power == self.italy:
                        self.assertAlmostEqual(s, 0.5)
                    else:
                        self.assertAlmostEqual(s, 0.6)
        self.check_score_order(scores)

    # GScoringWhipping
    def test_g_scoring_whipping_example_a(self):
        example_a = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 12,
                                               self.france: 3,
                                               self.germany: 6,
                                               self.italy: 9,
                                               self.russia: 0,
                                               self.turkey: 4},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.russia: 1908},
                                    draw=None)
        system = find_game_scoring_system('Whipping')
        scores = system.scores(example_a)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, 4)
            elif p == self.england:
                self.assertEqual(s, (120 + 12 + 24))
            elif p == self.france:
                self.assertEqual(s, (30 + 12))
            elif p == self.germany:
                self.assertEqual(s, (60 + 12))
            elif p == self.italy:
                self.assertEqual(s, (90 + 12))
            elif p == self.russia:
                self.assertEqual(s, 8)
            else:
                # Turkey
                self.assertEqual(s, (40 + 12))
        self.check_score_order(scores)

    def test_g_scoring_whipping_example_b(self):
        example_b = SimpleGameState(sc_counts={self.austria: 17,
                                               self.england: 0,
                                               self.france: 1,
                                               self.germany: 12,
                                               self.italy: 0,
                                               self.russia: 4,
                                               self.turkey: 0},
                                    final_year=1911,
                                    elimination_years={self.england: 1911,
                                                       self.italy: 1906,
                                                       self.turkey: 1905},
                                    draw=None)
        system = find_game_scoring_system('Whipping')
        scores = system.scores(example_b)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, (170 + 15 + 34))
            elif p == self.england:
                self.assertEqual(s, 11)
            elif p == self.france:
                self.assertEqual(s, (10 + 15))
            elif p == self.germany:
                self.assertEqual(s, (120 + 15))
            elif p == self.italy:
                self.assertEqual(s, 6)
            elif p == self.russia:
                self.assertEqual(s, (40 + 15))
            else:
                # Turkey
                self.assertEqual(s, 5)
        self.check_score_order(scores)

    def test_g_scoring_whipping_example_c(self):
        example_c = SimpleGameState(sc_counts={self.austria: 18,
                                               self.england: 3,
                                               self.france: 4,
                                               self.germany: 0,
                                               self.italy: 0,
                                               self.russia: 9,
                                               self.turkey: 0},
                                    final_year=1911,
                                    elimination_years={self.germany: 1908,
                                                       self.italy: 1905,
                                                       self.turkey: 1904},
                                    draw=None)
        system = find_game_scoring_system('Whipping')
        scores = system.scores(example_c)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, (340 + 60 + 68))
            elif p == self.england:
                self.assertEqual(s, 11)
            elif p == self.france:
                self.assertEqual(s, 11)
            elif p == self.germany:
                self.assertEqual(s, 8)
            elif p == self.italy:
                self.assertEqual(s, 5)
            elif p == self.russia:
                self.assertEqual(s, 11)
            else:
                # Turkey
                self.assertEqual(s, 4)
        self.check_score_order(scores)

    def test_g_scoring_whipping_example_d(self):
        example_d = SimpleGameState(sc_counts={self.austria: 4,
                                               self.england: 11,
                                               self.france: 11,
                                               self.germany: 0,
                                               self.italy: 0,
                                               self.russia: 0,
                                               self.turkey: 8},
                                    final_year=1911,
                                    elimination_years={self.germany: 1904,
                                                       self.italy: 1907,
                                                       self.russia: 1906},
                                    draw=None)
        system = find_game_scoring_system('Whipping')
        scores = system.scores(example_d)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, (40 + 15))
            elif p == self.england:
                self.assertEqual(s, (110 + 15 + 0))
            elif p == self.france:
                self.assertEqual(s, (110 + 15 + 0))
            elif p == self.germany:
                self.assertEqual(s, 4)
            elif p == self.italy:
                self.assertEqual(s, 7)
            elif p == self.russia:
                self.assertEqual(s, 6)
            else:
                # Turkey
                self.assertEqual(s, (80 + 15))
        self.check_score_order(scores)


class CDiploNamurGameScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        set1 = GameSet.objects.get(name='Avalon Hill')

        s1 = G_SCORING_SYSTEMS[0].name

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
                                   start=datetime.combine(t1.start_date, time(hour=12, tzinfo=timezone.utc)))
        r13 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=16, tzinfo=timezone.utc)))
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=datetime.combine(t1.start_date, time(hour=20, tzinfo=timezone.utc)))

        # Add Games to r11
        g11 = Game.objects.create(name='g11', started_at=r11.start, the_round=r11, the_set=set1)
        Game.objects.create(name='g12', started_at=r11.start, the_round=r11, the_set=set1)
        # Add Games to r12
        Game.objects.create(name='g13', started_at=r12.start, the_round=r12, is_finished=True, the_set=set1)
        Game.objects.create(name='g14', started_at=r12.start, the_round=r12, the_set=set1)
        # Add Games to r13
        Game.objects.create(name='g15', started_at=r13.start, the_round=r13, is_finished=True, the_set=set1)
        Game.objects.create(name='g16', started_at=r13.start, the_round=r13, is_finished=True, the_set=set1)

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

        CentreCount.objects.create(power=cls.austria, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.england, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1902, count=6)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=8)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1904, count=8)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1905, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1905, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1905, count=13)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1905, count=4)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1905, count=6)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1906, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1906, count=17)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1906, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1906, count=7)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1907, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1907, count=18)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1907, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1907, count=7)
        # SimpleGameStates for two Games
        cls.three_way_tie = SimpleGameState(sc_counts={cls.austria: 1,
                                                       cls.england: 10,
                                                       cls.france: 1,
                                                       cls.germany: 1,
                                                       cls.italy: 10,
                                                       cls.russia: 10,
                                                       cls.turkey: 1},
                                            final_year=1907,
                                            elimination_years={},
                                            draw=None)
        cls.three_survivors = SimpleGameState(sc_counts={cls.austria: 0,
                                                         cls.england: 17,
                                                         cls.france: 0,
                                                         cls.germany: 0,
                                                         cls.italy: 16,
                                                         cls.russia: 1,
                                                         cls.turkey: 0},
                                              final_year=1907,
                                              elimination_years={cls.austria: 1903,
                                                                 cls.france: 1907,
                                                                 cls.germany: 1905,
                                                                 cls.turkey: 1905},
                                              draw=None)

    def check_score_order(self, scores):
        """Check that the scores appear in GreatPower order when iterated through"""
        EXPECT = [p for p in GreatPower.objects.all()]
        order = [k for k in scores.keys()]
        self.assertEqual(EXPECT, order)

    def test_g_scoring_cdiplo_namur_no_solo1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1904)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('C-Diplo Namur')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 1)
                elif sc.count == 4:
                    self.assertEqual(s, 1 + 14)
                elif sc.count == 5:
                    self.assertEqual(s, 1 + 16 + 7/2)
                elif sc.count == 8:
                    self.assertEqual(s, 1 + 20 + (38 + 14)/2)
                else:
                    raise AssertionError(f'Unexpected SC count {sc.count}')
        self.check_score_order(scores)

    def test_g_scoring_cdiplo_namur_no_solo2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('C-Diplo Namur')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 1)
                elif sc.count == 3:
                    self.assertEqual(s, 1 + 12)
                elif sc.count == 4:
                    self.assertEqual(s, 1 + 14)
                elif sc.count == 5:
                    self.assertEqual(s, 1 + 16 + 7)
                elif sc.count == 6:
                    self.assertEqual(s, 1 + 18 + 14)
                elif sc.count == 13:
                    self.assertEqual(s, 1 + (18 + 7) + 38)
                else:
                    raise AssertionError(f'Unexpected SC count {sc.count}')
        self.check_score_order(scores)

    def test_g_scoring_cdiplo_namur_no_solo3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('C-Diplo Namur')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 1)
                elif sc.count == 5:
                    self.assertEqual(s, 1 + 16 + 7/2)
                elif sc.count == 7:
                    self.assertEqual(s, 1 + (18 + 1) + 14)
                elif sc.count == 17:
                    self.assertEqual(s, 1 + (18 + 11) + 38)
                else:
                    raise AssertionError(f'Unexpected SC count {sc.count}')
        self.check_score_order(scores)

    def test_g_scoring_cdiplo_namur_3way(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1902)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('C-Diplo Namur')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 4:
                    self.assertEqual(s, 1 + 14)
                elif sc.count == 6:
                    self.assertEqual(s, 1 + 18 + (38 + 14 + 7)/3)
                else:
                    raise AssertionError(f'Unexpected SC count {sc.count}')
        self.check_score_order(scores)

    def test_g_scoring_cdiplo_namur_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('C-Diplo Namur')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 18:
                    self.assertEqual(s, 85)
                else:
                    self.assertEqual(s, 0)
        self.check_score_order(scores)


class WorldClassicGameScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        set1 = GameSet.objects.get(name='Avalon Hill')

        s1 = G_SCORING_SYSTEMS[0].name

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
                                   start=datetime.combine(t1.start_date, time(hour=12, tzinfo=timezone.utc)))
        r13 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=16, tzinfo=timezone.utc)))
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=datetime.combine(t1.start_date, time(hour=20, tzinfo=timezone.utc)))

        # Add Games to r11
        g11 = Game.objects.create(name='g11', started_at=r11.start, the_round=r11, the_set=set1)
        Game.objects.create(name='g12', started_at=r11.start, the_round=r11, the_set=set1)
        # Add Games to r12
        Game.objects.create(name='g13', started_at=r12.start, the_round=r12, is_finished=True, the_set=set1)
        Game.objects.create(name='g14', started_at=r12.start, the_round=r12, the_set=set1)
        # Add Games to r13
        Game.objects.create(name='g15', started_at=r13.start, the_round=r13, is_finished=True, the_set=set1)
        Game.objects.create(name='g16', started_at=r13.start, the_round=r13, is_finished=True, the_set=set1)

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

        CentreCount.objects.create(power=cls.austria, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.england, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1902, count=6)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=8)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1904, count=8)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1905, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1905, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1905, count=13)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1905, count=4)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1905, count=6)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1906, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1906, count=17)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1906, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1906, count=7)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1907, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1907, count=18)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1907, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1907, count=7)
        # SimpleGameStates for two Games
        cls.three_way_tie = SimpleGameState(sc_counts={cls.austria: 1,
                                                       cls.england: 10,
                                                       cls.france: 1,
                                                       cls.germany: 1,
                                                       cls.italy: 10,
                                                       cls.russia: 10,
                                                       cls.turkey: 1},
                                            final_year=1907,
                                            elimination_years={},
                                            draw=None)
        cls.three_survivors = SimpleGameState(sc_counts={cls.austria: 0,
                                                         cls.england: 17,
                                                         cls.france: 0,
                                                         cls.germany: 0,
                                                         cls.italy: 16,
                                                         cls.russia: 1,
                                                         cls.turkey: 0},
                                              final_year=1907,
                                              elimination_years={cls.austria: 1903,
                                                                 cls.france: 1907,
                                                                 cls.germany: 1905,
                                                                 cls.turkey: 1905},
                                              draw=None)

    def check_score_order(self, scores):
        """Check that the scores appear in GreatPower order when iterated through"""
        EXPECT = [p for p in GreatPower.objects.all()]
        order = [k for k in scores.keys()]
        self.assertEqual(EXPECT, order)

    def test_g_scoring_world_classic_no_solo1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1904)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('World Classic')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 3)
                elif sc.count == 8:
                    self.assertEqual(s, 30 + 10 * sc.count + 48/2)
                else:
                    self.assertEqual(s, 30 + 10 * sc.count)
        self.check_score_order(scores)

    def test_g_scoring_world_classic_no_solo2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('World Classic')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    self.assertEqual(s, 3)
                elif sc.count == 13:
                    self.assertEqual(s, 30 + 10 * sc.count + 48)
                else:
                    self.assertEqual(s, 30 + 10 * sc.count)
        self.check_score_order(scores)

    def test_g_scoring_world_classic_no_solo3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('World Classic')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 0:
                    if sc.power == self.austria:
                        self.assertEqual(s, 3)
                    else:
                        self.assertEqual(s, 5)
                elif sc.count == 17:
                    self.assertEqual(s, 30 + 10 * sc.count + 48)
                else:
                    self.assertEqual(s, 30 + 10 * sc.count)
        self.check_score_order(scores)

    def test_g_scoring_world_classic_3way(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1902)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('World Classic')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 6:
                    self.assertEqual(s, 30 + 10 * sc.count + 48/3)
                else:
                    self.assertEqual(s, 30 + 10 * sc.count)
        self.check_score_order(scores)

    def test_g_scoring_summer_classic_3way(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1902)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Summer Classic')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 6:
                    self.assertEqual(s, 30 + 10 * sc.count)
                else:
                    self.assertEqual(s, 30 + 10 * sc.count)
        self.check_score_order(scores)

    def test_g_scoring_world_classic_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('World Classic')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 18:
                    self.assertEqual(s, 420)
                else:
                    if sc.power == self.austria:
                        self.assertEqual(s, 3)
                    elif sc.power == self.france:
                        self.assertEqual(s, 5)
                    elif sc.power == self.italy:
                        self.assertEqual(s, 5)
                    else:
                        self.assertEqual(s, 6)
        self.check_score_order(scores)


class CarnageGameScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        set1 = GameSet.objects.get(name='Avalon Hill')

        s1 = G_SCORING_SYSTEMS[0].name

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
                                   start=datetime.combine(t1.start_date, time(hour=12, tzinfo=timezone.utc)))
        r13 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=16, tzinfo=timezone.utc)))
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=datetime.combine(t1.start_date, time(hour=20, tzinfo=timezone.utc)))

        # Add Games to r11
        g11 = Game.objects.create(name='g11', started_at=r11.start, the_round=r11, the_set=set1)
        Game.objects.create(name='g12', started_at=r11.start, the_round=r11, the_set=set1)
        # Add Games to r12
        Game.objects.create(name='g13', started_at=r12.start, the_round=r12, is_finished=True, the_set=set1)
        Game.objects.create(name='g14', started_at=r12.start, the_round=r12, the_set=set1)
        # Add Games to r13
        Game.objects.create(name='g15', started_at=r13.start, the_round=r13, is_finished=True, the_set=set1)
        Game.objects.create(name='g16', started_at=r13.start, the_round=r13, is_finished=True, the_set=set1)

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

        CentreCount.objects.create(power=cls.austria, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.england, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1902, count=6)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=8)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1904, count=8)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1905, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1905, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1905, count=13)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1905, count=4)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1905, count=6)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1906, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1906, count=17)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1906, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1906, count=7)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1907, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1907, count=18)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1907, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1907, count=7)
        # SimpleGameStates for two Games
        cls.three_way_tie = SimpleGameState(sc_counts={cls.austria: 1,
                                                       cls.england: 10,
                                                       cls.france: 1,
                                                       cls.germany: 1,
                                                       cls.italy: 10,
                                                       cls.russia: 10,
                                                       cls.turkey: 1},
                                            final_year=1907,
                                            elimination_years={},
                                            draw=None)
        cls.three_survivors = SimpleGameState(sc_counts={cls.austria: 0,
                                                         cls.england: 17,
                                                         cls.france: 0,
                                                         cls.germany: 0,
                                                         cls.italy: 16,
                                                         cls.russia: 1,
                                                         cls.turkey: 0},
                                              final_year=1907,
                                              elimination_years={cls.austria: 1903,
                                                                 cls.france: 1907,
                                                                 cls.germany: 1905,
                                                                 cls.turkey: 1905},
                                              draw=None)

    def check_score_order(self, scores):
        """Check that the scores appear in GreatPower order when iterated through"""
        EXPECT = [p for p in GreatPower.objects.all()]
        order = [k for k in scores.keys()]
        self.assertEqual(EXPECT, order)

    # GScoringCarnage (with dead equal)
    def test_g_scoring_carnage1_simple(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sc.count == 4:
                self.assertEqual(s, (3000 + 2000 + 1000) / 3 + sc.count)
            else:
                self.assertEqual(s, (7000 + 6000 + 5000 + 4000) / 4 + sc.count)
        # 2 SCs are still neutral
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS - 2)
        self.check_score_order(scores)

    def test_g_scoring_carnage1_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            if sc.count == 18:
                self.assertEqual(s, 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        self.check_score_order(scores)

    def test_g_scoring_carnage1_eliminations(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            # 1 at 17, 1 at 7, 2 at 5, and 3 eliminated
            if sc.count == 17:
                self.assertEqual(s, 7000 + sc.count)
            elif sc.count == 7:
                self.assertEqual(s, 6000 + sc.count)
            elif sc.count == 5:
                self.assertEqual(s, (5000 + 4000) / 2 + sc.count)
            else:
                self.assertEqual(s, (3000 + 2000 + 1000) / 3 + sc.count)
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        self.check_score_order(scores)

    # Carnage with elimination order
    def test_g_scoring_carnage2_simple(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Carnage with elimination order')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sc.count == 4:
                self.assertEqual(s, (3000 + 2000 + 1000) / 3 + sc.count)
            else:
                self.assertEqual(s, (7000 + 6000 + 5000 + 4000) / 4 + sc.count)
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS - 2)
        self.check_score_order(scores)

    def test_g_scoring_carnage2_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Carnage with elimination order')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            if sc.count == 18:
                self.assertEqual(s, 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        self.check_score_order(scores)

    def test_g_scoring_carnage2_eliminations(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Carnage with elimination order')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            # 1 at 17, 1 at 7, 2 at 5, and 3 eliminated
            if sc.count == 17:
                self.assertEqual(s, 7000 + sc.count)
            elif sc.count == 7:
                self.assertEqual(s, 6000 + sc.count)
            elif sc.count == 5:
                self.assertEqual(s, (5000 + 4000) / 2 + sc.count)
            else:
                # Austria died in 1905, France and Italy in 1906
                if p in [self.france, self.italy]:
                    self.assertEqual(s, (3000 + 2000) / 2 + sc.count)
                else:
                    self.assertEqual(s, 1000 + sc.count)
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        self.check_score_order(scores)

    # Carnage 2023 (elimination order and leader gap bonus)
    def test_g_scoring_carnage2023_simple(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Carnage 2023')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sc.count == 4:
                self.assertEqual(s, (3000 + 2000 + 1000) / 3 + sc.count)
            else:
                self.assertEqual(s, (7000 + 6000 + 5000 + 4000) / 4 + sc.count)
        # With tied lead, we know the total score
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS - 2)
        self.check_score_order(scores)

    def test_g_scoring_carnage2023_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Carnage 2023')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            if sc.count == 18:
                self.assertEqual(s, 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
            else:
                self.assertEqual(s, 0)
        # With a solo, we know the total score
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        self.check_score_order(scores)

    def test_g_scoring_carnage2023_eliminations(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Carnage 2023')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.filter(power=p).last()
            # 1 at 17, 1 at 7, 2 at 5, and 3 eliminated
            if sc.count == 17:
                # Bonus 300 points per dot ahead of second place
                self.assertEqual(s, 7000 + sc.count + (17 - 7) * 300)
            elif sc.count == 7:
                self.assertEqual(s, 6000 + sc.count)
            elif sc.count == 5:
                self.assertEqual(s, (5000 + 4000) / 2 + sc.count)
            else:
                # Austria died in 1905, France and Italy in 1906
                if p in [self.france, self.italy]:
                    self.assertEqual(s, (3000 + 2000) / 2 + sc.count)
                else:
                    self.assertEqual(s, 1000 + sc.count)
        self.check_score_order(scores)
        # Total score now varies depending on the lead the leader has

    # GScoringCentreCarnage
    def test_g_scoring_centrecarnage_1(self):
        # There used to be an "example 1" and "example 2" in the doc, but no more :-(
        example_1 = SimpleGameState(sc_counts={self.austria: 11,
                                               self.england: 10,
                                               self.france: 8,
                                               self.germany: 2,
                                               self.italy: 2,
                                               self.russia: 1,
                                               self.turkey: 0},
                                    final_year=1908,
                                    elimination_years={self.turkey: 1904},
                                    draw=None)
        system = find_game_scoring_system('Center-count Carnage')
        scores = system.scores(example_1)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, 11 * 500 + 7007)
            elif p == self.england:
                self.assertEqual(s, 10 * 500 + 6006)
            elif p == self.france:
                self.assertEqual(s, 8 * 500 + 5005)
            elif p == self.germany:
                self.assertEqual(s,  2 * 500 + (4004 + 3003) / 2)
            elif p == self.italy:
                self.assertEqual(s,  2 * 500 + (4004 + 3003) / 2)
            elif p == self.russia:
                self.assertEqual(s, 1 * 500 + 2002)
            else:
                # Turkey:
                self.assertEqual(s, 1001)
        self.check_score_order(scores)

    def test_g_scoring_centrecarnage_2(self):
        # There used to be an "example 1" and "example 2" in the doc, but no more :-(
        example_2 = SimpleGameState(sc_counts={self.austria: 13,
                                               self.england: 7,
                                               self.france: 5,
                                               self.germany: 5,
                                               self.italy: 4,
                                               self.russia: 0,
                                               self.turkey: 0},
                                    final_year=1908,
                                    elimination_years={self.russia: 1905,
                                                       self.turkey: 1904},
                                    draw=None)
        system = find_game_scoring_system('Center-count Carnage')
        scores = system.scores(example_2)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            if p == self.austria:
                self.assertEqual(s, 13 * 500 + 7007)
            elif p == self.england:
                self.assertEqual(s, 7 * 500 + 6006)
            elif p == self.france:
                self.assertEqual(s, 5 * 500 + (5005 + 4004) / 2)
            elif p == self.germany:
                self.assertEqual(s, 5 * 500 + (5005 + 4004) / 2)
            elif p == self.italy:
                self.assertEqual(s, 4 * 500 + 3003)
            elif p == self.russia:
                self.assertEqual(s, 2002)
            else:
                # Turkey:
                self.assertEqual(s, 1001)
        self.check_score_order(scores)

# GScoringDetour09
class Detour09GameScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')

        s1 = G_SCORING_SYSTEMS[0].name

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
        g11 = Game.objects.create(name='g11', started_at=r11.start, the_round=r11, the_set=cls.set1)

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

        CentreCount.objects.create(power=cls.austria, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.england, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1902, count=6)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=8)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1904, count=8)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1905, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1905, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1905, count=13)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1905, count=4)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1905, count=6)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1909, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1909, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1909, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1909, count=17)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1909, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1909, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1909, count=7)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1910, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1910, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1910, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1910, count=18)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1910, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1910, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1910, count=7)

    def check_score_order(self, scores):
        """Check that the scores appear in GreatPower order when iterated through"""
        EXPECT = [p for p in GreatPower.objects.all()]
        order = [k for k in scores.keys()]
        self.assertEqual(EXPECT, order)

    def test_g_scoring_detour09_no_solo1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1904)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Detour09')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 4:
                    # 4+2+0+0=6
                    self.assertAlmostEqual(s, 100 * 6 / (6+6+8+8+13+13))
                elif sc.count == 5:
                    # 5+2+0+1=8
                    self.assertAlmostEqual(s, 100 * 8 / (6+6+8+8+13+13))
                elif sc.count == 8:
                    # 8+2+0+3=13
                    self.assertAlmostEqual(s, 100 * 13 / (6+6+8+8+13+13))
                else:
                    self.assertAlmostEqual(s, 0.75)
        self.check_score_order(scores)

    def test_g_scoring_detour09_no_solo2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Detour09')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 3:
                    # 3+2+0+0=5
                    self.assertAlmostEqual(s, 100 * 5 / (5+5+7+9+11+26))
                elif sc.count == 4:
                    # 4+2+0+1=7
                    self.assertAlmostEqual(s, 100 * 7 / (5+5+7+9+11+26))
                elif sc.count == 5:
                    # 5+2+0+2=9
                    self.assertAlmostEqual(s, 100 * 9 / (5+5+7+9+11+26))
                elif sc.count == 6:
                    # 6+2+0+3=11
                    self.assertAlmostEqual(s, 100 * 11 / (5+5+7+9+11+26))
                elif sc.count == 13:
                    # 13+2+7+4=26
                    self.assertAlmostEqual(s, 100 * 26 / (5+5+7+9+11+26))
                else:
                    self.assertAlmostEqual(s, 0.75)
        self.check_score_order(scores)

    def test_g_scoring_detour09_no_solo3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1909)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Detour09')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 5:
                    # 5+2+0+1=8
                    self.assertAlmostEqual(s, 100 * 8 / (8+8+12+33))
                elif sc.count == 7:
                    # 7+2+0+3=12
                    self.assertAlmostEqual(s, 100 * 12 / (8+8+12+33))
                elif sc.count == 17:
                    # 17+2+10+4=33
                    self.assertAlmostEqual(s, 100 * 33 / (8+8+12+33))
                else:
                    if sc.power == self.austria:
                        self.assertAlmostEqual(s, 0.75)
                    elif sc.power == self.france:
                        self.assertAlmostEqual(s, 2.00)
                    else:
                        # Italy
                        self.assertAlmostEqual(s, 2.00)
        self.check_score_order(scores)

    def test_g_scoring_detour09_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1910)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Detour09')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 18:
                    self.assertEqual(s, 110)
                else:
                    if sc.power == self.austria:
                        self.assertAlmostEqual(s, 0.75)
                    else:
                        # Suvival bonus is capped at 2.0
                        self.assertAlmostEqual(s, 2.00)
        self.check_score_order(scores)

    def test_g_scoring_detour09_3_equal_top(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1902)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Detour09')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 4:
                    # 4+2+0+0=6
                    self.assertAlmostEqual(s, 100 * 6 / (6+6+6+6++10+10+10))
                else:
                    # sc.count == 6
                    # 6+2+0+2=10
                    self.assertAlmostEqual(s, 100 * 10 / (6+6+6+6+10+10+10))
        self.check_score_order(scores)

    def test_g_scoring_detour09_4_equal_top(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Detour09')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 4:
                    # 4+2+0+0=6
                    self.assertAlmostEqual(s, 100 * 6 / (6+6+6+8+8+8+8))
                else:
                    # sc.count == 5
                    # 5+2+0+1=8
                    self.assertAlmostEqual(s, 100 * 8 / (6+6+6+8+8+8+8))
        self.check_score_order(scores)

    def test_g_scoring_detour09_2_equal_below_top(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(1)
        g = Game.objects.create(name='g12', started_at=r.start, the_round=r, the_set=self.set1)
        CentreCount.objects.create(power=self.austria, game=g, year=1907, count=2)
        CentreCount.objects.create(power=self.england, game=g, year=1907, count=3)
        CentreCount.objects.create(power=self.france, game=g, year=1907, count=4)
        CentreCount.objects.create(power=self.germany, game=g, year=1907, count=10)
        CentreCount.objects.create(power=self.italy, game=g, year=1907, count=4)
        CentreCount.objects.create(power=self.russia, game=g, year=1907, count=5)
        CentreCount.objects.create(power=self.turkey, game=g, year=1907, count=6)
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Detour09')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 10:
                    # 1st
                    # 10+2+4+4=20
                    self.assertAlmostEqual(s, 100 * 20 / (20+11+9+6+6+5+4))
                elif sc.count == 6:
                    # 2nd
                    # 6+2+3=11
                    self.assertAlmostEqual(s, 100 * 11 / (20+11+9+6+6+5+4))
                elif sc.count == 5:
                    # 3rd
                    # 5+2+2=9
                    self.assertAlmostEqual(s, 100 * 9 / (20+11+9+6+6+5+4))
                elif sc.count == 4:
                    # Joint 4th
                    # 4+2=6
                    self.assertAlmostEqual(s, 100 * 6 / (20+11+9+6+6+5+4))
                elif sc.count == 3:
                    # 6th
                    # 3+2=5
                    self.assertAlmostEqual(s, 100 * 5 / (20+11+9+6+6+5+4))
                else:
                    # 7th
                    # 2+2=4
                    self.assertAlmostEqual(s, 100 * 4 / (20+11+9+6+6+5+4))
        self.check_score_order(scores)

    def test_g_scoring_detour09_3_equal_below_top(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(1)
        g = Game.objects.create(name='g12', started_at=r.start, the_round=r, the_set=self.set1)
        CentreCount.objects.create(power=self.austria, game=g, year=1907, count=2)
        CentreCount.objects.create(power=self.england, game=g, year=1907, count=3)
        CentreCount.objects.create(power=self.france, game=g, year=1907, count=4)
        CentreCount.objects.create(power=self.germany, game=g, year=1907, count=10)
        CentreCount.objects.create(power=self.italy, game=g, year=1907, count=4)
        CentreCount.objects.create(power=self.russia, game=g, year=1907, count=4)
        CentreCount.objects.create(power=self.turkey, game=g, year=1907, count=7)
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Detour09')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 10:
                    # 1st
                    # 10+2+3+4=19
                    self.assertAlmostEqual(s, 100 * 19 / (19+12+6+6+6+5+4))
                elif sc.count == 7:
                    # 2nd
                    # 7+2+3=12
                    self.assertAlmostEqual(s, 100 * 12 / (19+12+6+6+6+5+4))
                elif sc.count == 4:
                    # Joint 3rd
                    # 4+2=6
                    self.assertAlmostEqual(s, 100 * 6 / (19+12+6+6+6+5+4))
                elif sc.count == 3:
                    # 6th
                    # 3+2=5
                    self.assertAlmostEqual(s, 100 * 5 / (19+12+6+6+6+5+4))
                else:
                    # 7th
                    # 2+2=4
                    self.assertAlmostEqual(s, 100 * 4 / (19+12+6+6+6+5+4))
        self.check_score_order(scores)


# GScoringRankedClassic
class RankedClassicGameScoringTests(TestCase):
    fixtures = ['game_sets.json']

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

    def check_score_order(self, scores):
        """Check that the scores appear in GreatPower order when iterated through"""
        EXPECT = [p for p in GreatPower.objects.all()]
        order = [k for k in scores.keys()]
        self.assertEqual(EXPECT, order)

    def test_g_scoring_rankedclassic_no_solo1(self):
        example_a = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 10,
                                               self.france: 9,
                                               self.germany: 8,
                                               self.italy: 5,
                                               self.russia: 0,
                                               self.turkey: 2},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.russia: 1908},
                                    draw=None)
        system = find_game_scoring_system('Ranked Classic')
        scores = system.scores(example_a)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 3)
                elif p == self.england:
                    self.assertEqual(s, 30 + 10 * 10 + 200)
                elif p == self.france:
                    self.assertEqual(s, 30 + 9 * 10 + 90)
                elif p == self.germany:
                    self.assertEqual(s, 30 + 8 * 10 + 60)
                elif p == self.italy:
                    self.assertEqual(s, 30 + 5 * 10 + 40)
                elif p == self.russia:
                    self.assertEqual(s, 7)
                else:
                    # Turkey
                    self.assertEqual(s, 30 + 2 * 10 + 30)
        self.check_score_order(scores)

    def test_g_scoring_rankedclassic_no_solo2(self):
        example_b = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 17,
                                               self.france: 0,
                                               self.germany: 10,
                                               self.italy: 4,
                                               self.russia: 0,
                                               self.turkey: 3},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        system = find_game_scoring_system('Ranked Classic')
        scores = system.scores(example_b)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 3)
                elif p == self.england:
                    self.assertEqual(s, 30 + 17 * 10 + 200)
                elif p == self.france:
                    self.assertEqual(s, 7)
                elif p == self.germany:
                    self.assertEqual(s, 30 + 10 * 10 + 90)
                elif p == self.italy:
                    self.assertEqual(s, 30 + 4 * 10 + 60)
                elif p == self.russia:
                    self.assertEqual(s, 7)
                else:
                    # Turkey
                    self.assertEqual(s, 30 + 3 * 10 + 40)
        self.check_score_order(scores)

    def test_g_scoring_rankedclassic_no_solo3(self):
        example_c = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 11,
                                               self.france: 0,
                                               self.germany: 11,
                                               self.italy: 11,
                                               self.russia: 0,
                                               self.turkey: 1},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        system = find_game_scoring_system('Ranked Classic')
        scores = system.scores(example_c)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 3)
                elif p == self.england:
                    self.assertEqual(s, 30 + 11 * 10 + 60)
                elif p == self.france:
                    self.assertEqual(s, 7)
                elif p == self.germany:
                    self.assertEqual(s, 30 + 11 * 10 + 60)
                elif p == self.italy:
                    self.assertEqual(s, 30 + 11 * 10 + 60)
                elif p == self.russia:
                    self.assertEqual(s, 7)
                else:
                    # Turkey
                    self.assertEqual(s, 30 + 1 * 10 + 40)
        self.check_score_order(scores)

    def test_g_scoring_rankedclassic_no_solo4(self):
        example_d = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 12,
                                               self.france: 0,
                                               self.germany: 11,
                                               self.italy: 11,
                                               self.russia: 0,
                                               self.turkey: 0},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1907,
                                                       self.turkey: 1907},
                                    draw=None)
        system = find_game_scoring_system('Ranked Classic')
        scores = system.scores(example_d)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 3)
                elif p == self.england:
                    self.assertEqual(s, 30 + 12 * 10 + 200)
                elif p == self.france:
                    self.assertEqual(s, 7)
                elif p == self.germany:
                    self.assertEqual(s, 30 + 11 * 10 + 70)
                elif p == self.italy:
                    self.assertEqual(s, 30 + 11 * 10 + 70)
                elif p == self.russia:
                    self.assertEqual(s, 6)
                else:
                    # Turkey
                    self.assertEqual(s, 6)
        self.check_score_order(scores)

    def test_g_scoring_rankedclassic_no_solo5(self):
        example_e = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 12,
                                               self.france: 0,
                                               self.germany: 10,
                                               self.italy: 10,
                                               self.russia: 0,
                                               self.turkey: 2},
                                    final_year=1908,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        system = find_game_scoring_system('Ranked Classic')
        scores = system.scores(example_e)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 3)
                elif p == self.england:
                    self.assertEqual(s, 30 + 12 * 10 + 200)
                elif p == self.france:
                    self.assertEqual(s, 7)
                elif p == self.germany:
                    self.assertEqual(s, 30 + 10 * 10 + 70)
                elif p == self.italy:
                    self.assertEqual(s, 30 + 10 * 10 + 70)
                elif p == self.russia:
                    self.assertEqual(s, 7)
                else:
                    # Turkey
                    self.assertEqual(s, 30 + 2 * 10 + 40)
        self.check_score_order(scores)

    def test_g_scoring_rankedclassic_solo(self):
        example_f = SimpleGameState(sc_counts={self.austria: 0,
                                               self.england: 18,
                                               self.france: 0,
                                               self.germany: 10,
                                               self.italy: 4,
                                               self.russia: 0,
                                               self.turkey: 2},
                                    final_year=1911,
                                    elimination_years={self.austria: 1904,
                                                       self.france: 1908,
                                                       self.russia: 1908},
                                    draw=None)
        system = find_game_scoring_system('Ranked Classic')
        scores = system.scores(example_f)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                if p == self.austria:
                    self.assertEqual(s, 3)
                elif p == self.england:
                    self.assertEqual(s, 550)
                elif p == self.france:
                    self.assertEqual(s, 7)
                elif p == self.germany:
                    self.assertEqual(s, 10)
                elif p == self.italy:
                    self.assertEqual(s, 10)
                elif p == self.russia:
                    self.assertEqual(s, 7)
                else:
                    # Turkey
                    self.assertEqual(s, 10)
        self.check_score_order(scores)

# GScoringMaxonian
class MaxonianGameScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        set1 = GameSet.objects.get(name='Avalon Hill')

        s1 = G_SCORING_SYSTEMS[0].name

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
        g11 = Game.objects.create(name='g11', started_at=r11.start, the_round=r11, the_set=set1)

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

        CentreCount.objects.create(power=cls.austria, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.england, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1902, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1902, count=6)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1902, count=6)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=8)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1904, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1904, count=8)

        CentreCount.objects.create(power=cls.austria, game=g11, year=1905, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1905, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1905, count=13)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1905, count=3)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1905, count=4)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1905, count=6)

        # Two powers over the bonus threshold
        CentreCount.objects.create(power=cls.austria, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1906, count=2)
        CentreCount.objects.create(power=cls.france, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1906, count=17)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1906, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1906, count=1)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1906, count=14)

        # Two powers over the bonus threshold
        CentreCount.objects.create(power=cls.austria, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1907, count=1)
        CentreCount.objects.create(power=cls.france, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1907, count=18)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1907, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1907, count=1)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1907, count=14)

    def check_score_order(self, scores):
        """Check that the scores appear in GreatPower order when iterated through"""
        EXPECT = [p for p in GreatPower.objects.all()]
        order = [k for k in scores.keys()]
        self.assertEqual(EXPECT, order)

    def test_g_scoring_maxonian_no_solo1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1904)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.power == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif sc.power == self.england:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                elif sc.power == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif sc.power == self.germany:
                    # 1st
                    self.assertAlmostEqual(s, 7)
                elif sc.power == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif sc.power == self.russia:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                else:
                    # 2nd
                    self.assertAlmostEqual(s, 6)
        self.check_score_order(scores)

    def test_g_scoring_maxonian_no_solo2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1905)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.power == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif sc.power == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif sc.power == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif sc.power == self.germany:
                    # 1st
                    self.assertAlmostEqual(s, 7)
                elif sc.power == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif sc.power == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd
                    self.assertAlmostEqual(s, 6)
        self.check_score_order(scores)

    def test_g_scoring_maxonian_no_solo3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.power == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif sc.power == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif sc.power == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif sc.power == self.germany:
                    # 1st, 4 over threshold
                    self.assertAlmostEqual(s, 7+4)
                elif sc.power == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif sc.power == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd, 1 over threshold
                    self.assertAlmostEqual(s, 6+1)
        self.check_score_order(scores)

    def test_g_scoring_7eleven_no_solo3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1906)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('7Eleven')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.power == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif sc.power == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif sc.power == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif sc.power == self.germany:
                    # 1st, 6 over threshold
                    self.assertAlmostEqual(s, 7+6)
                elif sc.power == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif sc.power == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd, 3 over threshold
                    self.assertAlmostEqual(s, 6+3)
        self.check_score_order(scores)

    def test_g_scoring_maxonian_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1907)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.power == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif sc.power == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif sc.power == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif sc.power == self.germany:
                    # 1st, 5 over threshold
                    self.assertAlmostEqual(s, 7+5)
                elif sc.power == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif sc.power == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd
                    self.assertAlmostEqual(s, 6)
        self.check_score_order(scores)

    def test_g_scoring_maxonian_3_equal_top(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1902)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if (sc.power == self.austria) or (sc.power == self.france):
                    # Joint 4th
                    self.assertAlmostEqual(s, (4 + 3) / 2)
                elif (sc.power == self.england) or (sc.power == self.italy):
                    # Joint 6th
                    self.assertAlmostEqual(s, (2 + 1) / 2)
                elif (sc.power == self.germany) or (sc.power == self.russia):
                    # Joint 1st
                    self.assertAlmostEqual(s, (7 + 6) / 2)
                else:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
        self.check_score_order(scores)

    def test_g_scoring_maxonian_4_equal_top(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        system = find_game_scoring_system('Maxonian')
        scores = system.scores(tgs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.filter(power=p).last()
                if sc.count == 5:
                    # Joint 1st
                    self.assertAlmostEqual(s, (7 + 6 + 5 + 4) / 4)
                else:
                    # Joint 5th
                    self.assertAlmostEqual(s, (3 + 2 + 1) / 3)
        self.check_score_order(scores)
