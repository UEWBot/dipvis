# Diplomacy Tournament Visualiser
# Copyright (C) 2014 Chris Brand
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
from django.core.exceptions import ValidationError
from django.utils import timezone

from tournament.models import *

class TournamentModelTests(TestCase):
    def setUp(self):
        set1 = GameSet.objects.get(name='Avalon Hill')
        set2 = GameSet.objects.get(name='Gibsons')
        s1 = G_SCORING_SYSTEMS[0].name
        t1 = Tournament.objects.create(name='t1',
                                       start_date=timezone.now(),
                                       end_date=timezone.now(),
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name)
        t2 = Tournament.objects.create(name='t2',
                                       start_date=timezone.now(),
                                       end_date=timezone.now(),
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=timezone.now(),
                                       end_date=timezone.now(),
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name)
        r11 = Round.objects.create(tournament=t1, number=1, scoring_system=s1, dias=True)
        r12 = Round.objects.create(tournament=t1, number=2, scoring_system=s1, dias=True)
        r13 = Round.objects.create(tournament=t1, number=3, scoring_system=s1, dias=True)
        r14 = Round.objects.create(tournament=t1, number=4, scoring_system=s1, dias=True)
        r21 = Round.objects.create(tournament=t2, number=1, scoring_system=s1, dias=True)
        r22 = Round.objects.create(tournament=t2, number=2, scoring_system=s1, dias=True)
        r31 = Round.objects.create(tournament=t3, number=1, scoring_system=s1, dias=True)
        r32 = Round.objects.create(tournament=t3, number=2, scoring_system=s1, dias=True)
        g11 = Game.objects.create(name='g11', started_at=timezone.now(), the_round=r11, the_set=set1)
        g12 = Game.objects.create(name='g12', started_at=timezone.now(), the_round=r11, the_set=set1)
        g13 = Game.objects.create(name='g13', started_at=timezone.now(), the_round=r12, is_finished=True, the_set=set1)
        g14 = Game.objects.create(name='g14', started_at=timezone.now(), the_round=r12, the_set=set1)
        g15 = Game.objects.create(name='g15', started_at=timezone.now(), the_round=r13, is_finished=True, the_set=set1)
        g16 = Game.objects.create(name='g16', started_at=timezone.now(), the_round=r13, is_finished=True, the_set=set1)
        g21 = Game.objects.create(name='g21', started_at=timezone.now(), the_round=r21, the_set=set1)
        g22 = Game.objects.create(name='g22', started_at=timezone.now(), the_round=r22, the_set=set1)
        g31 = Game.objects.create(name='g31', started_at=timezone.now(), the_round=r31, is_finished=True, the_set=set1)
        g32 = Game.objects.create(name='g32', started_at=timezone.now(), the_round=r32, is_finished=True, the_set=set1)
        self.austria = GreatPower.objects.get(abbreviation='A')
        self.england = GreatPower.objects.get(abbreviation='E')
        self.france = GreatPower.objects.get(abbreviation='F')
        self.germany = GreatPower.objects.get(abbreviation='G')
        self.italy = GreatPower.objects.get(abbreviation='I')
        self.russia = GreatPower.objects.get(abbreviation='R')
        self.turkey = GreatPower.objects.get(abbreviation='T')

    def test_validate_year_negative(self):
        self.assertRaises(ValidationError, validate_year, -1)

    def test_validate_year_1899(self):
        self.assertRaises(ValidationError, validate_year, 1899)

    def test_validate_sc_count_negative(self):
        self.assertRaises(ValidationError, validate_sc_count, -1)

    def test_validate_sc_count_35(self):
        self.assertRaises(ValidationError, validate_sc_count, 35)
    
    def test_round_is_finished_no_games_over(self):
        t = Tournament.objects.get(name='t1')
        r1 = t.round_set.get(number=1)
        self.assertEqual(r1.is_finished(), False)

    def test_round_is_finished_some_games_over(self):
        t = Tournament.objects.get(name='t1')
        r2 = t.round_set.get(number=2)
        self.assertEqual(r2.is_finished(), False)

    def test_round_is_finished_all_games_over(self):
        t = Tournament.objects.get(name='t1')
        r3 = t.round_set.get(number=3)
        self.assertEqual(r3.is_finished(), True)

    def test_round_is_finished_no_games(self):
        """
        Rounds with no games can't have started, let alone finished
        """
        t = Tournament.objects.get(name='t1')
        r4 = t.round_set.get(number=4)
        self.assertEqual(r4.is_finished(), False)

    def test_tourney_is_finished_some_rounds_over(self):
        t = Tournament.objects.get(name='t1')
        self.assertEqual(t.is_finished(), False)

    def test_tourney_is_finished_no_rounds_over(self):
        t = Tournament.objects.get(name='t2')
        self.assertEqual(t.is_finished(), False)

    def test_tourney_is_finished_all_rounds_over(self):
        t = Tournament.objects.get(name='t3')
        self.assertEqual(t.is_finished(), True)

    def test_draw_proposal_with_duplicates(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False,
                          power_1=self.austria, power_2=self.austria)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_with_gap(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False,
                          power_1=self.austria, power_3=self.england)
        self.assertRaises(ValidationError, dp.clean)

