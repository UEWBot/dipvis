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

from django.test import TestCase
from django.utils import timezone

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.values.diplomacy_values import TOTAL_SCS
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.game_scoring_system_views import SimpleGameState
from tournament.models import Tournament, Round, Game, DrawProposal, CentreCount
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import DrawSecrecy, Seasons
from tournament.models import find_game_scoring_system
from tournament.tournament_game_state import TournamentGameState

from datetime import timedelta
from math import floor

HOURS_8 = timedelta(hours=8)
HOURS_16 = timedelta(hours=16)
HOURS_24 = timedelta(hours=24)

class GameScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        set1 = GameSet.objects.get(name='Avalon Hill')

        s1 = G_SCORING_SYSTEMS[0].name

        now = timezone.now()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date)
        r12 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_8)
        r13 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_16)
        Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_24)

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


    # GScoringWorldClassic
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

# GScoringDetour09
class Detour09GameScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        set1 = GameSet.objects.get(name='Avalon Hill')

        s1 = G_SCORING_SYSTEMS[0].name

        now = timezone.now()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date)

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

# GScoringMaxonian
class MaxonianGameScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        set1 = GameSet.objects.get(name='Avalon Hill')

        s1 = G_SCORING_SYSTEMS[0].name

        now = timezone.now()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date)

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
