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
Handicap Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, timedelta

from django.forms.formsets import formset_factory
from django.test import TestCase

from tournament.forms import BaseHandicapsFormset, HandicapForm
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Tournament, TournamentPlayer)
from tournament.players import Player


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
        cls.tp = TournamentPlayer.objects.create(player=p, tournament=t, handicap=0.0)

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
        self.assertIs(True, form.is_valid())
        self.assertAlmostEqual(form.cleaned_data['handicap'], 5.0)
        # Cleanup
        self.tp.handicap = 0.0
        self.tp.save()

    def test_handicap_form_has_changed_implicit_initial(self):
        form = HandicapForm(tp=self.tp, data={'handicap': '0.0'})
        self.assertIs(False, form.has_changed())

    def test_handicap_form_has_changed_explicit_initial(self):
        form = HandicapForm(tp=self.tp,
                            data={'handicap': '5.0'},
                            initial={'handicap': 5.0})
        self.assertIs(False, form.has_changed())


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
