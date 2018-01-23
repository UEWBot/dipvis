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
from django.utils import timezone

from tournament.models import *

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
                                       draw_secrecy=SECRET)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date)
        r12 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_8)
        r13 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_16)
        r14 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_24)

        # Add Games to r11
        g11 = Game.objects.create(name='g11', started_at=r11.start, the_round=r11, the_set=cls.set1)
        g12 = Game.objects.create(name='g12', started_at=r11.start, the_round=r11, the_set=cls.set1)
        # Add Games to r12
        g13 = Game.objects.create(name='g13', started_at=r12.start, the_round=r12, is_finished=True, the_set=cls.set1)
        g14 = Game.objects.create(name='g14', started_at=r12.start, the_round=r12, the_set=cls.set1)
        # Add Games to r13
        g15 = Game.objects.create(name='g15', started_at=r13.start, the_round=r13, is_finished=True, the_set=cls.set1)
        g16 = Game.objects.create(name='g16', started_at=r13.start, the_round=r13, is_finished=True, the_set=cls.set1)

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # Add CentreCounts to g11
        sc1101a = CentreCount.objects.create(power=cls.austria, game=g11, year=1901, count=5)
        sc1101e = CentreCount.objects.create(power=cls.england, game=g11, year=1901, count=4)
        sc1101f = CentreCount.objects.create(power=cls.france, game=g11, year=1901, count=5)
        sc1101g = CentreCount.objects.create(power=cls.germany, game=g11, year=1901, count=5)
        sc1101i = CentreCount.objects.create(power=cls.italy, game=g11, year=1901, count=4)
        sc1101r = CentreCount.objects.create(power=cls.russia, game=g11, year=1901, count=5)
        sc1101t = CentreCount.objects.create(power=cls.turkey, game=g11, year=1901, count=4)

        sc1104a = CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        sc1104e = CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=4)
        sc1104f = CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=2)
        sc1104g = CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=18)
        sc1104i = CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=2)
        sc1104r = CentreCount.objects.create(power=cls.russia, game=g11, year=1904, count=3)
        sc1104t = CentreCount.objects.create(power=cls.turkey, game=g11, year=1904, count=5)

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
        scs = g.centrecount_set.filter(year=1904)
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

    def test_g_scoring_draws_7way_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for s in scores.values():
            self.assertEqual(s, 100.0/7)

    def test_g_scoring_draws_4way_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.austria,
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

    def test_g_scoring_draws_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)

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
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('CDiplo 100')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)

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
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('CDiplo 80')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 80)
            else:
                self.assertEqual(s, 0)

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
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('Sum of Squares')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)

    # GScoringCarnage
    def test_g_scoring_carnage_simple(self):
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
                self.assertEqual(s, (3000 + 2000 + 1000) / 3 + 4)
            else:
                self.assertEqual(s, (7000 + 6000 + 5000 + 4000) / 4 + 5)
        self.assertEqual(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS - 2)

    def test_g_scoring_carnage_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
            else:
                self.assertEqual(s, 0)

    # TODO test Carnage scoring with eliminations but no solo

