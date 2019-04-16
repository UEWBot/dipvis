# Diplomacy Tournament Visualiser
# Copyright (C) 2019 Chris Brand
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
Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import timedelta

from django.forms.formsets import formset_factory
from django.test import TestCase
from django.utils import timezone

from tournament.diplomacy import GreatPower, GameSet, SupplyCentre
from tournament.models import G_SCORING_SYSTEMS
from tournament.models import T_SCORING_SYSTEMS, R_SCORING_SYSTEMS
from tournament.models import Tournament, Round, Game
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
from tournament.players import Player

from tournament.forms import PrefsForm, BasePrefsFormset, DrawForm
from tournament.forms import GameScoreForm, GamePlayersForm, BaseGamePlayersFormset
from tournament.forms import PowerAssignForm, BasePowerAssignFormset
from tournament.forms import GetSevenPlayersForm, SCOwnerForm, BaseSCOwnerFormset
from tournament.forms import SCCountForm, BaseSCCountFormset, GameEndedForm
from tournament.forms import PlayerRoundForm, BasePlayerRoundFormset
from tournament.forms import PlayerRoundScoreForm, BasePlayerRoundScoreFormset

class PrefsFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        p = Player.objects.create(first_name='Arthur', last_name='Bottom')
        t = Tournament.objects.create(name='t1',
                                      start_date=timezone.now(),
                                      end_date=timezone.now(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=Tournament.SECRET)
        cls.tp = TournamentPlayer.objects.create(player=p, tournament=t)

    def test_prefs_form_prefs_field_label(self):
        form = PrefsForm(tp=self.tp)
        self.assertEqual(form.fields['prefs'].label, 'Arthur Bottom')

    def test_prefs_form_prefs_help_text(self):
        form = PrefsForm(tp=self.tp)
        self.assertEqual(form.fields['prefs'].help_text, '')

    def test_prefs_form_prefs_none(self):
        form = PrefsForm(tp=self.tp)
        self.assertEqual(form['prefs'].initial, '')

    def test_prefs_form_prefs_initial(self):
        form = PrefsForm(tp=self.tp, initial={'prefs': 'A'})
        # Explicit initial should override implicit
        self.assertEqual(form['prefs'].initial, 'A')

    def test_prefs_form_prefs_some(self):
        # Add preferences for the TournamentPlayer
        self.tp.create_preferences_from_string('AEF')
        form = PrefsForm(tp=self.tp)
        self.assertEqual(form['prefs'].initial, 'AEF')
        self.tp.preference_set.all().delete()

    def test_prefs_form_prefs_delete(self):
        # Add preferences for the TournamentPlayer
        self.tp.create_preferences_from_string('AEF')
        form = PrefsForm(tp=self.tp, data={'prefs': ''})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['prefs'], '')
        self.tp.preference_set.all().delete()

    def test_prefs_form_prefs_enter_some(self):
        form = PrefsForm(tp=self.tp, data={'prefs': 'EFG'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['prefs'], 'EFG')

class PrefsFormsetTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=timezone.now(),
                                          end_date=timezone.now(),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=Tournament.SECRET)
        p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        p2 = Player.objects.create(first_name='Christina', last_name='Dragnet')
        cls.tp1 = TournamentPlayer.objects.create(player=p1, tournament=cls.t)
        cls.tp2 = TournamentPlayer.objects.create(player=p2, tournament=cls.t)

        cls.PrefsFormset = formset_factory(PrefsForm, extra=0, formset=BasePrefsFormset)

    def test_prefs_formset_creation(self):
        formset = self.PrefsFormset(tournament=self.t)
        tps = set()
        for form in formset:
            self.assertEqual(form['prefs'].initial, form.tp.prefs_string())
            tps.add(form.tp)
        # Both TournamentPlayers should be present
        self.assertEqual(len(formset), 2)
        self.assertIn(self.tp1, tps)
        self.assertIn(self.tp2, tps)

    def test_prefs_formset_initial(self):
        initial = []
        initial.append({'prefs': 'EF'})
        formset = self.PrefsFormset(tournament=self.t, initial=initial)
        # Explicit initial should override implicit
        for form in formset:
            self.assertEqual(form['prefs'].initial, 'EF')
        self.assertEqual(len(formset), len(initial))

class DrawFormTest(TestCase):

    # Common validation method
    def check_common_fields(self, form):
        for field in ('year', 'season', 'proposer'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)

    def test_init_missing_dias(self):
        with self.assertRaises(KeyError):
            DrawForm(secrecy=Tournament.SECRET)

    def test_init_missing_secrecy(self):
        with self.assertRaises(KeyError):
            DrawForm(dias=True)

    def test_init_invalid_secrecy(self):
        with self.assertRaises(AssertionError):
            DrawForm(dias=True, secrecy='Q')

    def test_dias_secret(self):
        form = DrawForm(dias=True, secrecy=Tournament.SECRET)
        # Form should have year, season, proposer, and passed
        self.check_common_fields(form)
        self.assertIn('passed', form.fields)

    def test_non_dias_secret(self):
        form = DrawForm(dias=False, secrecy=Tournament.SECRET)
        # Form should have year, season, proposer, powers, and passed
        self.check_common_fields(form)
        for field in ('powers', 'passed'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)

    def test_dias_counts(self):
        form = DrawForm(dias=True, secrecy=Tournament.COUNTS)
        # Form should have year, season, proposer, and votes_in_favour
        self.check_common_fields(form)
        self.assertIn('votes_in_favour', form.fields)

    def test_non_dias_counts(self):
        form = DrawForm(dias=False, secrecy=Tournament.COUNTS)
        # Form should have year, season, proposer, powers, and votes_in_favour
        self.check_common_fields(form)
        for field in ('powers', 'votes_in_favour'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)

class GameScoreFormTest(TestCase):
    fixtures = ['game_sets.json']

    def test_game_name_field_disabled(self):
        form = GameScoreForm()
        self.assertTrue(form.fields['game_name'].disabled)

    def test_power_fields_exist(self):
        form = GameScoreForm()
        for power in GreatPower.objects.all():
            with self.subTest(power=power.name):
                self.assertIn(power.name, form.fields)

    def test_power_fields_optional(self):
        form = GameScoreForm()
        for power in GreatPower.objects.all():
            with self.subTest(power=power.name):
                self.assertFalse(form.fields[power.name].required)

class GamePlayersFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # We need a Tournament with a Round, and some RoundPlayers to choose from
        # We'll also create some extra TournamentPlayers and Players
        # to ensure that the form doesn't pick them up
        t = Tournament.objects.create(name='t1',
                                      start_date=timezone.now(),
                                      end_date=timezone.now(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=Tournament.SECRET)
        cls.r1 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=t.start_date)
        r2 = Round.objects.create(tournament=t,
                                  scoring_system=G_SCORING_SYSTEMS[0].name,
                                  dias=True,
                                  start=t.start_date + timedelta(hours=8))
        p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        p3 = Player.objects.create(first_name='Christina', last_name='Calculus')
        p4 = Player.objects.create(first_name='Douglas', last_name='Dragnet')
        p7 = Player.objects.create(first_name='Georgette', last_name='Giant')
        p8 = Player.objects.create(first_name='Harold', last_name='Homeless')
        p9 = Player.objects.create(first_name='Irene', last_name='Imp')
        Player.objects.create(first_name='Julia', last_name='Jug')
        # Deliberately create these two out of alphabetical order
        p5 = Player.objects.create(first_name='Edwina', last_name='Eggplant')
        p6 = Player.objects.create(first_name='Frank', last_name='Furious')
        TournamentPlayer.objects.create(player=p1, tournament=t)
        TournamentPlayer.objects.create(player=p2, tournament=t)
        TournamentPlayer.objects.create(player=p3, tournament=t)
        TournamentPlayer.objects.create(player=p4, tournament=t)
        TournamentPlayer.objects.create(player=p5, tournament=t)
        TournamentPlayer.objects.create(player=p6, tournament=t)
        TournamentPlayer.objects.create(player=p7, tournament=t)
        TournamentPlayer.objects.create(player=p8, tournament=t)
        TournamentPlayer.objects.create(player=p9, tournament=t)
        cls.rp1 = RoundPlayer.objects.create(player=p1, the_round=cls.r1)
        cls.rp2 = RoundPlayer.objects.create(player=p2, the_round=cls.r1)
        cls.rp3 = RoundPlayer.objects.create(player=p3, the_round=cls.r1)
        cls.rp5 = RoundPlayer.objects.create(player=p5, the_round=cls.r1)
        cls.rp6 = RoundPlayer.objects.create(player=p6, the_round=cls.r1)
        cls.rp7 = RoundPlayer.objects.create(player=p7, the_round=cls.r1)
        # Again, create this one out of alphabetical order
        cls.rp4 = RoundPlayer.objects.create(player=p4, the_round=cls.r1)
        cls.rp8 = RoundPlayer.objects.create(player=p8, the_round=cls.r1)
        RoundPlayer.objects.create(player=p9, the_round=r2)

    def test_init_needs_round(self):
        with self.assertRaises(KeyError):
            GamePlayersForm()

    def test_game_name_field(self):
        form = GamePlayersForm(the_round=self.r1)
        self.assertIn('game_name', form.fields)

    def test_set_field(self):
        form = GamePlayersForm(the_round=self.r1)
        self.assertIn('the_set', form.fields)

    def test_power_fields(self):
        form = GamePlayersForm(the_round=self.r1)
        for power in GreatPower.objects.all():
            with self.subTest(power=power.name):
                self.assertTrue(form.fields[power.name].required)

    def test_power_choices(self):
        form = GamePlayersForm(the_round=self.r1)
        # Pick a GreatPower at random - they will all be the same
        the_choices = list(form.fields['England'].choices)
        # We should have one per RoundPlayer, plus the initial empty choice
        self.assertEqual(len(the_choices), self.r1.roundplayer_set.count() + 1)
        # The keys should be the RoundPlayer pks
        self.assertEqual(the_choices[1][0], self.rp1.pk)
        # and the values should be the Player names, in alphabetical order
        self.assertEqual(the_choices[1][1], str(self.rp1.player))
        self.assertEqual(the_choices[2][1], str(self.rp2.player))
        self.assertEqual(the_choices[3][1], str(self.rp3.player))
        self.assertEqual(the_choices[4][1], str(self.rp4.player))
        self.assertEqual(the_choices[5][1], str(self.rp5.player))
        self.assertEqual(the_choices[6][1], str(self.rp6.player))
        self.assertEqual(the_choices[7][1], str(self.rp7.player))
        self.assertEqual(the_choices[8][1], str(self.rp8.player))

    def test_success(self):
        data = {'game_name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1)
        self.assertTrue(form.is_valid())

    def test_field_error(self):
        data = {'game_name': 'R1G1',
                'the_set': 'Non-existent set',
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('That choice is not one of the available choices', form.errors['the_set'][0])

    def test_player_error(self):
        data = {'game_name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': 'None',
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('That choice is not one of the available choices', form.errors['France'][0])

    def test_reject_duplicate_players(self):
        data = {'game_name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp1.pk)}
        form = GamePlayersForm(data, the_round=self.r1)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertIn('appears more than once', form.errors['__all__'][0])
        # We should see the Player, not the RoundPlayer, in any error
        self.assertNotIn(str(self.rp1), form.errors['__all__'][0])

class BaseGamePlayersFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        t = Tournament.objects.create(name='t1',
                                      start_date=timezone.now(),
                                      end_date=timezone.now(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=Tournament.SECRET)
        cls.r = Round.objects.create(tournament=t,
                                     scoring_system=G_SCORING_SYSTEMS[0].name,
                                     dias=True,
                                     start=t.start_date)
        # Seven Players, all of whom are playing this Round
        p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        p3 = Player.objects.create(first_name='Christina', last_name='Calculus')
        p4 = Player.objects.create(first_name='Douglas', last_name='Dragnet')
        p5 = Player.objects.create(first_name='Edwina', last_name='Eggplant')
        p6 = Player.objects.create(first_name='Frank', last_name='Furious')
        p7 = Player.objects.create(first_name='Georgette', last_name='Giant')
        TournamentPlayer.objects.create(player=p1, tournament=t)
        TournamentPlayer.objects.create(player=p2, tournament=t)
        TournamentPlayer.objects.create(player=p3, tournament=t)
        TournamentPlayer.objects.create(player=p4, tournament=t)
        TournamentPlayer.objects.create(player=p5, tournament=t)
        TournamentPlayer.objects.create(player=p6, tournament=t)
        TournamentPlayer.objects.create(player=p7, tournament=t)
        cls.rp1 = RoundPlayer.objects.create(player=p1, the_round=cls.r)
        cls.rp2 = RoundPlayer.objects.create(player=p2, the_round=cls.r)
        cls.rp3 = RoundPlayer.objects.create(player=p3, the_round=cls.r)
        cls.rp4 = RoundPlayer.objects.create(player=p4, the_round=cls.r)
        cls.rp5 = RoundPlayer.objects.create(player=p5, the_round=cls.r)
        cls.rp6 = RoundPlayer.objects.create(player=p6, the_round=cls.r)
        cls.rp7 = RoundPlayer.objects.create(player=p7, the_round=cls.r)

        cls.GamePlayersFormset = formset_factory(GamePlayersForm,
                                                 extra=2,
                                                 formset=BaseGamePlayersFormset)
        # ManagementForm data
        cls.data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }

    def test_formset_needs_round(self):
        # Omit the_round constructor parameter
        with self.assertRaises(KeyError):
            self.GamePlayersFormset()

    def test_formset_empty(self):
        # Leave the formset blank
        formset = self.GamePlayersFormset(self.data, the_round=self.r)
        self.assertTrue(formset.is_valid())

    def test_formset_add_one_game(self):
        # Add one Game, leave the other form blank
        data = self.data.copy()
        data['form-0-game_name'] = 'Only Game'
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-Austria-Hungary'] = str(self.rp1.pk)
        data['form-0-England'] = str(self.rp2.pk)
        data['form-0-France'] = str(self.rp3.pk)
        data['form-0-Germany'] = str(self.rp4.pk)
        data['form-0-Italy'] = str(self.rp5.pk)
        data['form-0-Russia'] = str(self.rp6.pk)
        data['form-0-Turkey'] = str(self.rp7.pk)
        formset = self.GamePlayersFormset(data, the_round=self.r)
        self.assertTrue(formset.is_valid())

    def test_formset_form_error(self):
        # Add one Game with an error, leave the other form blank
        data = self.data.copy()
        data['form-0-game_name'] = ''
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-Austria-Hungary'] = str(self.rp1.pk)
        data['form-0-England'] = str(self.rp2.pk)
        data['form-0-France'] = str(self.rp3.pk)
        data['form-0-Germany'] = str(self.rp4.pk)
        data['form-0-Italy'] = str(self.rp5.pk)
        data['form-0-Russia'] = str(self.rp6.pk)
        data['form-0-Turkey'] = str(self.rp7.pk)
        formset = self.GamePlayersFormset(data, the_round=self.r)
        self.assertFalse(formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

    def test_formset_duplicate_game_names(self):
        # Add two Games, with the same name
        GAME_NAME = 'Best Game'
        data = self.data.copy()
        data['form-0-game_name'] = GAME_NAME
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-Austria-Hungary'] = str(self.rp1.pk)
        data['form-0-England'] = str(self.rp2.pk)
        data['form-0-France'] = str(self.rp3.pk)
        data['form-0-Germany'] = str(self.rp4.pk)
        data['form-0-Italy'] = str(self.rp5.pk)
        data['form-0-Russia'] = str(self.rp6.pk)
        data['form-0-Turkey'] = str(self.rp7.pk)
        data['form-1-game_name'] = GAME_NAME
        data['form-1-the_set'] = str(GameSet.objects.first().pk)
        data['form-1-Austria-Hungary'] = str(self.rp7.pk)
        data['form-1-England'] = str(self.rp6.pk)
        data['form-1-France'] = str(self.rp5.pk)
        data['form-1-Germany'] = str(self.rp4.pk)
        data['form-1-Italy'] = str(self.rp3.pk)
        data['form-1-Russia'] = str(self.rp2.pk)
        data['form-1-Turkey'] = str(self.rp1.pk)
        formset = self.GamePlayersFormset(data, the_round=self.r)
        self.assertFalse(formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertIn('Game names must be unique', formset.non_form_errors()[0])

class PowerAssignFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # We need a Tournament with a Round and a Game with seven GamePlayers
        # Add in an extra player for the Round to ensure that they don't get picked up
        t = Tournament.objects.create(name='t1',
                                      start_date=timezone.now(),
                                      end_date=timezone.now(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=Tournament.SECRET)
        r = Round.objects.create(tournament=t,
                                 scoring_system=G_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 start=t.start_date)
        cls.g = Game.objects.create(name='Test Game',
                                    the_round=r,
                                    the_set=GameSet.objects.first())

        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        cls.p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        cls.p3 = Player.objects.create(first_name='Christina', last_name='Calculus')
        cls.p4 = Player.objects.create(first_name='Douglas', last_name='Dragnet')
        cls.p5 = Player.objects.create(first_name='Edwina', last_name='Eggplant')
        cls.p6 = Player.objects.create(first_name='Frank', last_name='Furious')
        cls.p7 = Player.objects.create(first_name='Georgette', last_name='Giant')
        p8 = Player.objects.create(first_name='Harold', last_name='Homeless')
        TournamentPlayer.objects.create(player=cls.p1, tournament=t)
        TournamentPlayer.objects.create(player=cls.p2, tournament=t)
        TournamentPlayer.objects.create(player=cls.p3, tournament=t)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t)
        TournamentPlayer.objects.create(player=cls.p5, tournament=t)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t)
        TournamentPlayer.objects.create(player=p8, tournament=t)
        RoundPlayer.objects.create(player=cls.p1, the_round=r)
        RoundPlayer.objects.create(player=cls.p2, the_round=r)
        RoundPlayer.objects.create(player=cls.p3, the_round=r)
        RoundPlayer.objects.create(player=cls.p4, the_round=r)
        RoundPlayer.objects.create(player=cls.p5, the_round=r)
        RoundPlayer.objects.create(player=cls.p6, the_round=r)
        RoundPlayer.objects.create(player=cls.p7, the_round=r)
        RoundPlayer.objects.create(player=p8, the_round=r)
        cls.gp1 = GamePlayer.objects.create(player=cls.p1, game=cls.g)
        cls.gp2 = GamePlayer.objects.create(player=cls.p2, game=cls.g)
        cls.gp3 = GamePlayer.objects.create(player=cls.p3, game=cls.g)
        cls.gp4 = GamePlayer.objects.create(player=cls.p4, game=cls.g)
        cls.gp5 = GamePlayer.objects.create(player=cls.p5, game=cls.g)
        cls.gp6 = GamePlayer.objects.create(player=cls.p6, game=cls.g)
        cls.gp7 = GamePlayer.objects.create(player=cls.p7, game=cls.g)

    def test_init_needs_game(self):
        with self.assertRaises(KeyError):
            PowerAssignForm()

    def test_game_name_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('game_name', form.fields)

    def test_set_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('the_set', form.fields)

    def test_player_fields(self):
        form = PowerAssignForm(game=self.g)
        for gp in self.g.gameplayer_set.all():
            with self.subTest(gp=str(gp)):
                self.assertTrue(form.fields[gp.pk].required)

    def test_player_choices(self):
        # Each player should have a choice of all seven GreatPowers
        form = PowerAssignForm(game=self.g)
        # Pick a Player at random - they will all be the same
        the_choices = list(form.fields[self.g.gameplayer_set.first().pk].choices)
        # We should have one per GreatPower, plus the initial empty choice
        self.assertEqual(len(the_choices), 8)
        # Key should be the GreatPower pk, value should be the name
        for i, power in enumerate(GreatPower.objects.all(), 1):
            with self.subTest(power=str(power)):
                self.assertEqual(the_choices[i][0], power.pk)
                self.assertEqual(the_choices[i][1], power.name)

    def test_player_labels(self):
        # The label for each power choice shoudl be the Player's name
        form = PowerAssignForm(game=self.g)
        for gp in self.g.gameplayer_set.all():
            with self.subTest(gp=str(gp)):
                self.assertEqual(form.fields[gp.pk].label, str(gp.player))

    def test_success(self):
        data = {'game_name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                self.p1.pk: str(self.turkey.pk),
                self.p2.pk: str(self.austria.pk),
                self.p3.pk: str(self.england.pk),
                self.p4.pk: str(self.france.pk),
                self.p5.pk: str(self.germany.pk),
                self.p6.pk: str(self.italy.pk),
                self.p7.pk: str(self.russia.pk)}
        form = PowerAssignForm(data, game=self.g)
        self.assertTrue(form.is_valid())

    def test_field_error(self):
        data = {'game_name': 'R1G1',
                'the_set': 'Non-existent set',
                self.p1.pk: str(self.turkey.pk),
                self.p2.pk: str(self.austria.pk),
                self.p3.pk: str(self.england.pk),
                self.p4.pk: str(self.france.pk),
                self.p5.pk: str(self.germany.pk),
                self.p6.pk: str(self.italy.pk),
                self.p7.pk: str(self.russia.pk)}
        form = PowerAssignForm(data, game=self.g)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('That choice is not one of the available choices', form.errors['the_set'][0])

    def test_power_error(self):
        data = {'game_name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                self.p1.pk: str(self.turkey.pk),
                self.p2.pk: str(self.austria.pk),
                self.p3.pk: 'None',
                self.p4.pk: str(self.france.pk),
                self.p5.pk: str(self.germany.pk),
                self.p6.pk: str(self.italy.pk),
                self.p7.pk: str(self.russia.pk)}
        form = PowerAssignForm(data, game=self.g)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('That choice is not one of the available choices', form.errors[self.p3.pk][0])

    def test_reject_duplicate_powers(self):
        data = {'game_name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                self.p1.pk: str(self.turkey.pk),
                self.p2.pk: str(self.france.pk),
                self.p3.pk: str(self.england.pk),
                self.p4.pk: str(self.france.pk),
                self.p5.pk: str(self.germany.pk),
                self.p6.pk: str(self.italy.pk),
                self.p7.pk: str(self.russia.pk)}
        form = PowerAssignForm(data, game=self.g)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertIn('appears more than once', form.errors['__all__'][0])

class BasePowerAssignFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # We need two Games with GamePlayers and a Round with no Games
        t = Tournament.objects.create(name='t1',
                                      start_date=timezone.now(),
                                      end_date=timezone.now(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=Tournament.SECRET)
        cls.r1 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=t.start_date)
        cls.r2 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=t.start_date + timedelta(hours=8))
        g1 = Game.objects.create(name='Test Game 1',
                                 the_round=cls.r1,
                                 the_set=GameSet.objects.first())
        g2 = Game.objects.create(name='Test Game 2',
                                 the_round=cls.r1,
                                 the_set=GameSet.objects.first())
        p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        p3 = Player.objects.create(first_name='Christina', last_name='Calculus')
        p4 = Player.objects.create(first_name='Douglas', last_name='Dragnet')
        p5 = Player.objects.create(first_name='Edwina', last_name='Eggplant')
        p6 = Player.objects.create(first_name='Frank', last_name='Furious')
        p7 = Player.objects.create(first_name='Georgette', last_name='Giant')
        TournamentPlayer.objects.create(player=p1, tournament=t)
        TournamentPlayer.objects.create(player=p2, tournament=t)
        TournamentPlayer.objects.create(player=p3, tournament=t)
        TournamentPlayer.objects.create(player=p4, tournament=t)
        TournamentPlayer.objects.create(player=p5, tournament=t)
        TournamentPlayer.objects.create(player=p6, tournament=t)
        TournamentPlayer.objects.create(player=p7, tournament=t)
        RoundPlayer.objects.create(player=p1, the_round=cls.r1)
        RoundPlayer.objects.create(player=p2, the_round=cls.r1)
        RoundPlayer.objects.create(player=p3, the_round=cls.r1)
        RoundPlayer.objects.create(player=p4, the_round=cls.r1)
        RoundPlayer.objects.create(player=p5, the_round=cls.r1)
        RoundPlayer.objects.create(player=p6, the_round=cls.r1)
        RoundPlayer.objects.create(player=p7, the_round=cls.r1)
        cls.gp1 = GamePlayer.objects.create(player=p1, game=g1)
        cls.gp2 = GamePlayer.objects.create(player=p2, game=g1)
        cls.gp3 = GamePlayer.objects.create(player=p3, game=g1)
        cls.gp4 = GamePlayer.objects.create(player=p4, game=g1)
        cls.gp5 = GamePlayer.objects.create(player=p5, game=g1)
        cls.gp6 = GamePlayer.objects.create(player=p6, game=g1)
        cls.gp7 = GamePlayer.objects.create(player=p7, game=g1)
        cls.gp8 = GamePlayer.objects.create(player=p1, game=g2)
        cls.gp9 = GamePlayer.objects.create(player=p2, game=g2)
        cls.gp10 = GamePlayer.objects.create(player=p3, game=g2)
        cls.gp11 = GamePlayer.objects.create(player=p4, game=g2)
        cls.gp12 = GamePlayer.objects.create(player=p5, game=g2)
        cls.gp13 = GamePlayer.objects.create(player=p6, game=g2)
        cls.gp14 = GamePlayer.objects.create(player=p7, game=g2)

        cls.PowerAssignFormset = formset_factory(PowerAssignForm,
                                                 extra=0,
                                                 formset=BasePowerAssignFormset)
        # ManagementForm data
        cls.data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '2',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }
        cls.initial = []
        for game in cls.r1.game_set.all():
            game_dict = {}
            game_dict['game_name'] = game.name
            game_dict['the_set'] = game.the_set
            cls.initial.append(game_dict)

    def test_formset_needs_round(self):
        # Omit the_round constructor parameter
        with self.assertRaises(KeyError):
            self.PowerAssignFormset()

    def test_formset_extra(self):
        # extra must be zero
        PowerAssignFormset = formset_factory(PowerAssignForm,
                                             extra=1,
                                             formset=BasePowerAssignFormset)
        with self.assertRaises(AssertionError):
            PowerAssignFormset(the_round=self.r1)

    def test_formset_no_games(self):
        with self.assertRaises(AssertionError):
            self.PowerAssignFormset(the_round=self.r2)

    def test_formset_success(self):
        # Complete the form correctly
        data = self.data.copy()
        data['form-0-game_name'] = 'Game 1'
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-%d' % self.gp1.pk] = str(self.austria.pk)
        data['form-0-%d' % self.gp2.pk] = str(self.england.pk)
        data['form-0-%d' % self.gp3.pk] = str(self.france.pk)
        data['form-0-%d' % self.gp4.pk] = str(self.germany.pk)
        data['form-0-%d' % self.gp5.pk] = str(self.italy.pk)
        data['form-0-%d' % self.gp6.pk] = str(self.russia.pk)
        data['form-0-%d' % self.gp7.pk] = str(self.turkey.pk)
        data['form-1-game_name'] = 'Game 2'
        data['form-1-the_set'] = str(GameSet.objects.first().pk)
        data['form-1-%d' % self.gp8.pk] = str(self.austria.pk)
        data['form-1-%d' % self.gp9.pk] = str(self.england.pk)
        data['form-1-%d' % self.gp10.pk] = str(self.france.pk)
        data['form-1-%d' % self.gp11.pk] = str(self.germany.pk)
        data['form-1-%d' % self.gp12.pk] = str(self.italy.pk)
        data['form-1-%d' % self.gp13.pk] = str(self.russia.pk)
        data['form-1-%d' % self.gp14.pk] = str(self.turkey.pk)
        formset = self.PowerAssignFormset(data, the_round=self.r1)
        self.assertTrue(formset.is_valid())

    def test_formset_form_error(self):
        # Complete the form with an error in one field
        data = self.data.copy()
        data['form-0-game_name'] = 'Game 1'
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-%d' % self.gp1.pk] = str(self.austria.pk)
        data['form-0-%d' % self.gp2.pk] = str(self.england.pk)
        data['form-0-%d' % self.gp3.pk] = str(self.france.pk)
        data['form-0-%d' % self.gp4.pk] = str(self.germany.pk)
        data['form-0-%d' % self.gp5.pk] = str(self.italy.pk)
        data['form-0-%d' % self.gp6.pk] = str(self.russia.pk)
        data['form-0-%d' % self.gp7.pk] = str(self.turkey.pk)
        data['form-1-game_name'] = 'Ridiculously Long Game Name'
        data['form-1-the_set'] = str(GameSet.objects.first().pk)
        data['form-1-%d' % self.gp8.pk] = str(self.austria.pk)
        data['form-1-%d' % self.gp9.pk] = str(self.england.pk)
        data['form-1-%d' % self.gp10.pk] = str(self.france.pk)
        data['form-1-%d' % self.gp11.pk] = str(self.germany.pk)
        data['form-1-%d' % self.gp12.pk] = str(self.italy.pk)
        data['form-1-%d' % self.gp13.pk] = str(self.russia.pk)
        data['form-1-%d' % self.gp14.pk] = str(self.turkey.pk)
        formset = self.PowerAssignFormset(data, the_round=self.r1)
        self.assertFalse(formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

    def test_formset_duplicate_game_names(self):
        # Give both Games the same name
        GAME_NAME = 'Best Game'
        data = self.data.copy()
        data['form-0-game_name'] = GAME_NAME
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-%d' % self.gp1.pk] = str(self.austria.pk)
        data['form-0-%d' % self.gp2.pk] = str(self.england.pk)
        data['form-0-%d' % self.gp3.pk] = str(self.france.pk)
        data['form-0-%d' % self.gp4.pk] = str(self.germany.pk)
        data['form-0-%d' % self.gp5.pk] = str(self.italy.pk)
        data['form-0-%d' % self.gp6.pk] = str(self.russia.pk)
        data['form-0-%d' % self.gp7.pk] = str(self.turkey.pk)
        data['form-1-game_name'] = GAME_NAME
        data['form-1-the_set'] = str(GameSet.objects.first().pk)
        data['form-1-%d' % self.gp8.pk] = str(self.austria.pk)
        data['form-1-%d' % self.gp9.pk] = str(self.england.pk)
        data['form-1-%d' % self.gp10.pk] = str(self.france.pk)
        data['form-1-%d' % self.gp11.pk] = str(self.germany.pk)
        data['form-1-%d' % self.gp12.pk] = str(self.italy.pk)
        data['form-1-%d' % self.gp13.pk] = str(self.russia.pk)
        data['form-1-%d' % self.gp14.pk] = str(self.turkey.pk)
        formset = self.PowerAssignFormset(data, the_round=self.r1)
        self.assertFalse(formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertIn('Game names must be unique', formset.non_form_errors()[0])

class GetSevenPlayersFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # We need a Tournament, with 2 Rounds, one with an exact multiple of 7,
        # and one without
        t = Tournament.objects.create(name='t1',
                                      start_date=timezone.now(),
                                      end_date=timezone.now(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=Tournament.SECRET)
        cls.r1 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=t.start_date)
        cls.r2 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=t.start_date + timedelta(hours=8))

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
        cls.rp1_5 = RoundPlayer.objects.create(player=p5, the_round=cls.r1)
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

    def test_form_needs_round(self):
        # Omit the_round constructor parameter
        with self.assertRaises(KeyError):
            GetSevenPlayersForm()

    def check_fields(self, prefix, count):
        form = GetSevenPlayersForm(the_round=self.r1)
        for i in range(0, count):
            with self.subTest(i=i):
                name = '%s_%d' % (prefix, i)
                self.assertIn(name, form.fields)
                the_choices = list(form.fields[name].choices)
                # We should have one choice per RoundPlayer, plus the initial empty choice
                self.assertEqual(len(the_choices), self.r1.roundplayer_set.count() + 1)
                # The keys should be the RoundPlayer pks
                self.assertEqual(the_choices[1][0], self.rp1_1.pk)
                # and the values should be the Player names, in alphabetical order
                self.assertEqual(the_choices[1][1], str(self.rp1_1.player))
                self.assertEqual(the_choices[2][1], str(self.rp1_2.player))
                self.assertEqual(the_choices[3][1], str(self.rp1_3.player))
                self.assertEqual(the_choices[4][1], str(self.rp1_4.player))
                self.assertEqual(the_choices[5][1], str(self.rp1_5.player))
                self.assertEqual(the_choices[6][1], str(self.rp1_6.player))
                self.assertEqual(the_choices[7][1], str(self.rp1_7.player))
                self.assertEqual(the_choices[8][1], str(self.rp1_8.player))
                self.assertEqual(the_choices[9][1], str(self.rp1_9.player))
                self.assertEqual(the_choices[10][1], str(self.rp1_10.player))

    def test_sitters_fields(self):
        # We should have 3 fields for players sitting out
        self.check_fields('sitter', 3)

    def test_doubles_fields(self):
        # We should have 4 fields for players playing two games
        self.check_fields('double', 4)

    def test_success_sitters(self):
        # Valid form with people sitting out
        data = {'sitter_0': str(self.rp1_10.pk),
                'sitter_1': str(self.rp1_7.pk),
                'sitter_2': str(self.rp1_3.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1)
        self.assertTrue(form.is_valid())

    def test_success_doublers(self):
        # Valid form with people playing two games
        data = {'double_0': str(self.rp1_10.pk),
                'double_1': str(self.rp1_7.pk),
                'double_2': str(self.rp1_3.pk),
                'double_3': str(self.rp1_4.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1)
        self.assertTrue(form.is_valid())

    def test_existing_sitters(self):
        # Already two people flagged as sitting out the round
        self.rp1_3.game_count = 0
        self.rp1_3.save()
        self.rp1_4.game_count = 0
        self.rp1_4.save()
        form = GetSevenPlayersForm(the_round=self.r1)
        # They should be listed as a sitter
        self.assertEqual(form['sitter_0'].initial, self.rp1_3)
        self.assertEqual(form['sitter_1'].initial, self.rp1_4)
        # Clean up changes made
        self.rp1_3.game_count = 1
        self.rp1_3.save()
        self.rp1_4.game_count = 1
        self.rp1_4.save()

    def test_existing_doublers(self):
        # Already two people flagged as playing two games
        self.rp1_3.game_count = 2
        self.rp1_3.save()
        self.rp1_4.game_count = 2
        self.rp1_4.save()
        form = GetSevenPlayersForm(the_round=self.r1)
        # They should be listed as a doubler
        self.assertEqual(form['double_0'].initial, self.rp1_3)
        self.assertEqual(form['double_1'].initial, self.rp1_4)
        # Clean up changes made
        self.rp1_3.game_count = 1
        self.rp1_3.save()
        self.rp1_4.game_count = 1
        self.rp1_4.save()

    def test_sitting_twice(self):
        # One person listed twice as sitting out
        data = {'sitter_0': str(self.rp1_10.pk),
                'sitter_1': str(self.rp1_3.pk),
                'sitter_2': str(self.rp1_3.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertIn('appears more than once', form.errors['__all__'][0])

    def test_doubling_twice(self):
        # One person listed twice as playing two games
        data = {'double_0': str(self.rp1_10.pk),
                'double_1': str(self.rp1_7.pk),
                'double_2': str(self.rp1_10.pk),
                'double_3': str(self.rp1_4.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertIn('appears more than once', form.errors['__all__'][0])

    def test_provide_both(self):
        # Both people sitting out and people playing two boards
        data = {'sitter_0': str(self.rp1_1.pk),
                'sitter_1': str(self.rp1_2.pk),
                'sitter_2': str(self.rp1_3.pk),
                'double_0': str(self.rp1_4.pk),
                'double_1': str(self.rp1_5.pk),
                'double_2': str(self.rp1_6.pk),
                'double_3': str(self.rp1_7.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Either have players sit out', form.errors['__all__'][0])

    def test_too_few_sitters(self):
        data = {'sitter_0': str(self.rp1_10.pk),
                'sitter_1': str(self.rp1_7.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Too few players sitting out', form.errors['__all__'][0])

    def test_too_few_doublers(self):
        data = {'double_0': str(self.rp1_10.pk),
                'double_1': str(self.rp1_7.pk),
                'double_2': str(self.rp1_3.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Too few players playing two', form.errors['__all__'][0])

    def test_none_needed(self):
        # Exact multiple of seven already
        form = GetSevenPlayersForm(the_round=self.r2)
        # Nothing needed
        self.assertEqual(len(form.fields), 0)

class SCOwnerFormTest(TestCase):
    fixtures = ['game_sets.json']

    def test_field_count(self):
        form = SCOwnerForm()
        self.assertEqual(len(form.fields), 1 + SupplyCentre.objects.count())

    def test_required(self):
        form = SCOwnerForm()
        for field in form.fields:
            with self.subTest(field=field):
                if field == 'year':
                    self.assertTrue(form.fields[field].required)
                else:
                    self.assertFalse(form.fields[field].required)

    def test_year_1900(self):
        # 1900 should be accepted
        form = SCOwnerForm(data={'year': 1900})
        self.assertTrue(form.is_valid())

    def test_year_1899(self):
        # 1899 should not be accepted
        form = SCOwnerForm(data={'year': 1899})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Ensure this value is greater than', form.errors['year'][0])

class BaseSCOwnerFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        cls.SCOwnerFormset = formset_factory(SCOwnerForm,
                                             formset=BaseSCOwnerFormset)
        # ManagementForm data
        cls.data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }
        cls.row_data = {}
        for sc in SupplyCentre.objects.all():
            cls.row_data[sc.name] = sc.initial_owner

    def test_success(self):
        # Everything is ok
        data = self.data.copy()
        for i in range(2):
            for key, val in self.row_data.items():
                if val:
                    data['form-%d-%s' % (i, key)] = val.pk
            data['form-%d-year' % i] = 1902 + i
        data['form-0-Belgium'] = self.france.pk
        data['form-1-Belgium'] = self.germany.pk
        formset = self.SCOwnerFormset(data)
        self.assertTrue(formset.is_valid())

    def test_leave_one_form_blank(self):
        # Everything is ok, one form left blank
        data = self.data.copy()
        for key, val in self.row_data.items():
            if val:
                data['form-0-%s' % key] = val.pk
        data['form-0-year'] = 1904
        data['form-0-Belgium'] = self.france.pk
        formset = self.SCOwnerFormset(data)
        self.assertTrue(formset.is_valid())

    def test_form_error(self):
        # Error in one of the forms
        data = self.data.copy()
        for i in range(2):
            for key, val in self.row_data.items():
                if val:
                    data['form-%d-%s' % (i, key)] = val.pk
            # First year will be 1899, which is invalid
            data['form-%d-year' % i] = 1899 + i
        data['form-0-Belgium'] = self.france.pk
        data['form-1-Belgium'] = self.germany.pk
        formset = self.SCOwnerFormset(data)
        self.assertFalse(formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

    def test_duplicate_year(self):
        # Duplicate years
        data = self.data.copy()
        for i in range(2):
            for key, val in self.row_data.items():
                if val:
                    data['form-%d-%s' % (i, key)] = val.pk
            data['form-%d-year' % i] = 1902
        data['form-0-Belgium'] = self.france.pk
        data['form-1-Belgium'] = self.germany.pk
        formset = self.SCOwnerFormset(data)
        self.assertFalse(formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertIn('appears more than once', formset.non_form_errors()[0])

    def test_scs_become_neutral(self):
        # SC changes from owned to neutral
        data = self.data.copy()
        for i in range(2):
            for key, val in self.row_data.items():
                if val:
                    data['form-%d-%s' % (i, key)] = val.pk
            data['form-%d-year' % i] = 1902 + i
        data['form-0-Belgium'] = self.france.pk
        formset = self.SCOwnerFormset(data)
        self.assertFalse(formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertIn('should never change from owned', formset.errors[1]['Belgium'][0])

class GameEndedFormTest(TestCase):

    def test_is_finished_not_required(self):
        form = GameEndedForm()
        self.assertFalse(form.fields['is_finished'].required)

class SCCountFormTest(TestCase):
    fixtures = ['game_sets.json']

    def test_success(self):
        # Everything is ok
        data = {'year': 1902,
                'Austria-Hungary': 5,
                'England': 6,
                'France': 6,
                'Germany': 2,
                'Italy': 5,
                'Russia': 4,
                'Turkey': 5,
               }
        form = SCCountForm(data=data)
        self.assertTrue(form.is_valid())

    def test_year_1900(self):
        # 1900 should be accepted
        data = {'year': 1900,
                'Austria-Hungary': 5,
                'England': 6,
                'France': 6,
                'Germany': 2,
                'Italy': 5,
                'Russia': 4,
                'Turkey': 5,
               }
        form = SCCountForm(data=data)
        self.assertTrue(form.is_valid())

    def test_year_1899(self):
        # 1899 should not be accepted
        data = {'year': 1899,
                'Austria-Hungary': 5,
                'England': 6,
                'France': 6,
                'Germany': 2,
                'Italy': 5,
                'Russia': 4,
                'Turkey': 5,
               }
        form = SCCountForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Ensure this value is greater than', form.errors['year'][0])

    def test_negative_sc_count(self):
        # One power has lost more than all their dots
        data = {'year': 1905,
                'Austria-Hungary': 4,
                'England': 5,
                'France': -1,
                'Germany': 5,
                'Italy': 4,
                'Russia': 4,
                'Turkey': 4,
               }
        form = SCCountForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Ensure this value is greater than', form.errors['France'][0])

    def test_power_with_too_many_dots(self):
        # One power has more than all the dots
        data = {'year': 1920,
                'Austria-Hungary': 0,
                'England': 0,
                'France': 0,
                'Germany': 0,
                'Italy': 35,
                'Russia': 0,
                'Turkey': 0,
               }
        form = SCCountForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Ensure this value is less than', form.errors['Italy'][0])

    def test_too_many_dots_in_total(self):
        # More than 34 in total
        data = {'year': 1920,
                'Austria-Hungary': 5,
                'England': 5,
                'France': 5,
                'Germany': 5,
                'Italy': 5,
                'Russia': 5,
                'Turkey': 5,
               }
        form = SCCountForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # This includes non-field errors
        self.assertEqual(len(form.errors), 1)

    def test_fake_neutral_field(self):
        # Ensure that the extra 'neutral' field gets added
        data = {'year': 1902,
                'Austria-Hungary': 5,
                'England': 6,
                'France': 6,
                'Germany': 2,
                'Italy': 5,
                'Russia': 4,
                'Turkey': 5,
               }
        form = SCCountForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['neutral'], 1)

class BaseSCCountFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        cls.SCCountFormset = formset_factory(SCCountForm,
                                             formset=BaseSCCountFormset)
        # ManagementForm data
        cls.data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }

    def test_success(self):
        # Everything is ok
        data = self.data.copy()
        for i in range(2):
            data['form-%d-Austria-Hungary' % i] = 4 + i
            data['form-%d-England' % i] = 4 + i
            data['form-%d-France' % i] = 4 + i
            data['form-%d-Germany' % i] = 4 + i
            data['form-%d-Italy' % i] = 4 + i
            data['form-%d-Russia' % i] = 3 + i
            data['form-%d-Turkey' % i] = 4 + i
            data['form-%d-year' % i] = 1902 + i
        formset = self.SCCountFormset(data)
        self.assertTrue(formset.is_valid())

    def test_one_form_blank(self):
        # One form left empty
        data = self.data.copy()
        data['form-0-Austria-Hungary'] = 4
        data['form-0-England'] = 4
        data['form-0-France'] = 4
        data['form-0-Germany'] = 4
        data['form-0-Italy'] = 4
        data['form-0-Russia'] = 3
        data['form-0-Turkey'] = 4
        data['form-0-year'] = 1902
        formset = self.SCCountFormset(data)
        self.assertTrue(formset.is_valid())

    def test_form_error(self):
        # Something wrong in one of the forms
        data = self.data.copy()
        for i in range(2):
            data['form-%d-Austria-Hungary' % i] = 4 + i
            data['form-%d-England' % i] = 4 + i
            data['form-%d-France' % i] = 4 + i
            data['form-%d-Germany' % i] = 4 + i
            data['form-%d-Italy' % i] = 4 + i
            data['form-%d-Russia' % i] = 3 + i
            # Negative SC counts are not allowed
            data['form-%d-Turkey' % i] = i - 1
            data['form-%d-year' % i] = 1902 + i
        formset = self.SCCountFormset(data)
        self.assertFalse(formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

    def test_duplicate_year(self):
        # One year is repeated
        data = self.data.copy()
        for i in range(2):
            data['form-%d-Austria-Hungary' % i] = 4 + i
            data['form-%d-England' % i] = 4 + i
            data['form-%d-France' % i] = 4 + i
            data['form-%d-Germany' % i] = 4 + i
            data['form-%d-Italy' % i] = 4 + i
            data['form-%d-Russia' % i] = 3 + i
            data['form-%d-Turkey' % i] = 4 + i
            data['form-%d-year' % i] = 1902
        formset = self.SCCountFormset(data)
        self.assertFalse(formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertIn('appears more than once', formset.non_form_errors()[0])

    def test_neutrals_increase(self):
        # SupplyCentres become neutral
        data = self.data.copy()
        for i in range(2):
            data['form-%d-Austria-Hungary' % i] = 4
            data['form-%d-England' % i] = 4
            data['form-%d-France' % i] = 4
            data['form-%d-Germany' % i] = 4
            data['form-%d-Italy' % i] = 4
            data['form-%d-Russia' % i] = 3
            data['form-%d-year' % i] = 1902 + i
        data['form-0-Turkey'] = 5
        data['form-1-Turkey'] = 3
        formset = self.SCCountFormset(data)
        self.assertFalse(formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertIn('Neutrals increase', formset.non_form_errors()[0])

class PlayerRoundFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # We need a Player and a Tournament
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=timezone.now(),
                                          end_date=timezone.now(),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=Tournament.SECRET)

        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')

    def test_form_needs_first_round_num(self):
        # Omit first_round_num constructor parameter
        with self.assertRaises(KeyError):
            PlayerRoundForm(last_round_num=3, this_round_num=1)

    def test_form_needs_last_round_num(self):
        # Omit last_round_num constructor parameter
        with self.assertRaises(KeyError):
            PlayerRoundForm(first_round_num=1, this_round_num=1)

    def test_form_needs_this_round_num(self):
        # Omit this_round_num constructor parameter
        with self.assertRaises(KeyError):
            PlayerRoundForm(first_round_num=1, last_round_num=2)

    def test_success(self):
        # Do everything right
        data = {'player': str(self.p1.pk),
                'round_2': 'on'}
        initial = {'player': self.p1,
                   'round_1': False}
        form = PlayerRoundForm(data,
                               initial=initial,
                               first_round_num=1,
                               last_round_num=2,
                               this_round_num=1)
        self.assertTrue(form.is_valid())

    def test_round_fields(self):
        # Check that the correct round fields are created
        form = PlayerRoundForm(first_round_num=1,
                               last_round_num=3,
                               this_round_num=2)
        # We should have three round fields, numbered 1, 2, and 3
        self.assertEqual(len(form.fields), 4)
        # Just the first should be disabled
        self.assertTrue(form.fields['round_1'].disabled)
        self.assertFalse(form.fields['round_2'].disabled)
        self.assertFalse(form.fields['round_3'].disabled)

class BasePlayerRoundFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # We need three Tournaments, one with TournamentPlayers and Rounds,
        # and one finished,
        # and we need at least one Player who isn't playing the Tournament
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=timezone.now(),
                                           end_date=timezone.now(),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET)
        cls.r1 = Round.objects.create(tournament=cls.t1,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=cls.t1.start_date)
        cls.r2 = Round.objects.create(tournament=cls.t1,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=cls.t1.start_date + timedelta(hours=8))
        cls.t2 = Tournament.objects.create(name='t2',
                                           start_date=timezone.now(),
                                           end_date=timezone.now(),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET)
        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        cls.p2 = Player.objects.create(first_name='Christina', last_name='Dragnet')
        Player.objects.create(first_name='Ethelred', last_name='Fishfinger')
        TournamentPlayer.objects.create(player=cls.p1, tournament=cls.t1)
        TournamentPlayer.objects.create(player=cls.p2, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p1, the_round=cls.r1)
        cls.t3 = Tournament.objects.create(name='t3',
                                           start_date=timezone.now(),
                                           end_date=timezone.now(),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET)
        cls.r3 = Round.objects.create(tournament=cls.t3,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=cls.t3.start_date)
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
        # Everything is ok
        data = self.data.copy()
        data['form-0-player'] = str(self.p1.pk)
        data['form-0-round_1'] = 'ok'
        data['form-1-player'] = str(self.p2.pk)
        formset = self.PlayerRoundFormset(self.data, tournament=self.t1)
        self.assertTrue(formset.is_valid())

    def test_success_single_round(self):
        # Single round roll call
        data = self.data.copy()
        data['form-0-player'] = str(self.p1.pk)
        data['form-0-round_1'] = 'ok'
        data['form-1-player'] = str(self.p2.pk)
        ROUND_NUM = 2
        formset = self.PlayerRoundFormset(self.data,
                                          round_num=ROUND_NUM,
                                          tournament=self.t1)
        self.assertTrue(formset.is_valid())
        for form in formset:
            with self.subTest(form=form):
                for field in form.fields:
                    if field == 'player':
                        continue
                    # The only checkbox shoudl be for round_num
                    self.assertEqual(field, 'round_%d' % ROUND_NUM)

    def test_no_players(self):
        # Should be fine for a Tournament with no TournamentPlayers
        formset = self.PlayerRoundFormset(self.data, tournament=self.t2)
        self.assertTrue(formset.is_valid())

    def test_tournament_over(self):
        # Should be fine for a Tournament that is finished
        formset = self.PlayerRoundFormset(self.data, tournament=self.t3)
        self.assertTrue(formset.is_valid())
        # All checkboxes should be disabled
        for form in formset:
            with self.subTest(form=form):
                for field in form.fields:
                    if field == 'player':
                        continue
                    with self.subTest(field=field):
                        self.assertTrue(form.fields[field].disabled)

    def test_duplicate_players(self):
        # Don't allow the same player to be listed more than once
        data = self.data.copy()
        data['form-0-player'] = str(self.p1.pk)
        data['form-0-round_1'] = 'ok'
        data['form-1-player'] = str(self.p1.pk)
        formset = self.PlayerRoundFormset(data, tournament=self.t2)
        self.assertFalse(formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertIn('appears more than once', formset.non_form_errors()[0])

    def test_form_error(self):
        # Check that errors in an individual form get handled correctly
        data = self.data.copy()
        data['form-0-player'] = str(self.p1.pk)
        data['form-1-player'] = 'Aardvark'
        formset = self.PlayerRoundFormset(data, tournament=self.t2)
        self.assertFalse(formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

class PlayerRoundScoreFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # We need a Player and a Tournament
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=timezone.now(),
                                          end_date=timezone.now(),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=Tournament.SECRET)

        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        cls.tp1 = TournamentPlayer.objects.create(player=cls.p1, tournament=cls.t)

    def test_form_needs_tournament(self):
        # Omit tournament constructor parameter
        with self.assertRaises(KeyError):
            PlayerRoundScoreForm(rounds=2, this_round=1)

    def test_form_needs_rounds(self):
        # Omit rounds constructor parameter
        with self.assertRaises(KeyError):
            PlayerRoundScoreForm(tournament=self.t, this_round=1)

    def test_form_needs_this_round(self):
        # Omit this_round constructor parameter
        with self.assertRaises(KeyError):
            PlayerRoundScoreForm(tournament=self.t, rounds=2)

    def test_success(self):
        # Everything is ok
        initial = {'tp': self.t.tournamentplayer_set.first(),
                   'player': str(self.p1.pk),
                  }
        form = PlayerRoundScoreForm({'tp': str(self.t.tournamentplayer_set.first().pk)},
                                    initial=initial,
                                    tournament=self.t,
                                    rounds=2,
                                    this_round=1)
        self.assertTrue(form.is_valid())

    def test_fields_disabled(self):
        # Many fields should be disabled
        initial = {'tp': self.tp1,
                   'player': str(self.p1.pk),
                  }
        form = PlayerRoundScoreForm(initial=initial,
                                    tournament=self.t,
                                    rounds=3,
                                    this_round=2)
        for field in ['player', 'round_1', 'game_scores_2', 'game_scores_3']:
            with self.subTest(field=field):
                self.assertTrue(form.fields[field].disabled)

class BasePlayerRoundScoreFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # We need three Tournaments, one with TournamentPlayers and Rounds,
        # and one that is over
        p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        p2 = Player.objects.create(first_name='Christina', last_name='Dragnet')
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=timezone.now(),
                                           end_date=timezone.now(),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET)
        r1 = Round.objects.create(tournament=cls.t1,
                                  scoring_system=G_SCORING_SYSTEMS[0].name,
                                  dias=True,
                                  start=cls.t1.start_date)
        Round.objects.create(tournament=cls.t1,
                             scoring_system=G_SCORING_SYSTEMS[0].name,
                             dias=True,
                             start=cls.t1.start_date + timedelta(hours=8))
        TournamentPlayer.objects.create(player=p1, tournament=cls.t1)
        TournamentPlayer.objects.create(player=p2, tournament=cls.t1)
        RoundPlayer.objects.create(player=p1, the_round=r1)
        cls.t2 = Tournament.objects.create(name='t2',
                                           start_date=timezone.now(),
                                           end_date=timezone.now(),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET)
        cls.t3 = Tournament.objects.create(name='t3',
                                           start_date=timezone.now(),
                                           end_date=timezone.now(),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET)
        r3 = Round.objects.create(tournament=cls.t3,
                                  scoring_system=G_SCORING_SYSTEMS[0].name,
                                  dias=True,
                                  start=cls.t3.start_date)
        Game.objects.create(name='Test Game',
                            the_round=r3,
                            the_set=GameSet.objects.first(),
                            is_finished=True)
        TournamentPlayer.objects.create(player=p1, tournament=cls.t3)

        cls.PlayerRoundScoreFormset = formset_factory(PlayerRoundScoreForm,
                                                      extra=0,
                                                      formset=BasePlayerRoundScoreFormset)
        # ManagementForm data
        cls.data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '2',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }

    def test_formset_needs_tournament(self):
        # Omit tournament kwarg
        with self.assertRaises(KeyError):
            self.PlayerRoundScoreFormset()

    def test_success(self):
        # All ok
        data = self.data.copy()
        data['form-0-tp'] = str(self.t1.tournamentplayer_set.first().pk)
        data['form-0-round_1'] = '105.3'
        data['form-0-overall_score'] = '105.3'
        data['form-1-tp'] = str(self.t1.tournamentplayer_set.last().pk)
        data['form-TOTAL_FORMS'] = str(self.t1.tournamentplayer_set.count())
        initial = []
        for tp in self.t1.tournamentplayer_set.all():
            initial.append({'tp': tp,
                            'player': tp.player,
                            'round_1': 3.5,
                            'overall_score': 3.5,
                           })
        formset = self.PlayerRoundScoreFormset(data, initial=initial, tournament=self.t1)
        self.assertTrue(formset.is_valid())

    def test_no_players(self):
        # Should be fine for a Tournament with no TournamentPlayers
        data = {
            'form-TOTAL_FORMS': '0',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }
        formset = self.PlayerRoundScoreFormset(data, tournament=self.t2)
        self.assertTrue(formset.is_valid())

    def test_finished(self):
        # Should be fine for a completed Tournament
        data = self.data.copy()
        data['form-0-tp'] = str(self.t3.tournamentplayer_set.first().pk)
        data['form-0-round_1'] = '105.3'
        data['form-0-overall_score'] = '105.3'
        data['form-TOTAL_FORMS'] = str(self.t3.tournamentplayer_set.count())
        initial = []
        for tp in self.t3.tournamentplayer_set.all():
            initial.append({'tp': tp,
                            'player': tp.player,
                            'round_1': 3.5,
                            'overall_score': 3.5,
                           })
        formset = self.PlayerRoundScoreFormset(data, initial=initial, tournament=self.t3)
        self.assertTrue(formset.is_valid())
