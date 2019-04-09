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

from tournament.diplomacy import GreatPower, GameSet
from tournament.models import SECRET, COUNTS, G_SCORING_SYSTEMS
from tournament.models import T_SCORING_SYSTEMS, R_SCORING_SYSTEMS, SECRET
from tournament.models import Tournament, Round, Game
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
from tournament.players import Player

from tournament.forms import PrefsForm, BasePrefsFormset, DrawForm
from tournament.forms import GameScoreForm, GamePlayersForm, BaseGamePlayersFormset
from tournament.forms import PowerAssignForm

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
                                      draw_secrecy=SECRET)
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
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=timezone.now(),
                                          end_date=timezone.now(),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=SECRET)
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
    fixtures = ['game_sets.json']

    # Common validation method
    def check_common_fields(self, form):
        for field in ('year', 'season', 'proposer'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)

    def test_init_missing_dias(self):
        with self.assertRaises(KeyError):
            DrawForm(secrecy=SECRET)

    def test_init_missing_secrecy(self):
        with self.assertRaises(KeyError):
            DrawForm(dias=True)

    def test_init_invalid_secrecy(self):
        with self.assertRaises(AssertionError):
            DrawForm(dias=True, secrecy='Q')

    def test_dias_secret(self):
        form = DrawForm(dias=True, secrecy=SECRET)
        # Form should have year, season, proposer, and passed
        self.check_common_fields(form)
        self.assertIn('passed', form.fields)

    def test_non_dias_secret(self):
        form = DrawForm(dias=False, secrecy=SECRET)
        # Form should have year, season, proposer, powers, and passed
        self.check_common_fields(form)
        for field in ('powers', 'passed'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)

    def test_dias_counts(self):
        form = DrawForm(dias=True, secrecy=COUNTS)
        # Form should have year, season, proposer, and votes_in_favour
        self.check_common_fields(form)
        self.assertIn('votes_in_favour', form.fields)

    def test_non_dias_counts(self):
        form = DrawForm(dias=False, secrecy=COUNTS)
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
        HOURS_8 = timedelta(hours=8)
        t = Tournament.objects.create(name='t1',
                                      start_date=timezone.now(),
                                      end_date=timezone.now(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=SECRET)
        cls.r1 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=t.start_date)
        r2 = Round.objects.create(tournament=t,
                                  scoring_system=G_SCORING_SYSTEMS[0].name,
                                  dias=True,
                                  start=t.start_date + HOURS_8)
        p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        p3 = Player.objects.create(first_name='Christina', last_name='Calculus')
        p4 = Player.objects.create(first_name='Douglas', last_name='Dragnet')
        p7 = Player.objects.create(first_name='Georgette', last_name='Giant')
        p8 = Player.objects.create(first_name='Harold', last_name='Homeless')
        p9 = Player.objects.create(first_name='Irene', last_name='Imp')
        p10 = Player.objects.create(first_name='Julia', last_name='Jug')
        # Deliberately create these two out of alphabetical order
        p5 = Player.objects.create(first_name='Edwina', last_name='Eggplant')
        p6 = Player.objects.create(first_name='Frank', last_name='Furious')
        tp1 = TournamentPlayer.objects.create(player=p1, tournament=t)
        tp2 = TournamentPlayer.objects.create(player=p2, tournament=t)
        tp3 = TournamentPlayer.objects.create(player=p3, tournament=t)
        tp4 = TournamentPlayer.objects.create(player=p4, tournament=t)
        tp5 = TournamentPlayer.objects.create(player=p5, tournament=t)
        tp6 = TournamentPlayer.objects.create(player=p6, tournament=t)
        tp7 = TournamentPlayer.objects.create(player=p7, tournament=t)
        tp8 = TournamentPlayer.objects.create(player=p8, tournament=t)
        tp9 = TournamentPlayer.objects.create(player=p9, tournament=t)
        cls.rp1 = RoundPlayer.objects.create(player=p1, the_round=cls.r1)
        cls.rp2 = RoundPlayer.objects.create(player=p2, the_round=cls.r1)
        cls.rp3 = RoundPlayer.objects.create(player=p3, the_round=cls.r1)
        cls.rp5 = RoundPlayer.objects.create(player=p5, the_round=cls.r1)
        cls.rp6 = RoundPlayer.objects.create(player=p6, the_round=cls.r1)
        cls.rp7 = RoundPlayer.objects.create(player=p7, the_round=cls.r1)
        # Again, create this one out of alphabetical order
        cls.rp4 = RoundPlayer.objects.create(player=p4, the_round=cls.r1)
        cls.rp8 = RoundPlayer.objects.create(player=p8, the_round=cls.r1)
        rp9 = RoundPlayer.objects.create(player=p9, the_round=r2)

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
                                      draw_secrecy=SECRET)
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
        tp1 = TournamentPlayer.objects.create(player=p1, tournament=t)
        tp2 = TournamentPlayer.objects.create(player=p2, tournament=t)
        tp3 = TournamentPlayer.objects.create(player=p3, tournament=t)
        tp4 = TournamentPlayer.objects.create(player=p4, tournament=t)
        tp5 = TournamentPlayer.objects.create(player=p5, tournament=t)
        tp6 = TournamentPlayer.objects.create(player=p6, tournament=t)
        tp7 = TournamentPlayer.objects.create(player=p7, tournament=t)
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
        HOURS_8 = timedelta(hours=8)
        t = Tournament.objects.create(name='t1',
                                      start_date=timezone.now(),
                                      end_date=timezone.now(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=SECRET)
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
        tp1 = TournamentPlayer.objects.create(player=cls.p1, tournament=t)
        tp2 = TournamentPlayer.objects.create(player=cls.p2, tournament=t)
        tp3 = TournamentPlayer.objects.create(player=cls.p3, tournament=t)
        tp4 = TournamentPlayer.objects.create(player=cls.p4, tournament=t)
        tp5 = TournamentPlayer.objects.create(player=cls.p5, tournament=t)
        tp6 = TournamentPlayer.objects.create(player=cls.p6, tournament=t)
        tp7 = TournamentPlayer.objects.create(player=cls.p7, tournament=t)
        tp8 = TournamentPlayer.objects.create(player=p8, tournament=t)
        rp1 = RoundPlayer.objects.create(player=cls.p1, the_round=r)
        rp2 = RoundPlayer.objects.create(player=cls.p2, the_round=r)
        rp3 = RoundPlayer.objects.create(player=cls.p3, the_round=r)
        rp4 = RoundPlayer.objects.create(player=cls.p4, the_round=r)
        rp5 = RoundPlayer.objects.create(player=cls.p5, the_round=r)
        rp6 = RoundPlayer.objects.create(player=cls.p6, the_round=r)
        rp7 = RoundPlayer.objects.create(player=cls.p7, the_round=r)
        rp8 = RoundPlayer.objects.create(player=p8, the_round=r)
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


