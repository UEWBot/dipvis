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
from datetime import date, datetime, time, timedelta, timezone

from django.forms.formsets import formset_factory
from django.test import TestCase

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.models.supply_centre import SupplyCentre
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import T_SCORING_SYSTEMS, R_SCORING_SYSTEMS
from tournament.models import DrawSecrecy
from tournament.models import Award, Tournament, Round, Game, Team
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
from tournament.players import Player

from tournament.forms import AwardsForm, BaseAwardsFormset, HandicapForm, BaseHandicapsFormset
from tournament.forms import PrefsForm, BasePrefsFormset, DrawForm, DeathYearForm
from tournament.forms import GameScoreForm, GamePlayersForm, BaseGamePlayersFormset
from tournament.forms import PaidForm, BasePaidFormset
from tournament.forms import PowerAssignForm, BasePowerAssignFormset
from tournament.forms import GetSevenPlayersForm, SCOwnerForm, BaseSCOwnerFormset
from tournament.forms import SCCountForm, BaseSCCountFormset, GameEndedForm
from tournament.forms import PlayerForm
from tournament.forms import PlayerRoundForm, BasePlayerRoundFormset
from tournament.forms import PlayerRoundScoreForm, BasePlayerRoundScoreFormset
from tournament.forms import SeederBiasForm
from tournament.forms import TeamForm, BaseTeamsFormset


class AwardsFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        # One Player who didn't participate
        Player.objects.create(first_name='Charlotte', last_name='Dotty')
        p3 = Player.objects.create(first_name='Edward', last_name='Foxtrot')
        p4 = Player.objects.create(first_name='Georgette', last_name='Halitosis')
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)
        cls.a1 = Award.objects.create(name='Nicest Player',
                                      description='Player who was the nicest')
        cls.tp1 = TournamentPlayer.objects.create(player=p3, tournament=cls.t)
        # Include one unranked player, who shouldn't be pickable
        cls.tp2 = TournamentPlayer.objects.create(player=p4, tournament=cls.t, unranked=True)
        cls.tp3 = TournamentPlayer.objects.create(player=p1, tournament=cls.t)
        cls.t.awards.add(cls.a1)
        cls.t.save()

    def test_init_needs_tournament(self):
        with self.assertRaises(KeyError):
            AwardsForm(award_name=str(self.a1))

    def test_init_needs_award_name(self):
        with self.assertRaises(KeyError):
            AwardsForm(tournament=self.t)

    def test_awards_form_player_field_label(self):
        form = AwardsForm(tournament=self.t, award_name=str(self.a1))
        self.assertEqual(form.fields['players'].label, str(self.a1))

    def test_awards_form_player_choices(self):
        form = AwardsForm(tournament=self.t, award_name=str(self.a1))
        the_choices = list(form.fields['players'].choices)
        # We should have one per TournamentPlayer
        self.assertEqual(len(the_choices), self.t.tournamentplayer_set.filter(unranked=False).count())
        # The keys should be the TournamentPlayer pks
        self.assertEqual(the_choices[0][0].value, self.tp3.pk)
        # and the values should be the Player names, in alphabetical order
        self.assertEqual(the_choices[0][1], self.tp3.player.sortable_str())
        self.assertEqual(the_choices[1][1], self.tp1.player.sortable_str())


class AwardsFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)
        p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        p2 = Player.objects.create(first_name='Christina', last_name='Dragnet')
        p3 = Player.objects.create(first_name='Edwin', last_name='Flubber')
        cls.tp1 = TournamentPlayer.objects.create(player=p1, tournament=cls.t)
        cls.tp2 = TournamentPlayer.objects.create(player=p2, tournament=cls.t)
        cls.tp3 = TournamentPlayer.objects.create(player=p3, tournament=cls.t)
        cls.a1 = Award.objects.create(name='Nicest Player',
                                      description='Player who was the nicest')
        cls.a2 = Award.objects.create(name='Best Austria',
                                      description='Who got the best result playing Austria',
                                      power=GreatPower.objects.get(abbreviation='A'))
        cls.a3 = Award.objects.create(name='Tallest Player',
                                      description='Player of unusual size')
        cls.t.awards.add(cls.a1)
        cls.t.awards.add(cls.a2)
        cls.t.awards.add(cls.a3)
        cls.t.save()
        cls.tp1.awards.add(cls.a1)
        cls.tp2.awards.add(cls.a2)
        cls.tp3.awards.add(cls.a2)

        cls.AwardsFormset = formset_factory(AwardsForm, extra=0, formset=BaseAwardsFormset)

    def test_awards_formset_creation(self):
        formset = self.AwardsFormset(tournament=self.t)
        awards = set()
        for form in formset:
            with self.subTest(award=form['award'].initial):
                if form['award'].initial == self.a1.id:
                    self.assertEqual(form['players'].initial, [self.tp1.id])
                elif form['award'].initial == self.a2.id:
                    self.assertEqual(form['players'].initial, [self.tp2.id, self.tp3.id])
                else:
                    self.assertEqual(form['players'].initial, [])
            awards.add(form['award'].initial)
        # All three Awards should be present
        self.assertEqual(len(formset), 3)
        self.assertIn(self.a1.id, awards)
        self.assertIn(self.a2.id, awards)
        self.assertIn(self.a3.id, awards)

    def test_awards_formset_initial(self):
        initial = []
        initial.append({'award': self.a1.id, 'players': [self.tp2.id]})
        formset = self.AwardsFormset(tournament=self.t, initial=initial)
        # Explicit initial should override implicit
        for form in formset:
            self.assertEqual(form['players'].initial, [self.tp2.id])
        self.assertEqual(len(formset), len(initial))


class PaidFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        p = Player.objects.create(first_name='Arthur', last_name='Bottom')
        today = date.today()
        t = Tournament.objects.create(name='t1',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        cls.tp = TournamentPlayer.objects.create(player=p, tournament=t, paid=False)

    def test_paid_form_paid_field_label(self):
        form = PaidForm(tp=self.tp)
        self.assertEqual(form.fields['paid'].label, 'Arthur Bottom')

    def test_paid_form_none(self):
        form = PaidForm(tp=self.tp)
        self.assertEqual(form['paid'].initial, False)

    def test_paid_form_paid_initial(self):
        form = PaidForm(tp=self.tp, initial={'paid': True})
        # Explicit initial should override implicit
        self.assertEqual(form['paid'].initial, True)


class PaidFormsetTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)
        p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        p2 = Player.objects.create(first_name='Christina', last_name='Dragnet')
        cls.tp1 = TournamentPlayer.objects.create(player=p1, tournament=cls.t)
        cls.tp2 = TournamentPlayer.objects.create(player=p2, tournament=cls.t)

        cls.PaidFormset = formset_factory(PaidForm, extra=0, formset=BasePaidFormset)

    def test_paid_formset_creation(self):
        formset = self.PaidFormset(tournament=self.t)
        tps = set()
        for form in formset:
            self.assertEqual(form['paid'].initial, form.tp.paid)
            tps.add(form.tp)
        # Both TournamentPlayers should be present
        self.assertEqual(len(formset), 2)
        self.assertIn(self.tp1, tps)
        self.assertIn(self.tp2, tps)

    def test_paid_formset_initial(self):
        initial = []
        initial.append({'paid': True})
        formset = self.PaidFormset(tournament=self.t, initial=initial)
        # Explicit initial should override implicit
        for form in formset:
            self.assertEqual(form['paid'].initial, True)
        self.assertEqual(len(formset), len(initial))


class PrefsFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        p = Player.objects.create(first_name='Arthur', last_name='Bottom')
        today = date.today()
        t = Tournament.objects.create(name='t1',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
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
        """Add preferences for the TournamentPlayer"""
        self.tp.create_preferences_from_string('AEF')
        form = PrefsForm(tp=self.tp)
        self.assertEqual(form['prefs'].initial, 'AEF')
        self.tp.preference_set.all().delete()

    def test_prefs_form_prefs_delete(self):
        """Remove preferences for the TournamentPlayer"""
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
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)
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


class HandicapFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        p = Player.objects.create(first_name='Arthur', last_name='Bottom')
        today = date.today()
        t = Tournament.objects.create(name='t1',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        cls.tp = TournamentPlayer.objects.create(player=p, tournament=t, handicap = 0.0)

    def test_handicap_form_handicap_field_label(self):
        form = HandicapForm(tp=self.tp)
        self.assertEqual(form.fields['handicap'].label, 'Arthur Bottom')

    def test_handicap_form_handicap_help_text(self):
        form = HandicapForm(tp=self.tp)
        self.assertEqual(form.fields['handicap'].help_text, '')

    def test_handicap_form_handicap_initial(self):
        form = HandicapForm(tp=self.tp, initial={'handicap': 17.5})
        # Explicit initial should override implicit
        self.assertAlmostEqual(form['handicap'].initial, 17.5)

    def test_handicap_form_handicap_exists(self):
        """Add handicap for the TournamentPlayer"""
        self.tp.handicap = 72.0
        self.tp.save()
        form = HandicapForm(tp=self.tp)
        self.assertAlmostEqual(form['handicap'].initial, 72.0)
        # Cleanup
        self.tp.handicap = 0.0
        self.tp.save()

    def test_handicap_form_handicap_change(self):
        """Change handicap for the TournamentPlayer"""
        self.tp.handicap = 72.0
        self.tp.save()
        form = HandicapForm(tp=self.tp, data={'handicap': '5.0'})
        self.assertTrue(form.is_valid())
        self.assertAlmostEqual(form.cleaned_data['handicap'], 5.0)
        # Cleanup
        self.tp.handicap = 0.0
        self.tp.save()


class HandicapsFormsetTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)
        p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        p2 = Player.objects.create(first_name='Christina', last_name='Dragnet')
        cls.tp1 = TournamentPlayer.objects.create(player=p1, tournament=cls.t, handicap=50.0)
        cls.tp2 = TournamentPlayer.objects.create(player=p2, tournament=cls.t, handicap=5.0)

        cls.HandicapsFormset = formset_factory(HandicapForm, extra=0, formset=BaseHandicapsFormset)

    def test_handicaps_formset_creation(self):
        formset = self.HandicapsFormset(tournament=self.t)
        tps = set()
        for form in formset:
            self.assertAlmostEqual(form['handicap'].initial, form.tp.handicap)
            tps.add(form.tp)
        # Both TournamentPlayers should be present
        self.assertEqual(len(formset), 2)
        self.assertIn(self.tp1, tps)
        self.assertIn(self.tp2, tps)

    def test_handicaps_formset_initial(self):
        initial = []
        initial.append({'handicap': '10.0'})
        formset = self.HandicapsFormset(tournament=self.t, initial=initial)
        # Explicit initial should override implicit
        for form in formset:
            self.assertEqual(form['handicap'].initial, '10.0')
        self.assertEqual(len(formset), len(initial))


class TeamFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        cls.p2 = Player.objects.create(first_name='Catherine', last_name='Dirigible')
        p3 = Player.objects.create(first_name='Ethel', last_name='Felony')
        # This one isn't in the tournament
        cls.p4 = Player.objects.create(first_name='Gregory', last_name='Human')
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET,
                                          team_size=3)
        TournamentPlayer.objects.create(player=cls.p1, tournament=cls.t)
        TournamentPlayer.objects.create(player=cls.p2, tournament=cls.t)
        TournamentPlayer.objects.create(player=p3, tournament=cls.t)
        # Single team with a single player
        cls.tm = Team.objects.create(tournament=cls.t, name='The Team')
        cls.tm.players.add(cls.p2)

    def test_team_form_player_fields_required(self):
        """One player should be required, others optional"""
        form = TeamForm(tournament=self.t)
        self.assertTrue(form.fields['player_0'].required)
        for i in range(1,self.t.team_size):
            self.assertFalse(form.fields[f'player_{i}'].required)

    def test_team_form_players_optional(self):
        """One player should be required, others optional"""
        form = TeamForm(tournament=self.t, data={'name': 'Sausages',
                                                 'player_0': str(self.p1.pk)})
        self.assertTrue(form.is_valid())

    def test_team_form_existing_team(self):
        """team kwarg should be supported"""
        form = TeamForm(tournament=self.t, team=self.tm)

    def test_team_repeated_player(self):
        """Same player can't appear more than once in a team"""
        form = TeamForm(tournament=self.t, data={'name': 'Sausages',
                                                 'player_0': str(self.p2.pk),
                                                 'player_1': str(self.p1.pk),
                                                 'player_2': str(self.p1.pk)})
        self.assertFalse(form.is_valid())
        self.assertFormError(form, None, 'Player Arthur Bottom appears more than once')

    def test_team_invalid_player(self):
        """Team includes a player who isn't playing the Tournament"""
        form = TeamForm(tournament=self.t, data={'name': 'Sausages',
                                                 'player_0': str(self.p2.pk),
                                                 'player_1': str(self.p1.pk),
                                                 'player_2': str(self.p4.pk)})
        self.assertFalse(form.is_valid())
        self.assertFormError(form,
                             'player_2',
                             'Select a valid choice. That choice is not one of the available choices.')


class TeamsFormsetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        cls.p2 = Player.objects.create(first_name='Catherine', last_name='Dirigible')
        cls.p3 = Player.objects.create(first_name='Ethel', last_name='Felony')
        cls.p4 = Player.objects.create(first_name='Gregory', last_name='Human')
        # This one isn't in the tournament
        cls.p5 = Player.objects.create(first_name='Iris', last_name='Jogger')
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET,
                                          team_size=2)
        TournamentPlayer.objects.create(player=cls.p1, tournament=cls.t)
        TournamentPlayer.objects.create(player=cls.p2, tournament=cls.t)
        TournamentPlayer.objects.create(player=cls.p3, tournament=cls.t)
        TournamentPlayer.objects.create(player=cls.p4, tournament=cls.t)
        # Single team with a single player
        cls.tm = Team.objects.create(tournament=cls.t, name='The Team')
        cls.tm.players.add(cls.p2)

        cls.TeamsFormset = formset_factory(TeamForm, extra=2, formset=BaseTeamsFormset)

    def test_teams_success(self):
        data = {'form-TOTAL_FORMS': '2',
                'form-INITIAL_FORMS': '1',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-name': 'Team 0',
                'form-0-player_0': str(self.p1.pk),
                'form-0-player_1': str(self.p2.pk),
                'form-1-name': 'Team 1',
                'form-1-player_0': str(self.p3.pk),
                'form-1-player_1': str(self.p4.pk),
               }
        formset = self.TeamsFormset(data, tournament=self.t)
        self.assertTrue(formset.is_valid())

    def test_teams_invalid_form(self):
        """One form fails validation"""
        data = {'form-TOTAL_FORMS': '2',
                'form-INITIAL_FORMS': '1',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-name': 'Team 0',
                'form-0-player_0': str(self.p1.pk),
                'form-0-player_1': str(self.p1.pk),
                'form-1-name': 'Team 1',
                'form-1-player_0': str(self.p3.pk),
                'form-1-player_1': str(self.p2.pk),
               }
        formset = self.TeamsFormset(data, tournament=self.t)
        self.assertFalse(formset.is_valid())
        # Should have one form error, and that's it
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

    def test_teams_invalid_player(self):
        """One player isn't playing the tournament"""
        data = {'form-TOTAL_FORMS': '2',
                'form-INITIAL_FORMS': '1',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-name': 'Team 0',
                'form-0-player_0': str(self.p1.pk),
                'form-0-player_1': str(self.p5.pk),
                'form-1-name': 'Team 1',
                'form-1-player_0': str(self.p3.pk),
                'form-1-player_1': str(self.p2.pk),
               }
        formset = self.TeamsFormset(data, tournament=self.t)
        self.assertFalse(formset.is_valid())
        # Should have one form error, and that's it
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

    def test_teams_duplicate_player(self):
        """Player playing for multiple Teams"""
        data = {'form-TOTAL_FORMS': '2',
                'form-INITIAL_FORMS': '1',
                'form-MAX_NUM_FORMS': '1000',
                'form-MIN_NUM_FORMS': '0',
                'form-0-name': 'Team 0',
                'form-0-player_0': str(self.p1.pk),
                'form-0-player_1': str(self.p2.pk),
                'form-1-name': 'Team 1',
                'form-1-player_0': str(self.p3.pk),
                'form-1-player_1': str(self.p1.pk),
               }
        formset = self.TeamsFormset(data, tournament=self.t)
        self.assertFalse(formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, None, None, 'Player Arthur Bottom appears in multiple teams')


class DrawFormTest(TestCase):

    # Common validation method
    def check_common_fields(self, form):
        for field in ('year', 'season', 'proposer'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)

    def test_init_missing_dias(self):
        with self.assertRaises(KeyError):
            DrawForm(secrecy=DrawSecrecy.SECRET,
                     player_count=7,
                     concession=False)

    def test_init_missing_player_count(self):
        with self.assertRaises(KeyError):
            DrawForm(secrecy=DrawSecrecy.SECRET,
                     dias=False,
                     concession=False)

    def test_init_missing_concession(self):
        with self.assertRaises(KeyError):
            DrawForm(dias=True,
                     player_count=6,
                     secrecy=DrawSecrecy.SECRET)

    def test_init_missing_secrecy(self):
        with self.assertRaises(KeyError):
            DrawForm(dias=True,
                     player_count=6,
                     concession=False)

    def test_init_invalid_secrecy(self):
        with self.assertRaises(AssertionError):
            DrawForm(dias=True,
                     secrecy='Q',
                     player_count=7,
                     concession=False)

    def test_dias_secret(self):
        form = DrawForm(dias=True,
                        secrecy=DrawSecrecy.SECRET,
                        player_count=7,
                        concession=False)
        # Form should have year, season, proposer, and passed
        self.check_common_fields(form)
        self.assertIn('passed', form.fields)
        for field in ('powers', 'votes_in_favour'):
            with self.subTest(field=field):
                self.assertNotIn(field, form.fields)

    def test_non_dias_secret(self):
        form = DrawForm(dias=False,
                        secrecy=DrawSecrecy.SECRET,
                        player_count=7,
                        concession=False)
        # Form should have year, season, proposer, powers, and passed
        self.check_common_fields(form)
        for field in ('powers', 'passed'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)
        self.assertNotIn('votes_in_favour', form.fields)

    def test_dias_counts(self):
        form = DrawForm(dias=True,
                        secrecy=DrawSecrecy.COUNTS,
                        player_count=7,
                        concession=False)
        # Form should have year, season, proposer, and votes_in_favour
        self.check_common_fields(form)
        self.assertIn('votes_in_favour', form.fields)
        for field in ('powers', 'passed'):
            with self.subTest(field=field):
                self.assertNotIn(field, form.fields)

    def test_non_dias_counts(self):
        form = DrawForm(dias=False,
                        secrecy=DrawSecrecy.COUNTS,
                        player_count=7,
                        concession=False)
        # Form should have year, season, proposer, powers, and votes_in_favour
        self.check_common_fields(form)
        for field in ('powers', 'votes_in_favour'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)
        self.assertNotIn('passed', form.fields)

    def test_concession_secret(self):
        form = DrawForm(dias=True,
                        secrecy=DrawSecrecy.SECRET,
                        player_count=7,
                        concession=True)
        # Form should have year, season, proposer, powers, and passed
        self.check_common_fields(form)
        for field in ('powers', 'passed'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)
        for field in ('votes_in_favour'):
            with self.subTest(field=field):
                self.assertNotIn(field, form.fields)

    def test_concession_counts(self):
        form = DrawForm(dias=True,
                        secrecy=DrawSecrecy.COUNTS,
                        player_count=7,
                        concession=True)
        # Form should have year, season, proposer, powers, and votes_in_favour
        self.check_common_fields(form)
        for field in ('powers', 'votes_in_favour'):
            with self.subTest(field=field):
                self.assertIn(field, form.fields)
        for field in ('passed'):
            with self.subTest(field=field):
                self.assertNotIn(field, form.fields)

    def test_proposer_optional(self):
        form = DrawForm(dias=False,
                        secrecy=DrawSecrecy.COUNTS,
                        player_count=7,
                        concession=False)
        self.assertFalse(form.fields['proposer'].required)


class GameScoreFormTest(TestCase):
    fixtures = ['game_sets.json']

    def test_name_field_disabled(self):
        form = GameScoreForm()
        self.assertTrue(form.fields['name'].disabled)

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
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)
        cls.r1 = Round.objects.create(tournament=cls.t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(cls.t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r2 = Round.objects.create(tournament=cls.t,
                                  scoring_system=G_SCORING_SYSTEMS[0].name,
                                  dias=True,
                                  start=datetime.combine(cls.t.start_date, time(hour=17, tzinfo=timezone.utc)))
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
        TournamentPlayer.objects.create(player=p1, tournament=cls.t)
        TournamentPlayer.objects.create(player=p2, tournament=cls.t)
        TournamentPlayer.objects.create(player=p3, tournament=cls.t)
        TournamentPlayer.objects.create(player=p4, tournament=cls.t)
        TournamentPlayer.objects.create(player=p5, tournament=cls.t)
        TournamentPlayer.objects.create(player=p6, tournament=cls.t)
        TournamentPlayer.objects.create(player=p7, tournament=cls.t)
        TournamentPlayer.objects.create(player=p8, tournament=cls.t)
        TournamentPlayer.objects.create(player=p9, tournament=cls.t)
        cls.rp1 = RoundPlayer.objects.create(player=p1, the_round=cls.r1)
        cls.rp2 = RoundPlayer.objects.create(player=p2, the_round=cls.r1)
        cls.rp3 = RoundPlayer.objects.create(player=p3, the_round=cls.r1, sandboxer=True)
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

    def test_game_id_field(self):
        form = GamePlayersForm(the_round=self.r1)
        self.assertIn('game_id', form.fields)

    def test_name_field(self):
        form = GamePlayersForm(the_round=self.r1)
        self.assertIn('name', form.fields)

    def test_set_field(self):
        form = GamePlayersForm(the_round=self.r1)
        self.assertIn('the_set', form.fields)

    def test_url_field(self):
        form = GamePlayersForm(the_round=self.r1)
        self.assertIn('external_url', form.fields)

    def test_notes_field(self):
        form = GamePlayersForm(the_round=self.r1)
        self.assertIn('notes', form.fields)

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
        self.assertEqual(the_choices[1][1], self.rp1.player.sortable_str())
        self.assertEqual(the_choices[2][1], self.rp2.player.sortable_str())
        # Sandboxers should be flagged
        self.assertEqual(the_choices[3][1], self.rp3.player.sortable_str()+'*')
        self.assertEqual(the_choices[4][1], self.rp4.player.sortable_str())
        self.assertEqual(the_choices[5][1], self.rp5.player.sortable_str())
        self.assertEqual(the_choices[6][1], self.rp6.player.sortable_str())
        self.assertEqual(the_choices[7][1], self.rp7.player.sortable_str())
        self.assertEqual(the_choices[8][1], self.rp8.player.sortable_str())

    def test_success(self):
        data = {'name': 'R1G1',
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

    def test_success_with_id(self):
        data = {'name': 'R1G1',
                'game_id': '17',
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

    def test_name_error1(self):
        data = {'name': 'R1 G1',
                'the_set': str(GameSet.objects.first().pk),
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
        self.assertIn('Game names cannot contain ', form.errors['name'][0])

    def test_name_error2(self):
        data = {'name': 'R1/G1',
                'the_set': str(GameSet.objects.first().pk),
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
        self.assertIn('Game names cannot contain ', form.errors['name'][0])

    def test_field_error(self):
        data = {'name': 'R1G1',
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
        data = {'name': 'R1G1',
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
        data = {'name': 'R1G1',
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

    def test_teammates_in_team_round(self):
        """Players from the same team in the same game in a team round"""
        self.t.team_size = 2
        self.t.save()
        self.r1.is_team_round = True
        self.r1.save()
        tm = Team.objects.create(tournament=self.t,
                                 name="The test team")
        tm.players.add(self.rp2.player)
        tm.players.add(self.rp4.player)
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Multiple players from team', form.errors['__all__'][0])
        # We should see the Player, not the RoundPlayer, in any error
        self.assertNotIn(str(self.rp2), form.errors['__all__'][0])
        # Cleanup
        tm.delete()
        self.t.team_size = None
        self.t.save()
        self.r1.is_team_round = False
        self.r1.save()

    def test_non_teammates_in_team_round(self):
        """No players from the same team in the same game in a team round"""
        self.t.team_size = 2
        self.t.save()
        self.r1.is_team_round = True
        self.r1.save()
        tm1 = Team.objects.create(tournament=self.t,
                                 name="The test team")
        tm1.players.add(self.rp2.player)
        tm2 = Team.objects.create(tournament=self.t,
                                 name="Another test team")
        tm2.players.add(self.rp4.player)
        data = {'name': 'R1G1',
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
        # Cleanup
        tm1.delete()
        tm2.delete()
        self.t.team_size = None
        self.t.save()
        self.r1.is_team_round = False
        self.r1.save()

    def test_teammates_in_non_team_round(self):
        """Players from the same team in the same game in a non-team round"""
        self.t.team_size = 2
        self.t.save()
        tm = Team.objects.create(tournament=self.t,
                                 name="The test team")
        tm.players.add(self.rp2.player)
        tm.players.add(self.rp4.player)
        data = {'name': 'R1G1',
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
        # Cleanup
        tm.delete()
        self.t.team_size = None
        self.t.save()


class BaseGamePlayersFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        today = date.today()
        t = Tournament.objects.create(name='t1',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        cls.r = Round.objects.create(tournament=t,
                                     scoring_system=G_SCORING_SYSTEMS[0].name,
                                     dias=True,
                                     start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
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
        """Omit the_round constructor parameter"""
        with self.assertRaises(KeyError):
            self.GamePlayersFormset()

    def test_formset_empty(self):
        """Leave the formset blank"""
        formset = self.GamePlayersFormset(self.data, the_round=self.r)
        self.assertTrue(formset.is_valid())

    def test_formset_add_one_game(self):
        """Add one Game, leave the other form blank"""
        data = self.data.copy()
        data['form-0-name'] = 'OnlyGame'
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
        """Add one Game with an error, leave the other form blank"""
        data = self.data.copy()
        data['form-0-name'] = ''
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

    def test_formset_duplicate_names(self):
        """Add two Games, with the same name"""
        GAME_NAME = 'BestGame'
        data = self.data.copy()
        data['form-0-name'] = GAME_NAME
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-Austria-Hungary'] = str(self.rp1.pk)
        data['form-0-England'] = str(self.rp2.pk)
        data['form-0-France'] = str(self.rp3.pk)
        data['form-0-Germany'] = str(self.rp4.pk)
        data['form-0-Italy'] = str(self.rp5.pk)
        data['form-0-Russia'] = str(self.rp6.pk)
        data['form-0-Turkey'] = str(self.rp7.pk)
        data['form-1-name'] = GAME_NAME
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
        today = date.today()
        t = Tournament.objects.create(name='t1',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        r = Round.objects.create(tournament=t,
                                 scoring_system=G_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
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
        RoundPlayer.objects.create(player=cls.p3, the_round=r, sandboxer=True)
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

    def test_name_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('name', form.fields)

    def test_set_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('the_set', form.fields)

    def test_url_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('external_url', form.fields)

    def test_notes_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('notes', form.fields)

    def test_player_fields(self):
        form = PowerAssignForm(game=self.g)
        for gp in self.g.gameplayer_set.all():
            with self.subTest(gp=str(gp)):
                self.assertTrue(form.fields[str(gp.pk)].required)

    def test_issues_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('issues', form.fields)
        self.assertTrue(form.fields['issues'].disabled)

    def test_player_choices(self):
        """Each player should have a choice of all seven GreatPowers"""
        form = PowerAssignForm(game=self.g)
        # Pick a Player at random - they will all be the same
        the_choices = list(form.fields[str(self.g.gameplayer_set.first().pk)].choices)
        # We should have one per GreatPower, plus the initial empty choice
        self.assertEqual(len(the_choices), 8)
        # Key should be the GreatPower pk, value should be the name
        for i, power in enumerate(GreatPower.objects.all(), 1):
            with self.subTest(power=str(power)):
                self.assertEqual(the_choices[i][0], power.pk)
                self.assertEqual(the_choices[i][1], power.name)

    def test_player_labels(self):
        """The label for each power choice should be the Player's name"""
        form = PowerAssignForm(game=self.g)
        for gp in self.g.gameplayer_set.all():
            with self.subTest(gp=str(gp)):
                # Sandboxers should be flagged
                if gp.roundplayer().sandboxer:
                    self.assertEqual(form.fields[str(gp.pk)].label, str(gp.player)+'*')
                else:
                    self.assertEqual(form.fields[str(gp.pk)].label, str(gp.player))

    def test_success(self):
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.austria.pk),
                str(self.gp3.pk): str(self.england.pk),
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data, game=self.g)
        self.assertTrue(form.is_valid())

    def test_name_error1(self):
        data = {'name': 'R1 G1',
                'the_set': str(GameSet.objects.first().pk),
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.austria.pk),
                str(self.gp3.pk): str(self.england.pk),
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data, game=self.g)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Game names cannot contain ', form.errors['name'][0])

    def test_name_error2(self):
        data = {'name': 'R1/G1',
                'the_set': str(GameSet.objects.first().pk),
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.austria.pk),
                str(self.gp3.pk): str(self.england.pk),
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data, game=self.g)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Game names cannot contain ', form.errors['name'][0])

    def test_field_error(self):
        data = {'name': 'R1G1',
                'the_set': 'Non-existent set',
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.austria.pk),
                str(self.gp3.pk): str(self.england.pk),
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data, game=self.g)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('That choice is not one of the available choices', form.errors['the_set'][0])

    def test_power_error(self):
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.austria.pk),
                str(self.gp3.pk): 'None',
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data, game=self.g)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, str(self.gp3.pk), 'Select a valid choice. That choice is not one of the available choices.')

    def test_reject_duplicate_powers(self):
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.france.pk),
                str(self.gp3.pk): str(self.england.pk),
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
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
                                      start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        cls.r2 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(t.start_date, time(hour=17, tzinfo=timezone.utc)))
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
            game_dict['name'] = game.name
            game_dict['the_set'] = game.the_set
            cls.initial.append(game_dict)

    def test_formset_needs_round(self):
        """Omit the_round constructor parameter"""
        with self.assertRaises(KeyError):
            self.PowerAssignFormset()

    def test_formset_extra(self):
        """extra must be zero"""
        PowerAssignFormset = formset_factory(PowerAssignForm,
                                             extra=1,
                                             formset=BasePowerAssignFormset)
        with self.assertRaises(AssertionError):
            PowerAssignFormset(the_round=self.r1)

    def test_formset_no_games(self):
        with self.assertRaises(AssertionError):
            self.PowerAssignFormset(the_round=self.r2)

    def test_formset_success(self):
        """Complete the form correctly"""
        data = self.data.copy()
        data['form-0-name'] = 'Game1'
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-%d' % self.gp1.pk] = str(self.austria.pk)
        data['form-0-%d' % self.gp2.pk] = str(self.england.pk)
        data['form-0-%d' % self.gp3.pk] = str(self.france.pk)
        data['form-0-%d' % self.gp4.pk] = str(self.germany.pk)
        data['form-0-%d' % self.gp5.pk] = str(self.italy.pk)
        data['form-0-%d' % self.gp6.pk] = str(self.russia.pk)
        data['form-0-%d' % self.gp7.pk] = str(self.turkey.pk)
        data['form-0-issues'] = ''
        data['form-1-name'] = 'Game2'
        data['form-1-the_set'] = str(GameSet.objects.first().pk)
        data['form-1-%d' % self.gp8.pk] = str(self.austria.pk)
        data['form-1-%d' % self.gp9.pk] = str(self.england.pk)
        data['form-1-%d' % self.gp10.pk] = str(self.france.pk)
        data['form-1-%d' % self.gp11.pk] = str(self.germany.pk)
        data['form-1-%d' % self.gp12.pk] = str(self.italy.pk)
        data['form-1-%d' % self.gp13.pk] = str(self.russia.pk)
        data['form-1-%d' % self.gp14.pk] = str(self.turkey.pk)
        data['form-1-issues'] = ''
        formset = self.PowerAssignFormset(data, the_round=self.r1)
        self.assertTrue(formset.is_valid())

    def test_formset_form_error(self):
        """Complete the form with an error in one field"""
        data = self.data.copy()
        data['form-0-name'] = 'Game1'
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-%d' % self.gp1.pk] = str(self.austria.pk)
        data['form-0-%d' % self.gp2.pk] = str(self.england.pk)
        data['form-0-%d' % self.gp3.pk] = str(self.france.pk)
        data['form-0-%d' % self.gp4.pk] = str(self.germany.pk)
        data['form-0-%d' % self.gp5.pk] = str(self.italy.pk)
        data['form-0-%d' % self.gp6.pk] = str(self.russia.pk)
        data['form-0-%d' % self.gp7.pk] = str(self.turkey.pk)
        data['form-0-issues'] = ''
        data['form-1-name'] = 'RidiculouslyLongGameName'
        data['form-1-the_set'] = str(GameSet.objects.first().pk)
        data['form-1-%d' % self.gp8.pk] = str(self.austria.pk)
        data['form-1-%d' % self.gp9.pk] = str(self.england.pk)
        data['form-1-%d' % self.gp10.pk] = str(self.france.pk)
        data['form-1-%d' % self.gp11.pk] = str(self.germany.pk)
        data['form-1-%d' % self.gp12.pk] = str(self.italy.pk)
        data['form-1-%d' % self.gp13.pk] = str(self.russia.pk)
        data['form-1-%d' % self.gp14.pk] = str(self.turkey.pk)
        data['form-1-issues'] = ''
        formset = self.PowerAssignFormset(data, the_round=self.r1)
        self.assertFalse(formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

    def test_formset_duplicate_names(self):
        """Give both Games the same name"""
        GAME_NAME = 'BestGame'
        data = self.data.copy()
        data['form-0-name'] = GAME_NAME
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-%d' % self.gp1.pk] = str(self.austria.pk)
        data['form-0-%d' % self.gp2.pk] = str(self.england.pk)
        data['form-0-%d' % self.gp3.pk] = str(self.france.pk)
        data['form-0-%d' % self.gp4.pk] = str(self.germany.pk)
        data['form-0-%d' % self.gp5.pk] = str(self.italy.pk)
        data['form-0-%d' % self.gp6.pk] = str(self.russia.pk)
        data['form-0-%d' % self.gp7.pk] = str(self.turkey.pk)
        data['form-0-issues'] = ''
        data['form-1-name'] = GAME_NAME
        data['form-1-the_set'] = str(GameSet.objects.first().pk)
        data['form-1-%d' % self.gp8.pk] = str(self.austria.pk)
        data['form-1-%d' % self.gp9.pk] = str(self.england.pk)
        data['form-1-%d' % self.gp10.pk] = str(self.france.pk)
        data['form-1-%d' % self.gp11.pk] = str(self.germany.pk)
        data['form-1-%d' % self.gp12.pk] = str(self.italy.pk)
        data['form-1-%d' % self.gp13.pk] = str(self.russia.pk)
        data['form-1-%d' % self.gp14.pk] = str(self.turkey.pk)
        data['form-1-issues'] = ''
        formset = self.PowerAssignFormset(data, the_round=self.r1)
        self.assertFalse(formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertIn('Game names must be unique', formset.non_form_errors()[0])


class GetSevenPlayersFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # We need a Tournament, with 4 Rounds, one with an exact multiple of 7 (round 2),
        # one that needs all standby players plus some to play two boards (round 1),
        # one that needs all the standby players to play (round 4),
        # and one that needs a subset of the standby players to play (round 3)
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
                                      start=datetime.combine(t.start_date, time(hour=8, tzinfo=timezone.utc)))
        cls.r2 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(t.start_date, time(hour=12, tzinfo=timezone.utc)))
        cls.r3 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(t.start_date, time(hour=16, tzinfo=timezone.utc)))
        cls.r4 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(t.start_date, time(hour=20, tzinfo=timezone.utc)))

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
            GetSevenPlayersForm()

    def test_sitters_fields(self):
        """We should have 2 fields for players sitting out"""
        prefix='sitter'
        form = GetSevenPlayersForm(the_round=self.r1)
        for i in range(0, 2):
            with self.subTest(i=i):
                name = '%s_%d' % (prefix, i)
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

    def test_doubles_fields(self):
        """We should have 4 fields for players playing two games"""
        prefix='double'
        form = GetSevenPlayersForm(the_round=self.r1)
        for i in range(0, 4):
            with self.subTest(i=i):
                name = '%s_%d' % (prefix, i)
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

    def test_no_standbys_fields(self):
        """We should have no standby fields if all standby players are needed"""
        form = GetSevenPlayersForm(the_round=self.r1)
        name = 'standby_0'
        self.assertNotIn(name, form.fields)

    def test_success_sitters(self):
        """Valid form with people sitting out"""
        data = {'sitter_0': str(self.rp1_10.pk),
                'sitter_1': str(self.rp1_7.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1)
        self.assertTrue(form.is_valid())

    def test_success_doublers(self):
        """Valid form with people playing two games"""
        data = {'double_0': str(self.rp1_10.pk),
                'double_1': str(self.rp1_7.pk),
                'double_2': str(self.rp1_3.pk),
                'double_3': str(self.rp1_4.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r1)
        self.assertTrue(form.is_valid())

    def test_existing_sitters(self):
        """Already two people flagged as sitting out the round"""
        self.rp1_3.game_count = 0
        self.rp1_3.save(update_fields=['game_count'])
        self.rp1_4.game_count = 0
        self.rp1_4.save(update_fields=['game_count'])
        form = GetSevenPlayersForm(the_round=self.r1)
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
        form = GetSevenPlayersForm(the_round=self.r1)
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
        form = GetSevenPlayersForm(data, the_round=self.r1)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertIn('appears more than once', form.errors['__all__'][0])

    def test_doubling_twice(self):
        """One person listed twice as playing two games"""
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
        """Both people sitting out and people playing two boards"""
        data = {'sitter_0': str(self.rp1_1.pk),
                'sitter_1': str(self.rp1_2.pk),
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
        """Exact multiple of seven already"""
        form = GetSevenPlayersForm(the_round=self.r2)
        # Nothing needed
        self.assertEqual(len(form.fields), 0)

    def test_standby_fields(self):
        """We should have 2 fields for standby players needed to play in Round 3"""
        prefix='standby'
        form = GetSevenPlayersForm(the_round=self.r3)
        for i in range(0, 2):
            with self.subTest(i=i):
                name = '%s_%d' % (prefix, i)
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
        form = GetSevenPlayersForm(the_round=self.r4)
        self.assertEqual(0, len(form.fields))

    def test_too_few_standbys(self):
        data = {'standby_0': str(self.rp3_1.pk),
               }
        form = GetSevenPlayersForm(data, the_round=self.r3)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Too few standby players selected to play', form.errors['__all__'][0])


class SCOwnerFormTest(TestCase):
    fixtures = ['game_sets.json']

    def test_field_count(self):
        form = SCOwnerForm()
        self.assertEqual(len(form.fields), 1 + SupplyCentre.objects.count())

    def test_required(self):
        form = SCOwnerForm()
        for field in form.fields:
            with self.subTest(field=field):
                self.assertFalse(form.fields[field].required)

    def test_year_1900(self):
        """1900 should be accepted"""
        form = SCOwnerForm(data={'year': 1900})
        self.assertTrue(form.is_valid())

    def test_year_1899(self):
        """1899 should not be accepted"""
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
        """Everything is ok"""
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
        """Everything is ok, one form left blank"""
        data = self.data.copy()
        for key, val in self.row_data.items():
            if val:
                data['form-0-%s' % key] = val.pk
        data['form-0-year'] = 1904
        data['form-0-Belgium'] = self.france.pk
        formset = self.SCOwnerFormset(data)
        self.assertTrue(formset.is_valid())

    def test_blank_one_form(self):
        """
        With initial data (game started)

        Everything is ok, one form blanked
        """
        data = self.data.copy()
        for key, val in self.row_data.items():
            if val:
                data['form-0-%s' % key] = val.pk
        data['form-0-year'] = 1904
        data['form-0-Belgium'] = self.france.pk
        initial = []
        for year in range(1901, 1905):
            scs = {'year': year}
            for sc in SupplyCentre.objects.all():
                scs[str(sc)] = sc.initial_owner
            initial.append(scs)
        formset = self.SCOwnerFormset(data, initial=initial)
        self.assertTrue(formset.is_valid())

    def test_form_error(self):
        """Error in one of the forms"""
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
        """Duplicate years"""
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
        """SC changes from owned to neutral"""
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


class DeathYearFormTest(TestCase):
    fixtures = ['game_sets.json']

    def test_label_field_disabled(self):
        form = DeathYearForm()
        self.assertTrue(form.fields['label'].disabled)

    def test_all_power_fields_not_required(self):
        form = DeathYearForm()
        for power in GreatPower.objects.all():
            with self.subTest(power=power):
                self.assertFalse(form.fields[power.name].required)

    def test_year_1900(self):
        data = {'France': 1900,
               }
        form = DeathYearForm(data=data)
        self.assertFalse(form.is_valid())

    def test_year_1901(self):
        data = {'Austria-Hungary': 1901,
               }
        form = DeathYearForm(data=data)
        self.assertTrue(form.is_valid())


class SCCountFormTest(TestCase):
    fixtures = ['game_sets.json']

    def test_success(self):
        """Everything is ok"""
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
        """1900 should be accepted"""
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
        """1899 should not be accepted"""
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
        """One power has lost more than all their dots"""
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
        """One power has more than all the dots"""
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
        """More than 34 in total"""
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
        """Ensure that the extra 'neutral' field gets added"""
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
        """Everything is ok"""
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
        """One form left empty"""
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
        """Something wrong in one of the forms"""
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
        """One year is repeated"""
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
        """SupplyCentres become neutral"""
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


class PlayerFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)

        cls.p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')

        cls.tp = TournamentPlayer.objects.create(tournament=cls.t, player=cls.p2)

    def test_player_labels(self):
        """Check the player names"""
        form = PlayerForm()
        the_choices = list(form.fields['player'].choices)
        # We should have one per Player, plus the initial empty choice
        self.assertEqual(len(the_choices), Player.objects.count() + 1)
        # The keys should be the Player pks
        self.assertEqual(the_choices[1][0], self.p1.pk)
        # and the values should be the Player names, in alphabetical order
        self.assertEqual(the_choices[1][1], self.p1.sortable_str())
        self.assertEqual(the_choices[2][1], self.p2.sortable_str())

    def test_player_tournament(self):
        """Check narrower QuerySet"""
        form = PlayerForm(tournament=self.t)
        the_choices = list(form.fields['player'].choices)
        # We should have one per TournamentPlayer, plus the initial empty choice
        self.assertEqual(len(the_choices), self.t.tournamentplayer_set.count() + 1)
        # The keys should be the Player pks
        self.assertEqual(the_choices[1][0], self.p2.pk)
        # and the values should be the Player names
        self.assertEqual(the_choices[1][1], self.p2.sortable_str())


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

    def test_form_needs_round_num(self):
        """Omit round_num constructor parameter"""
        with self.assertRaises(KeyError):
            PlayerRoundForm()

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
                               initial=initial,
                               round_num=1)
        self.assertTrue(form.is_valid())

    def test_success2(self):
        """Do everything right"""
        data = {'player': str(self.p1.pk)}
        initial = {'player': self.p1,
                   'present': False,
                   'standby': False,
                   'sandboxer': False,
                   'rounds_played': 0}
        form = PlayerRoundForm(data,
                               initial=initial,
                               round_num=1)
        self.assertTrue(form.is_valid())

    def test_round_fields(self):
        """Check that the correct round fields are created"""
        form = PlayerRoundForm(round_num=2)
        # We should have five fields - player, present, standby, sandboxer, and rounds_played
        self.assertEqual(len(form.fields), 5)

    def test_player_labels(self):
        """Check the player names"""
        form = PlayerRoundForm(round_num=2)
        the_choices = list(form.fields['player'].choices)
        # We should have one per Player, plus the initial empty choice
        self.assertEqual(len(the_choices), Player.objects.count() + 1)
        # The keys should be the Player pks
        self.assertEqual(the_choices[1][0], self.p1.pk)
        # and the values should be the Player names, in alphabetical order
        self.assertEqual(the_choices[1][1], self.p1.sortable_str())
        self.assertEqual(the_choices[2][1], self.p2.sortable_str())


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
                                      start=datetime.combine(cls.t1.start_date, time(hour=8, tzinfo=timezone.utc)))
        cls.r2 = Round.objects.create(tournament=cls.t1,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(cls.t1.start_date, time(hour=17, tzinfo=timezone.utc)))
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
                                      start=datetime.combine(cls.t3.start_date, time(hour=8, tzinfo=timezone.utc)))
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
            self.PlayerRoundFormset(round_num=2)

    def test_formset_needs_round_num(self):
        """Omit round_num constructor parameter"""
        with self.assertRaises(KeyError):
            self.PlayerRoundFormset(tournament=self.t2)

    def test_success(self):
        data = self.data.copy()
        data['form-0-player'] = str(self.p1.pk)
        data['form-0-present'] = 'ok'
        data['form-0-standby'] = 'ok'
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
                    # There should be checkboxes for present, standby, and sandboxer
                    # and an integer rounds_played
                    self.assertIn(field, ['present', 'standby', 'sandboxer', 'rounds_played'])

    def test_no_players(self):
        """Should be fine for a Tournament with no TournamentPlayers"""
        formset = self.PlayerRoundFormset(self.data, tournament=self.t2, round_num=1)
        self.assertTrue(formset.is_valid())

    def test_tournament_over(self):
        """Should be fine for a Tournament that is finished"""
        formset = self.PlayerRoundFormset(self.data, tournament=self.t3, round_num=1)
        self.assertTrue(formset.is_valid())

    def test_duplicate_players(self):
        """Don't allow the same player to be listed more than once"""
        data = self.data.copy()
        data['form-0-player'] = str(self.p1.pk)
        data['form-0-present'] = 'ok'
        data['form-1-player'] = str(self.p1.pk)
        formset = self.PlayerRoundFormset(data, tournament=self.t2, round_num=1)
        self.assertFalse(formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertIn('appears more than once', formset.non_form_errors()[0])

    def test_form_error(self):
        """Check that errors in an individual form get handled correctly"""
        data = self.data.copy()
        data['form-0-player'] = str(self.p1.pk)
        data['form-1-player'] = 'Aardvark'
        formset = self.PlayerRoundFormset(data, tournament=self.t2, round_num=1)
        self.assertFalse(formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)


class PlayerRoundScoreFormTest(TestCase):

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

        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        cls.p2 = Player.objects.create(first_name='Beauregard'.ljust(Player._meta.get_field('first_name').max_length, '.'),
                                       last_name='Bellaciousness'.ljust(Player._meta.get_field('first_name').max_length, '.'))
        cls.tp1 = TournamentPlayer.objects.create(player=cls.p1, tournament=cls.t)
        cls.tp2 = TournamentPlayer.objects.create(player=cls.p2, tournament=cls.t)

    def test_form_needs_tournament(self):
        """Omit tournament constructor parameter"""
        with self.assertRaises(KeyError):
            PlayerRoundScoreForm(last_round_num=2)

    def test_form_needs_last_round_num(self):
        """Omit last_round_num constructor parameter"""
        with self.assertRaises(KeyError):
            PlayerRoundScoreForm(tournament=self.t)

    def test_success(self):
        """Everything is ok"""
        initial = {'tp': self.tp1,
                   'player': self.tp1.player,
                  }
        form = PlayerRoundScoreForm({'tp': str(self.tp1.pk)},
                                    initial=initial,
                                    tournament=self.t,
                                    last_round_num=2)
        self.assertTrue(form.is_valid())

    def test_long_name(self):
        initial = {'tp': self.tp2,
                   'player': self.tp2.player,
                  }
        form = PlayerRoundScoreForm({'tp': str(self.tp2.pk),
                                     'round_2': '57.3'},
                                    initial=initial,
                                    tournament=self.t,
                                    last_round_num=2)
        self.assertTrue(form.is_valid())

    def test_fields_disabled(self):
        """Many fields should be disabled"""
        initial = {'tp': self.tp1,
                   'player': self.tp1.player,
                  }
        form = PlayerRoundScoreForm(initial=initial,
                                    tournament=self.t,
                                    last_round_num=3)
        for field in ['player', 'game_scores_1', 'game_scores_2', 'game_scores_3']:
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
        today = date.today()
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET)
        r1 = Round.objects.create(tournament=cls.t1,
                                  scoring_system=G_SCORING_SYSTEMS[0].name,
                                  dias=True,
                                  start=datetime.combine(cls.t1.start_date, time(hour=8, tzinfo=timezone.utc)))
        Round.objects.create(tournament=cls.t1,
                             scoring_system=G_SCORING_SYSTEMS[0].name,
                             dias=True,
                             start=datetime.combine(cls.t1.start_date, time(hour=17, tzinfo=timezone.utc)))
        TournamentPlayer.objects.create(player=p1, tournament=cls.t1)
        TournamentPlayer.objects.create(player=p2, tournament=cls.t1)
        RoundPlayer.objects.create(player=p1, the_round=r1)
        cls.t2 = Tournament.objects.create(name='t2',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET)
        cls.t3 = Tournament.objects.create(name='t3',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET)
        r3 = Round.objects.create(tournament=cls.t3,
                                  scoring_system=G_SCORING_SYSTEMS[0].name,
                                  dias=True,
                                  start=datetime.combine(cls.t3.start_date, time(hour=8, tzinfo=timezone.utc)))
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
        """Omit tournament kwarg"""
        with self.assertRaises(KeyError):
            self.PlayerRoundScoreFormset()

    def test_success(self):
        """All ok"""
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
        """Should be fine for a Tournament with no TournamentPlayers"""
        data = {
            'form-TOTAL_FORMS': '0',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }
        formset = self.PlayerRoundScoreFormset(data, tournament=self.t2)
        self.assertTrue(formset.is_valid())

    def test_finished(self):
        """Should be fine for a completed Tournament"""
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


class SeederBiasFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # We need two Tournaments and some TournamentPlayers
        p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        p2 = Player.objects.create(first_name='Christina', last_name='Dragnet')
        p3 = Player.objects.create(first_name='Charlie', last_name='Calculus')
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)
        t2 = Tournament.objects.create(name='t2',
                                       start_date=today,
                                       end_date=today + timedelta(hours=24),
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)
        # Create TournamentPlayers in reverse alphabetical order
        cls.tp1 = TournamentPlayer.objects.create(player=p2, tournament=cls.t)
        cls.tp2 = TournamentPlayer.objects.create(player=p1, tournament=cls.t)
        TournamentPlayer.objects.create(player=p3, tournament=t2)

    def test_form_needs_tournament(self):
        """Omit tournament kwarg"""
        with self.assertRaises(KeyError):
            SeederBiasForm()

    def test_success(self):
        """Everything is ok"""
        form = SeederBiasForm({'player1': str(self.tp1.pk),
                               'player2': str(self.tp2.pk)},
                              tournament=self.t)
        self.assertTrue(form.is_valid())

    def test_self_bias(self):
        """Can't keep a player away from themselves"""
        form = SeederBiasForm({'player1': str(self.tp1.pk),
                               'player2': str(self.tp1.pk)},
                              tournament=self.t)
        self.assertFalse(form.is_valid())

    def test_player_choices(self):
        form = SeederBiasForm(tournament=self.t)
        for field in ['player1', 'player2']:
            the_choices = list(form.fields[field].choices)
            # We should have one per TournamentPlayer, plus the initial empty choice
            self.assertEqual(len(the_choices), self.t.tournamentplayer_set.count() + 1)
            # The keys should be the TournamentPlayer pks
            self.assertEqual(the_choices[1][0], self.tp2.pk)
            self.assertEqual(the_choices[2][0], self.tp1.pk)
            # and the values should be the Player names, in alphabetical order
            self.assertEqual(the_choices[1][1], self.tp2.player.sortable_str())
            self.assertEqual(the_choices[2][1], self.tp1.player.sortable_str())
