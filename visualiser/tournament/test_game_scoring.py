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

from tournament.diplomacy import GameSet, GreatPower, TOTAL_SCS
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, Round, Game, DrawProposal, CentreCount
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import find_game_scoring_system

from datetime import timedelta

HOURS_8 = timedelta(hours=8)
HOURS_16 = timedelta(hours=16)
HOURS_24 = timedelta(hours=24)

class GameScoringTests(TestCase):
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

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date)
        r12 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_8)
        r13 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_16)
        Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_24)

        # Add Games to r11
        g11 = Game.objects.create(name='g11', started_at=r11.start, the_round=r11, the_set=cls.set1)
        Game.objects.create(name='g12', started_at=r11.start, the_round=r11, the_set=cls.set1)
        # Add Games to r12
        Game.objects.create(name='g13', started_at=r12.start, the_round=r12, is_finished=True, the_set=cls.set1)
        Game.objects.create(name='g14', started_at=r12.start, the_round=r12, the_set=cls.set1)
        # Add Games to r13
        Game.objects.create(name='g15', started_at=r13.start, the_round=r13, is_finished=True, the_set=cls.set1)
        Game.objects.create(name='g16', started_at=r13.start, the_round=r13, is_finished=True, the_set=cls.set1)

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

    # description
    def test_description(self):
        for system in G_SCORING_SYSTEMS:
            with self.subTest(system=system.name):
                desc = system.description
                # TODO verify desc

    # GScoringSolos
    def test_g_scoring_solos_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Solo or bust')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for s in scores.values():
            self.assertEqual(s, 0)

    def test_g_scoring_solos_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1907)
        system = find_game_scoring_system('Solo or bust')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)

    # GScoringDrawSize
    def test_g_scoring_draws_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for s in scores.values():
            self.assertEqual(s, 100.0/7)
        self.assertAlmostEqual(sum(scores.values()), 100)

    def test_g_scoring_draws_7way_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.austria,
                                    power_1=self.austria, power_2=self.england, power_3=self.france,
                                    power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for s in scores.values():
            self.assertEqual(s, 100.0/7)
        self.assertAlmostEqual(sum(scores.values()), 100)

    def test_g_scoring_draws_4way_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.austria,
                                    power_1=self.austria, power_2=self.england, power_3=self.russia,
                                    power_4=self.germany)
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p in GreatPower.objects.all():
            if (p == self.austria) or (p == self.england) or (p == self.russia) or (p == self.germany):
                self.assertEqual(scores[p], 100.0/4)
            else:
                self.assertEqual(scores[p], 0.0)
        # 2 neutrals don't matter
        self.assertEqual(sum(scores.values()), 100)

    def test_g_scoring_draws_eliminations(self):
        """No draw, no solo, but with powers eliminated"""
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1905)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(scs)
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
        scs = g.centrecount_set.filter(year=1907)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)

    # GScoringCDiplo
    def test_g_scoring_cdiplo_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('CDiplo 100')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1907)
        system = find_game_scoring_system('CDiplo 100')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)

    def test_g_scoring_cdiplo80_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('CDiplo 80')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1907)
        system = find_game_scoring_system('CDiplo 80')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 80)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 80)

    # GScoringSumOfSquares
    def test_g_scoring_squares_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Sum of Squares')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1907)
        system = find_game_scoring_system('Sum of Squares')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)

    # GScoringCarnage (with dead equal)
    def test_g_scoring_carnage1_simple(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1907)
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)

    def test_g_scoring_carnage1_eliminations(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1906)
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
        for p,s in scores.items():
            sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Carnage with elimination order')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sc.count == 4:
                self.assertEqual(s, (3000 + 2000 + 1000) / 3 + sc.count)
            else:
                self.assertEqual(s, (7000 + 6000 + 5000 + 4000) / 4 + sc.count)
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS - 2)

    def test_g_scoring_carnage2_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1907)
        system = find_game_scoring_system('Carnage with elimination order')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
            else:
                self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)

    def test_g_scoring_carnage2_eliminations(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1906)
        system = find_game_scoring_system('Carnage with elimination order')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
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

    # GScoringJanus
    def test_g_scoring_janus_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Janus')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
                # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
                if sc.count == 4:
                    self.assertEqual(s, 60 / 7 + 4)
                else:
                    self.assertEqual(s, 60 / 7 + 6 / 4 + 5)
        # Total of all scores should be 100 minus 2 (neutrals)
        self.assertAlmostEqual(sum(scores.values()), 98)

    def test_g_scoring_janus_no_solo_2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1905)
        system = find_game_scoring_system('Janus')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
                if sc.count == 0:
                    self.assertEqual(s, 0)
                elif sc.count == 3:
                    self.assertEqual(s, 3 + 10 - 7)
                elif sc.count == 4:
                    self.assertEqual(s, 4 + 10 - 7)
                elif sc.count == 5:
                    self.assertEqual(s, 5 + 10 - 7)
                elif sc.count == 6:
                    self.assertEqual(s, 6 + 10 - 7)
                else:
                    self.assertEqual(s, 13 + 6 + 10 + 7 * 5)
        # Total of all scores should be 100
        self.assertAlmostEqual(sum(scores.values()), 100)

    def test_g_scoring_janus_no_solo_3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1906)
        system = find_game_scoring_system('Janus')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
                if sc.count == 0:
                    self.assertEqual(s, 0)
                elif sc.count == 5:
                    self.assertEqual(s, 5 + 15 - 10)
                elif sc.count == 7:
                    self.assertEqual(s, 7 + 15 - 10)
                else:
                    self.assertEqual(s, 17 + 6 + 15 + 30)
        # Total of all scores should be 100
        self.assertAlmostEqual(sum(scores.values()), 100)

    def test_g_scoring_janus_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1907)
        system = find_game_scoring_system('Janus')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
                if sc.count == 18:
                    self.assertEqual(s, 100)
                else:
                    self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)

    # GScoringTribute
    def test_g_scoring_tribute_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Tribute')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('Tribute')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1905)
        system = find_game_scoring_system('Tribute')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1906)
        system = find_game_scoring_system('Tribute')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1907)
        system = find_game_scoring_system('Tribute')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
                if sc.count == 18:
                    self.assertEqual(s, 100)
                else:
                    self.assertEqual(s, 0)
        self.assertEqual(sum(scores.values()), 100)

    def test_g_scoring_world_classic_no_solo1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('World Classic')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
                if sc.count == 0:
                    self.assertEqual(s, 3)
                elif sc.count == 8:
                    self.assertEqual(s, 30 + 10 * sc.count + 48/2)
                else:
                    self.assertEqual(s, 30 + 10 * sc.count)

    def test_g_scoring_world_classic_no_solo2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1905)
        system = find_game_scoring_system('World Classic')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
                if sc.count == 0:
                    self.assertEqual(s, 3)
                elif sc.count == 13:
                    self.assertEqual(s, 30 + 10 * sc.count + 48)
                else:
                    self.assertEqual(s, 30 + 10 * sc.count)

    def test_g_scoring_world_classic_no_solo3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1906)
        system = find_game_scoring_system('World Classic')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1907)
        system = find_game_scoring_system('World Classic')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
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

    def test_g_scoring_manorcon_no_solo1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1905)
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
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
        scs = g.centrecount_set.filter(year=1906)
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
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
                    elif sc.power == self.italy:
                        self.assertAlmostEqual(s, 0.5)

    def test_g_scoring_manorcon_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1907)
        system = find_game_scoring_system('ManorCon')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            with self.subTest(power=p):
                sc = scs.get(power=p)
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

