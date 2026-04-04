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
Roll Call Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone

from django.forms.formsets import formset_factory
from django.test import TestCase

from tournament.diplomacy import GameSet
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Game, Round, RoundPlayer,
                               Tournament, TournamentPlayer)
from tournament.players import Player

from . import BasePlayerRoundFormset, PlayerRoundForm


class PlayerRoundFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # We need a Player and a Tournament
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)

        cls.p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')

    def test_success(self):
        """Do everything right"""
        data = {'player': str(self.p1.pk),
                'present': 'on',
                'standby': 'on',
                'sandboxer': 'on'}
        initial = {'player': self.p1,
                   'present': False,
                   'standby': False,
                   'sandboxer': False,
                   'rounds_played': 0}
        form = PlayerRoundForm(data,
                               initial=initial)
        self.assertIs(True, form.is_valid())

    def test_success2(self):
        """Do everything right"""
        data = {'player': str(self.p1.pk)}
        initial = {'player': self.p1,
                   'present': False,
                   'standby': False,
                   'sandboxer': False,
                   'rounds_played': 0}
        form = PlayerRoundForm(data,
                               initial=initial)
        self.assertIs(True, form.is_valid())

    def test_round_fields(self):
        """Check that the correct fields are created"""
        form = PlayerRoundForm()
        # We should have five fields - player, present, standby, sandboxer, and rounds_played
        self.assertEqual(len(form.fields), 5)

    def test_player_labels(self):
        """Check the player names"""
        form = PlayerRoundForm()
        the_choices = list(form.fields['player'].choices)
        # We should have one per Player, plus the initial empty choice
        self.assertEqual(len(the_choices), Player.objects.count() + 1)
        # The keys should be the Player pks
        self.assertEqual(the_choices[1][0], self.p1.pk)
        # and the values should be the Player names, in alphabetical order
        self.assertEqual(the_choices[1][1], self.p1.sortable_str())
        self.assertEqual(the_choices[2][1], self.p2.sortable_str())

    def test_has_changed(self):
        data = {'player': str(self.p1.pk),
                'present': 'ok',
                'standby': 'ok',
                'sandboxer': 'ok',
                'rounds_played': '1'}
        initial = {'player': self.p1,
                   'present': True,
                   'standby': True,
                   'sandboxer': True,
                   'rounds_played': 1}
        form = PlayerRoundForm(data=data, initial=initial)
        self.assertIs(False, form.has_changed())

    def test_validation(self):
        initial = {'player': self.p1,
                   'present': True,
                   'standby': True,
                   'sandboxer': True,
                   'rounds_played': 1}
        data = {'player': str(self.p1.pk),
                'sandboxer': 'ok',
                'rounds_played': '1'}
        form = PlayerRoundForm(data=data, initial=initial)
        self.assertIs(False, form.is_valid())
        data = {'player': str(self.p1.pk),
                'standby': 'ok',
                'rounds_played': '1'}
        form = PlayerRoundForm(data=data, initial=initial)
        self.assertIs(False, form.is_valid())
        data = {'player': str(self.p1.pk),
                'standby': 'ok',
                'sandboxer': 'ok',
                'rounds_played': '1'}
        form = PlayerRoundForm(data=data, initial=initial)
        self.assertIs(False, form.is_valid())


class BasePlayerRoundFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # We need three Tournaments, one with TournamentPlayers and Rounds,
        # and one finished,
        # and we need at least one Player who isn't playing the Tournament
        today = date.today()
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET)
        cls.r1 = Round.objects.create(tournament=cls.t1,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(cls.t1.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        cls.r2 = Round.objects.create(tournament=cls.t1,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(cls.t1.start_date, time(hour=17, tzinfo=datetime_timezone.utc)))
        cls.t2 = Tournament.objects.create(name='t2',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET)
        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        cls.p2 = Player.objects.create(first_name='Christina', last_name='Dragnet')
        Player.objects.create(first_name='Ethelred', last_name='Fishfinger')
        TournamentPlayer.objects.create(player=cls.p1, tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p2, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p1, the_round=cls.r1)
        cls.t3 = Tournament.objects.create(name='t3',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET)
        cls.r3 = Round.objects.create(tournament=cls.t3,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(cls.t3.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        cls.g = Game.objects.create(name='Test Game',
                                    the_round=cls.r3,
                                    the_set=GameSet.objects.first(),
                                    is_finished=True)

        cls.PlayerRoundFormset = formset_factory(PlayerRoundForm,
                                                 formset=BasePlayerRoundFormset)
        # ManagementForm data
        cls.data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }

    def test_formset_needs_tournament(self):
        with self.assertRaises(KeyError):
            self.PlayerRoundFormset()

    def test_success(self):
        data = self.data.copy()
        data['form-0-player'] = str(self.p1.pk)
        data['form-0-present'] = 'ok'
        data['form-0-standby'] = 'ok'
        data['form-1-player'] = str(self.p2.pk)
        formset = self.PlayerRoundFormset(self.data,
                                          tournament=self.t1)
        self.assertIs(True, formset.is_valid())
        for form in formset:
            with self.subTest(form=form):
                for field in form.fields:
                    if field == 'player':
                        continue
                    # There should be checkboxes for present, standby, and sandboxer
                    # and an integer rounds_played
                    self.assertIn(field, ['present', 'standby', 'sandboxer', 'rounds_played'])

    def test_no_players(self):
        """Should be fine for a Tournament with no TournamentPlayers"""
        formset = self.PlayerRoundFormset(self.data, tournament=self.t2)
        self.assertIs(True, formset.is_valid())

    def test_tournament_over(self):
        """Should be fine for a Tournament that is finished"""
        formset = self.PlayerRoundFormset(self.data, tournament=self.t3)
        self.assertIs(True, formset.is_valid())

    def test_duplicate_players(self):
        """Don't allow the same player to be listed more than once"""
        data = self.data.copy()
        data['form-0-player'] = str(self.p1.pk)
        data['form-0-present'] = 'ok'
        data['form-1-player'] = str(self.p1.pk)
        formset = self.PlayerRoundFormset(data, tournament=self.t2)
        self.assertIs(False, formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, None, None, 'Player Arthur Bottom appears more than once')

    def test_form_error(self):
        """Check that errors in an individual form get handled correctly"""
        data = self.data.copy()
        data['form-0-player'] = str(self.p1.pk)
        data['form-1-player'] = 'Aardvark'
        formset = self.PlayerRoundFormset(data, tournament=self.t2)
        self.assertIs(False, formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)
