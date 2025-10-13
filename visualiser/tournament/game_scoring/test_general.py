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
from tournament.game_scoring.base import InvalidYear
from tournament.game_scoring.utils import _adjust_rank_score_lower_special
from tournament.game_scoring_system_views import SimpleGameState
from tournament.models import Tournament, Round, Game, DrawProposal, CentreCount
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import DrawSecrecy, Seasons
from tournament.models import find_game_scoring_system
from tournament.tournament_game_state import TournamentGameState

HOURS_24 = timedelta(hours=24)


# Function needed by most classes
def check_score_order(self, scores):
    """Check that the scores appear in GreatPower order when iterated through"""
    EXPECT = [p for p in GreatPower.objects.all()]
    order = [k for k in scores.keys()]
    self.assertEqual(EXPECT, order)


class GameScoringTests(TestCase):
    """
    Tests that aren't specific to one scoring system
    """
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

    def test_no_corruption(self):
        """Ensure that calls to calculate scores are independent"""
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

    # description for all G_SCORING_SYSTEMS
    def test_description(self):
        for system in G_SCORING_SYSTEMS:
            with self.subTest(system=system.name):
                desc = system.description
                # TODO verify desc

    # dead_score_can_change() for all G_SCORING_SYSTEMS
    def test_score_changes(self):
        """Compare score for eliminated power before and after a solo"""
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
    def test_tgs_concession_is_solo(self):
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

    def test_tgs_draw_is_not_solo(self):
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

    def test_tgs_solo_year_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        self.assertIsNone(tgs.solo_year())

    def test_tgs_dot_count_invalid_year(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        self.assertRaises(InvalidYear, tgs.dot_count, self.france, year=1899)

    def test_tgs_year_eliminated_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        self.assertIsNone(tgs.year_eliminated(self.france))

    def test_tgs_powers_in_draw(self):
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
        powers = tgs.powers_in_draw()
        self.assertEqual(len(powers), 2)
        self.assertIn(self.france, powers)
        self.assertIn(self.turkey, powers)
        # Clean up
        dp.delete()

    # Some tests of SimpleGameState
    def test_sgs_concession_is_solo(self):
        sgs = SimpleGameState(sc_counts={self.austria: 1,
                                         self.england: 10,
                                         self.france: 1,
                                         self.germany: 1,
                                         self.italy: 10,
                                         self.russia: 10,
                                         self.turkey: 1},
                              final_year=1907,
                              elimination_years={},
                              draw=[self.italy])
        self.assertEqual(sgs.soloer(), self.italy)
        self.assertEqual(sgs.powers_in_draw(), [self.italy])

    def test_sgs_solo_year_none(self):
        self.assertIsNone(self.three_survivors.solo_year())

    # Some tests of _adjust_rank_score_lower_special
    def test_adjust_rank_score_lower_special_2_way_ties(self):
        POS_PTS = [70, 60, 50, 40, 30, 20, 10]
        POS_PTS_2_TIED = [30, 20, 10]
        dots = [(self.austria, 14),
                (self.england, 8),
                (self.france, 8),
                (self.germany, 2),
                (self.italy, 2),
                (self.russia, 0),
                (self.turkey, 0)]
        # 1st from POS_PTS, then 2 from POS_PTS_2_TIED, rest are beyond the end of POS_PTS_2_TIED
        EXPECT = [70, 20, 20, 0, 0, 0, 0]
        result = _adjust_rank_score_lower_special(dots,
                                                  POS_PTS,
                                                  POS_PTS_2_TIED)
        self.assertEqual(result, EXPECT)

    def test_adjust_rank_score_lower_special_short_rank_pts(self):
        POS_PTS = [70, 60, 50, 40, 30]
        POS_PTS_2_TIED = [30, 20, 10]
        dots = [(self.austria, 14),
                (self.england, 8),
                (self.france, 7),
                (self.germany, 2),
                (self.italy, 1),
                (self.russia, 1),
                (self.turkey, 0)]
        # 1st from POS_PTS, then 2 from POS_PTS_2_TIED, rest are beyond the end of POS_PTS_2_TIED
        EXPECT = [70, 60, 50, 40, 0, 0, 0]
        result = _adjust_rank_score_lower_special(dots,
                                                  POS_PTS,
                                                  POS_PTS_2_TIED)
        self.assertEqual(result, EXPECT)
