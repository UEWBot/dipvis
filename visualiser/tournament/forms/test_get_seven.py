# Diplomacy Tournament Visualiser
# Copyright (C) 2019-2026 Chris Brand
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

"""
Get Seven Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone

from django.test import TestCase

from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Pool, Round, RoundPlayer,
                               Tournament, TournamentPlayer)
from tournament.players import Player

from . import GetSevenPlayersForm


class GetSevenPlayersFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # We need a Tournament, with 4 Rounds:
        # - one that needs all standby players plus some to play two boards (round 1),
        # - one with an exact multiple of 7 (round 2),
        # - one that needs a subset of the standby players to play (round 3)
        # - one that needs all the standby players to play (round 4),
        today = date.today()
        t = Tournament.objects.create(name='t1',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        cls.r1 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        cls.r2 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(t.start_date, time(hour=12, tzinfo=datetime_timezone.utc)))
        cls.r3 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(t.start_date, time(hour=16, tzinfo=datetime_timezone.utc)))
        cls.r4 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(t.start_date, time(hour=20, tzinfo=datetime_timezone.utc)))

        p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        p3 = Player.objects.create(first_name='Christina', last_name='Calculus')
        p4 = Player.objects.create(first_name='Douglas', last_name='Dragnet')
        p5 = Player.objects.create(first_name='Edwina', last_name='Eggplant')
        p9 = Player.objects.create(first_name='Irene', last_name='Imp')
        p10 = Player.objects.create(first_name='Julia', last_name='Jug')
        # Create these out-of-order to check sorting
        p6 = Player.objects.create(first_name='Frank', last_name='Furious')
        p7 = Player.objects.create(first_name='Georgette', last_name='Giant')
        p8 = Player.objects.create(first_name='Harold', last_name='Homeless')
        TournamentPlayer.objects.create(player=p1, tournament=t)
        TournamentPlayer.objects.create(player=p2, tournament=t)
        TournamentPlayer.objects.create(player=p3, tournament=t)
        TournamentPlayer.objects.create(player=p4, tournament=t)
        TournamentPlayer.objects.create(player=p8, tournament=t)
        TournamentPlayer.objects.create(player=p9, tournament=t)
        TournamentPlayer.objects.create(player=p10, tournament=t)
        # Again, check sorting
        TournamentPlayer.objects.create(player=p5, tournament=t)
        TournamentPlayer.objects.create(player=p6, tournament=t)
        TournamentPlayer.objects.create(player=p7, tournament=t)

        cls.rp1_1 = RoundPlayer.objects.create(player=p1, the_round=cls.r1)
        cls.rp1_2 = RoundPlayer.objects.create(player=p2, the_round=cls.r1)
        cls.rp1_3 = RoundPlayer.objects.create(player=p3, the_round=cls.r1)
        cls.rp1_4 = RoundPlayer.objects.create(player=p4, the_round=cls.r1)
        cls.rp1_5 = RoundPlayer.objects.create(player=p5, the_round=cls.r1, standby=True)
        cls.rp1_7 = RoundPlayer.objects.create(player=p7, the_round=cls.r1)
        cls.rp1_8 = RoundPlayer.objects.create(player=p8, the_round=cls.r1)
        cls.rp1_9 = RoundPlayer.objects.create(player=p9, the_round=cls.r1)
        cls.rp1_10 = RoundPlayer.objects.create(player=p10, the_round=cls.r1)
        # Again, check sorting
        cls.rp1_6 = RoundPlayer.objects.create(player=p6, the_round=cls.r1)

        RoundPlayer.objects.create(player=p2, the_round=cls.r2)
        RoundPlayer.objects.create(player=p3, the_round=cls.r2)
        RoundPlayer.objects.create(player=p4, the_round=cls.r2)
        RoundPlayer.objects.create(player=p5, the_round=cls.r2)
        RoundPlayer.objects.create(player=p6, the_round=cls.r2)
        RoundPlayer.objects.create(player=p7, the_round=cls.r2)
        RoundPlayer.objects.create(player=p8, the_round=cls.r2)

        cls.rp3_1 = RoundPlayer.objects.create(player=p1, the_round=cls.r3, standby=True)
        cls.rp3_2 = RoundPlayer.objects.create(player=p2, the_round=cls.r3)
        cls.rp3_3 = RoundPlayer.objects.create(player=p3, the_round=cls.r3, standby=True)
        cls.rp3_4 = RoundPlayer.objects.create(player=p4, the_round=cls.r3)
        cls.rp3_5 = RoundPlayer.objects.create(player=p5, the_round=cls.r3, standby=True)
        cls.rp3_7 = RoundPlayer.objects.create(player=p7, the_round=cls.r3)
        cls.rp3_8 = RoundPlayer.objects.create(player=p8, the_round=cls.r3, standby=True)
        cls.rp3_9 = RoundPlayer.objects.create(player=p9, the_round=cls.r3)
        cls.rp3_10 = RoundPlayer.objects.create(player=p10, the_round=cls.r3)
        # Again, check sorting
        cls.rp3_6 = RoundPlayer.objects.create(player=p6, the_round=cls.r3, standby=True)

        RoundPlayer.objects.create(player=p2, the_round=cls.r4)
        RoundPlayer.objects.create(player=p3, the_round=cls.r4)
        RoundPlayer.objects.create(player=p4, the_round=cls.r4, standby=True)
        RoundPlayer.objects.create(player=p5, the_round=cls.r4)
        RoundPlayer.objects.create(player=p6, the_round=cls.r4, standby=True)
        RoundPlayer.objects.create(player=p7, the_round=cls.r4)
        RoundPlayer.objects.create(player=p8, the_round=cls.r4)

    def test_form_needs_round(self):
        """Omit the_round constructor parameter"""
        with self.assertRaises(KeyError):
            GetSevenPlayersForm(pool=None)

    def test_form_needs_pool(self):
        """Omit pool constructor parameter"""
        with self.assertRaises(KeyError):
            GetSevenPlayersForm(the_round=self.r1)

    def test_wrong_pool(self):
        """Only variable-sized pool is valid"""
        pool1 = Pool.objects.create(the_round=self.r1,
                                    name='Fixed',
                                    board_count=1)
        Pool.objects.create(the_round=self.r1,
                            name='Variable')
        with self.assertRaises(AssertionError):
            GetSevenPlayersForm(the_round=self.r1, pool=pool1)
        # Cleanup
        self.r1.pool_set.all().delete()

    def test_sitters_fields(self):
        """Check fields for players sitting out"""
        prefix = 'sitter'
        form = GetSevenPlayersForm(the_round=self.r1, pool=None)
        for i in range(0, 2):
            with self.subTest(i=i):
                name = f'{prefix}_{i}'
                self.assertIn(name, form.fields)
                the_choices = list(form.fields[name].choices)
                # We should have one choice per non-standby RoundPlayer, plus the initial empty choice
                self.assertEqual(len(the_choices), self.r1.roundplayer_set.filter(standby=False).count() + 1)
                # The keys should be the RoundPlayer pks
                self.assertEqual(the_choices[1][0], self.rp1_1.pk)
                # and the values should be the Player names, in alphabetical order
                self.assertEqual(the_choices[1][1], self.rp1_1.player.sortable_str())
                self.assertEqual(the_choices[2][1], self.rp1_2.player.sortable_str())
                self.assertEqual(the_choices[3][1], self.rp1_3.player.sortable_str())
                self.assertEqual(the_choices[4][1], self.rp1_4.player.sortable_str())
                self.assertEqual(the_choices[5][1], self.rp1_6.player.sortable_str())
                self.assertEqual(the_choices[6][1], self.rp1_7.player.sortable_str())
                self.assertEqual(the_choices[7][1], self.rp1_8.player.sortable_str())
                self.assertEqual(the_choices[8][1], self.rp1_9.player.sortable_str())
                self.assertEqual(the_choices[9][1], self.rp1_10.player.sortable_str())
        self.assertNotIn(f'{prefix}_2', form.fields)

    def test_doubles_fields(self):
        """Check fields for players playing two games"""
        prefix = 'double'
        form = GetSevenPlayersForm(the_round=self.r1, pool=None)
        for i in range(0, 4):
            with self.subTest(i=i):
                name = f'{prefix}_{i}'
                self.assertIn(name, form.fields)
                the_choices = list(form.fields[name].choices)
                # We should have one choice per RoundPlayer, plus the initial empty choice
                self.assertEqual(len(the_choices), self.r1.roundplayer_set.count() + 1)
                # The keys should be the RoundPlayer pks
                self.assertEqual(the_choices[1][0], self.rp1_1.pk)
                # and the values should be the Player names, in alphabetical order
                self.assertEqual(the_choices[1][1], self.rp1_1.player.sortable_str())
                self.assertEqual(the_choices[2][1], self.rp1_2.player.sortable_str())
                self.assertEqual(the_choices[3][1], self.rp1_3.player.sortable_str())
                self.assertEqual(the_choices[4][1], self.rp1_4.player.sortable_str())
                self.assertEqual(the_choices[5][1], self.rp1_5.player.sortable_str())
                self.assertEqual(the_choices[6][1], self.rp1_6.player.sortable_str())
                self.assertEqual(the_choices[7][1], self.rp1_7.player.sortable_str())
                self.assertEqual(the_choices[8][1], self.rp1_8.player.sortable_str())
                self.assertEqual(the_choices[9][1], self.rp1_9.player.sortable_str())
                self.assertEqual(the_choices[10][1], self.rp1_10.player.sortable_str())
        self.assertNotIn(f'{prefix}_4', form.fields)

    def test_no_standbys_fields(self):
        """We should have no standby fields if all standby players are needed"""
        form = GetSevenPlayersForm(the_round=self.r1, pool=None)
        name = 'standby_0'
        self.assertNotIn(name, form.fields)

    def test_pool(self):
        """If we pass a Pool, other pools should be ignored"""
        pool1 = Pool.objects.create(the_round=self.r1,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r1,
                                    name='Variable')
        for rp in self.r1.roundplayer_set.all():
            if rp == self.rp1_3:
                rp.pool = pool1
            else:
                rp.pool = pool2
            rp.save()
        form = GetSevenPlayersForm(the_round=self.r1, pool=pool2)
        # With 9 players, we need 1 sitter in addition to the standby
        self.assertIn('sitter_0', form.fields)
        self.assertNotIn('sitter_1', form.fields)
        # Player 3 should not be an option
        the_choices = list(form.fields['sitter_0'].choices)
        self.assertNotIn(self.rp1_3.pk, [pk for pk, name in the_choices])
        # Cleanup
        for rp in self.r1.roundplayer_set.all():
            rp.pool = None
            rp.save()
        self.r1.pool_set.all().delete()

    def test_success_sitters(self):
        """Valid form with people sitting out"""
        data = {'sitter_0': str(self.rp1_10.pk),
                'sitter_1': str(self.rp1_7.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(True, form.is_valid())

    def test_success_doublers(self):
        """Valid form with people playing two games"""
        data = {'double_0': str(self.rp1_10.pk),
                'double_1': str(self.rp1_7.pk),
                'double_2': str(self.rp1_3.pk),
                'double_3': str(self.rp1_4.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(True, form.is_valid())

    def test_existing_sitters(self):
        """Already two people flagged as sitting out the round"""
        self.rp1_3.game_count = 0
        self.rp1_3.save(update_fields=['game_count'])
        self.rp1_4.game_count = 0
        self.rp1_4.save(update_fields=['game_count'])
        form = GetSevenPlayersForm(the_round=self.r1, pool=None)
        # They should be listed as a sitter
        self.assertEqual(form['sitter_0'].initial, self.rp1_3)
        self.assertEqual(form['sitter_1'].initial, self.rp1_4)
        # Clean up changes made
        self.rp1_3.game_count = 1
        self.rp1_3.save(update_fields=['game_count'])
        self.rp1_4.game_count = 1
        self.rp1_4.save(update_fields=['game_count'])

    def test_existing_doublers(self):
        """Already two people flagged as playing two games"""
        self.rp1_3.game_count = 2
        self.rp1_3.save(update_fields=['game_count'])
        self.rp1_4.game_count = 2
        self.rp1_4.save(update_fields=['game_count'])
        form = GetSevenPlayersForm(the_round=self.r1, pool=None)
        # They should be listed as a doubler
        self.assertEqual(form['double_0'].initial, self.rp1_3)
        self.assertEqual(form['double_1'].initial, self.rp1_4)
        # Clean up changes made
        self.rp1_3.game_count = 1
        self.rp1_3.save(update_fields=['game_count'])
        self.rp1_4.game_count = 1
        self.rp1_4.save(update_fields=['game_count'])

    def test_sitting_twice(self):
        """One person listed twice as sitting out"""
        data = {'sitter_0': str(self.rp1_3.pk),
                'sitter_1': str(self.rp1_3.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, None, 'Player Christina Calculus appears more than once')

    def test_doubling_twice(self):
        """One person listed twice as playing two games"""
        data = {'double_0': str(self.rp1_10.pk),
                'double_1': str(self.rp1_7.pk),
                'double_2': str(self.rp1_10.pk),
                'double_3': str(self.rp1_4.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, None, 'Player Julia Jug appears more than once')

    def test_provide_both(self):
        """Both people sitting out and people playing two boards"""
        data = {'sitter_0': str(self.rp1_1.pk),
                'sitter_1': str(self.rp1_2.pk),
                'double_0': str(self.rp1_4.pk),
                'double_1': str(self.rp1_5.pk),
                'double_2': str(self.rp1_6.pk),
                'double_3': str(self.rp1_7.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, None, 'Either have players sit out the round or have players play two games')

    def test_too_few_sitters(self):
        data = {'sitter_0': str(self.rp1_10.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, None, 'Too few players sitting out games. Got 1, expected 2')

    def test_too_few_doublers(self):
        data = {'double_0': str(self.rp1_10.pk),
                'double_1': str(self.rp1_7.pk),
                'double_2': str(self.rp1_3.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, None, 'Too few players playing two games. Got 3, expected 4')

    def test_none_needed(self):
        """Exact multiple of seven already"""
        form = GetSevenPlayersForm(the_round=self.r2, pool=None)
        # Nothing needed
        self.assertEqual(len(form.fields), 0)

    def test_standby_fields(self):
        """We should have 2 fields for standby players needed to play in Round 3"""
        prefix='standby'
        form = GetSevenPlayersForm(the_round=self.r3, pool=None)
        for i in range(0, 2):
            with self.subTest(i=i):
                name = f'{prefix}_{i}'
                self.assertIn(name, form.fields)
                the_choices = list(form.fields[name].choices)
                # We should have one choice per standby RoundPlayer, plus the initial empty choice
                self.assertEqual(len(the_choices), self.r3.roundplayer_set.filter(standby=True).count() + 1)
                # The keys should be the RoundPlayer pks
                self.assertEqual(the_choices[1][0], self.rp3_1.pk)
                # and the values should be the Player names, in alphabetical order
                self.assertEqual(the_choices[1][1], self.rp3_1.player.sortable_str())
                self.assertEqual(the_choices[2][1], self.rp3_3.player.sortable_str())
                self.assertEqual(the_choices[3][1], self.rp3_5.player.sortable_str())
                self.assertEqual(the_choices[4][1], self.rp3_6.player.sortable_str())
                self.assertEqual(the_choices[5][1], self.rp3_8.player.sortable_str())

    def test_no_choices_needed(self):
        """If we need all standbys to play, no choices needed"""
        form = GetSevenPlayersForm(the_round=self.r4, pool=None)
        self.assertEqual(0, len(form.fields))

    def test_too_few_standbys(self):
        data = {'standby_0': str(self.rp3_1.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r3, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, None, 'Too few standby players selected to play. Got 1, expected 2')

    def test_has_changed_standbys_implicit_initial(self):
        data = {}
        for n, rp in enumerate(self.r3.roundplayer_set.filter(standby=True)):
            data[f'standby_{n}'] = str(rp.pk)
        form = GetSevenPlayersForm(data=data,
                                   the_round=self.r3,
                                   pool=None)
        self.assertIs(False, form.has_changed())

    def test_has_changed_no_standbys_implicit_initial(self):
        # Set some players already sitting out
        self.rp1_3.game_count = 0
        self.rp1_3.save(update_fields=['game_count'])
        self.rp1_4.game_count = 0
        self.rp1_4.save(update_fields=['game_count'])
        data = {'sitter_0': str(self.rp1_3.pk),
                'sitter_1': str(self.rp1_4.pk)}
        form = GetSevenPlayersForm(data=data,
                                   the_round=self.r1,
                                   pool=None)
        self.assertIs(False, form.has_changed())
        # Now set some to be playing two games
        self.rp1_3.game_count = 2
        self.rp1_3.save(update_fields=['game_count'])
        self.rp1_4.game_count = 2
        self.rp1_4.save(update_fields=['game_count'])
        data = {'double_0': str(self.rp1_3.pk),
                'double_1': str(self.rp1_4.pk)}
        form = GetSevenPlayersForm(data=data,
                                   the_round=self.r1,
                                   pool=None)
        self.assertIs(False, form.has_changed())
        # Clean up changes made
        self.rp1_3.game_count = 1
        self.rp1_3.save(update_fields=['game_count'])
        self.rp1_4.game_count = 1
        self.rp1_4.save(update_fields=['game_count'])

    def test_has_changed_standbys_explicit_initial(self):
        initial = {'standby_0': self.rp3_10,
                   'standby_1': self.rp3_7}
        data = {}
        for k, v in initial.items():
            data[k] = str(v.pk)
        form = GetSevenPlayersForm(data=data,
                                   initial=initial,
                                   the_round=self.r3,
                                   pool=None)
        self.assertIs(False, form.has_changed())

    def test_has_changed_no_standbys_explicit_initial(self):
        initial = {'sitter_0': self.rp1_10,
                   'sitter_1': self.rp1_7}
        data = {}
        for k, v in initial.items():
            data[k] = str(v.pk)
        form = GetSevenPlayersForm(data=data,
                                   initial=initial,
                                   the_round=self.r1,
                                   pool=None)
        self.assertIs(False, form.has_changed())
        initial = {'double_0': self.rp1_10,
                   'double_1': self.rp1_7,
                   'double_2': self.rp1_3,
                   'double_3': self.rp1_4}
        data = {}
        for k, v in initial.items():
            data[k] = str(v.pk)
        form = GetSevenPlayersForm(data=data,
                                   initial=initial,
                                   the_round=self.r1,
                                   pool=None)
        self.assertIs(False, form.has_changed())
