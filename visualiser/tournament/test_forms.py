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

from django.forms.formsets import formset_factory
from django.test import TestCase
from django.utils import timezone

from tournament.models import T_SCORING_SYSTEMS, R_SCORING_SYSTEMS, SECRET
from tournament.models import Tournament
from tournament.models import TournamentPlayer
from tournament.players import Player

from tournament.forms import PrefsForm, BasePrefsFormset

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
