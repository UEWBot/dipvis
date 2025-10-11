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

from django.test import TestCase

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.game_scoring.g_scoring_systems import G_SCORING_SYSTEMS
from tournament.game_scoring.test_general import check_score_order
from tournament.models import Tournament, Round, Game, DrawProposal, CentreCount
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import DrawSecrecy, Seasons
from tournament.models import find_game_scoring_system
from tournament.tournament_game_state import TournamentGameState

HOURS_24 = timedelta(hours=24)

# TODO: Migrate away from TournamentGameState
#       SimpleGameState is too simple, unfortunately, but we should be
#       able to use our own class derived from GameState instead.


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
                if p == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif p == self.england:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                elif p == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif p == self.germany:
                    # 1st
                    self.assertAlmostEqual(s, 7)
                elif p == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif p == self.russia:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                else:
                    # 2nd
                    self.assertAlmostEqual(s, 6)
        check_score_order(self, scores)

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
                if p == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif p == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif p == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif p == self.germany:
                    # 1st
                    self.assertAlmostEqual(s, 7)
                elif p == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif p == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd
                    self.assertAlmostEqual(s, 6)
        check_score_order(self, scores)

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
                if p == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif p == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif p == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif p == self.germany:
                    # 1st, 4 over threshold
                    self.assertAlmostEqual(s, 7+4)
                elif p == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif p == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd, 1 over threshold
                    self.assertAlmostEqual(s, 6+1)
        check_score_order(self, scores)

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
                if p == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif p == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif p == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif p == self.germany:
                    # 1st, 6 over threshold
                    self.assertAlmostEqual(s, 7+6)
                elif p == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif p == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd, 3 over threshold
                    self.assertAlmostEqual(s, 6+3)
        check_score_order(self, scores)

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
                if p == self.austria:
                    # 7th
                    self.assertAlmostEqual(s, 1)
                elif p == self.england:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
                elif p == self.france:
                    # 5th
                    self.assertAlmostEqual(s, 3)
                elif p == self.germany:
                    # 1st, 5 over threshold
                    self.assertAlmostEqual(s, 7+5)
                elif p == self.italy:
                    # 6th
                    self.assertAlmostEqual(s, 2)
                elif p == self.russia:
                    # 4th
                    self.assertAlmostEqual(s, 4)
                else:
                    # 2nd
                    self.assertAlmostEqual(s, 6)
        check_score_order(self, scores)

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
                if (p == self.austria) or (p == self.france):
                    # Joint 4th
                    self.assertAlmostEqual(s, (4 + 3) / 2)
                elif (p == self.england) or (p == self.italy):
                    # Joint 6th
                    self.assertAlmostEqual(s, (2 + 1) / 2)
                elif (p == self.germany) or (p == self.russia):
                    # Joint 1st
                    self.assertAlmostEqual(s, (7 + 6) / 2)
                else:
                    # 3rd
                    self.assertAlmostEqual(s, 5)
        check_score_order(self, scores)

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
        check_score_order(self, scores)
