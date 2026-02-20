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

from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone

from django.test import TestCase

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.game_scoring.g_scoring_systems import G_SCORING_SYSTEMS
from tournament.game_scoring.game_state import DotCountUnknown, InvalidYear
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               CentreCount, DrawProposal, DrawSecrecy, Game,
                               Round, Seasons, Tournament,
                               find_game_scoring_system)
from tournament.tournament_game_state import TournamentGameState

HOURS_24 = timedelta(hours=24)


class TournamentGameStateTests(TestCase):
    """
    Test TournamentGameState
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
                                   start=datetime.combine(t1.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        r12 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=12, tzinfo=datetime_timezone.utc)))
        r13 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=datetime.combine(t1.start_date, time(hour=16, tzinfo=datetime_timezone.utc)))
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=datetime.combine(t1.start_date, time(hour=20, tzinfo=datetime_timezone.utc)))

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

    # survivors()
    def test_tgs_survivors(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.all()
        tgs = TournamentGameState(scs)
        powers = tgs.survivors()
        # Despite the solo, all powers with SCs should be included
        self.assertEqual(len(powers), 4)
        self.assertIn(self.england, powers)
        self.assertIn(self.germany, powers)
        self.assertIn(self.russia, powers)
        self.assertIn(self.turkey, powers)

    # powers_in_draw()
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

    def test_tgs_powers_in_no_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        powers = tgs.powers_in_draw()
        self.assertEqual(len(powers), 7)
        #self.assertIn(self.france, powers)
        #self.assertIn(self.turkey, powers)

    def test_tgs_powers_in_draw_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.all()
        tgs = TournamentGameState(scs)
        powers = tgs.powers_in_draw()
        # TODO This feels wrong
        # Despite the solo, all powers with SCs should be included
        self.assertEqual(len(powers), 4)
        self.assertIn(self.england, powers)
        self.assertIn(self.germany, powers)
        self.assertIn(self.russia, powers)
        self.assertIn(self.turkey, powers)

    # solo_year()
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
        for p, s in scores.items():
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

    def test_tgs_solo_year(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.all()
        tgs = TournamentGameState(scs)
        year = tgs.solo_year()
        self.assertEqual(year, 1907)

    # num_powers_with()
    def test_tgs_num_powers_with(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.all()
        tgs = TournamentGameState(scs)
        num = tgs.num_powers_with(5)
        self.assertEqual(num, 1)
        num = tgs.num_powers_with(0)
        self.assertEqual(num, 3)
        num = tgs.num_powers_with(18)
        self.assertEqual(num, 1)

    # dot_count()
    def test_tgs_dot_count_valid_year(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        dots = tgs.dot_count(self.france, year=1901)
        self.assertEqual(dots, scs.get(power=self.france, year=1901).count)

    def test_tgs_dot_count_invalid_year(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        self.assertRaises(InvalidYear, tgs.dot_count, self.france, year=1899)

    def test_tgs_dot_count_unknown(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.all()
        tgs = TournamentGameState(scs)
        self.assertRaises(DotCountUnknown, tgs.dot_count, self.france, year=1903)

    # year_eliminated()
    def test_tgs_year_eliminated_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.filter(year__lte=1901)
        tgs = TournamentGameState(scs)
        self.assertIsNone(tgs.year_eliminated(self.france))

    # last_full_year()
    def test_tgs_last_full_year(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIsNone(g.passed_draw())
        scs = g.centrecount_set.all()
        tgs = TournamentGameState(scs)
        year = tgs.last_full_year()
        self.assertEqual(year, 1907)
