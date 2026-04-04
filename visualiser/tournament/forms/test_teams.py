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
Team Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, timedelta

from django.forms.formsets import formset_factory
from django.test import TestCase

from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Team, Tournament, TournamentPlayer)
from tournament.players import Player

from . import BaseTeamsFormset, TeamForm


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
        self.assertIs(True, form.fields['player_0'].required)
        for i in range(1, self.t.team_size):
            self.assertIs(False, form.fields[f'player_{i}'].required)

    def test_team_form_players_optional(self):
        """One player should be required, others optional"""
        form = TeamForm(tournament=self.t, data={'name': 'Sausages',
                                                 'player_0': str(self.p1.pk)})
        self.assertIs(True, form.is_valid())

    def test_team_form_existing_team(self):
        """team kwarg should be supported"""
        TeamForm(tournament=self.t, team=self.tm)

    def test_team_repeated_player(self):
        """Same player can't appear more than once in a team"""
        form = TeamForm(tournament=self.t, data={'name': 'Sausages',
                                                 'player_0': str(self.p2.pk),
                                                 'player_1': str(self.p1.pk),
                                                 'player_2': str(self.p1.pk)})
        self.assertIs(False, form.is_valid())
        self.assertFormError(form, None, 'Player Arthur Bottom appears more than once')

    def test_team_invalid_player(self):
        """Team includes a player who isn't playing the Tournament"""
        form = TeamForm(tournament=self.t, data={'name': 'Sausages',
                                                 'player_0': str(self.p2.pk),
                                                 'player_1': str(self.p1.pk),
                                                 'player_2': str(self.p4.pk)})
        self.assertIs(False, form.is_valid())
        self.assertFormError(form,
                             'player_2',
                             'Select a valid choice. That choice is not one of the available choices.')

    def test_team_form_has_changed_implicit_initial_1(self):
        form = TeamForm(tournament=self.t,
                        team=self.tm,
                        data={'name': 'The Team',
                              'player_0': str(self.p2.id)})
        self.assertIs(False, form.has_changed())

    def test_team_form_has_changed_implicit_initial_2(self):
        form = TeamForm(tournament=self.t,
                        data={})
        self.assertIs(False, form.has_changed())

    def test_team_form_has_changed_explicit_initial(self):
        form = TeamForm(tournament=self.t,
                        data={'name': 'Another Team',
                              'player_0': str(self.p2.id),
                              'player_1': str(self.p1.id)},
                        initial={'name': 'Another Team',
                                 'player_0': self.p2.id,
                                 'player_1': self.p1.id})
        self.assertIs(False, form.has_changed())


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
        self.assertIs(True, formset.is_valid())

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
        self.assertIs(False, formset.is_valid())
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
        self.assertIs(False, formset.is_valid())
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
        self.assertIs(False, formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, None, None, 'Player Arthur Bottom appears in multiple teams')
