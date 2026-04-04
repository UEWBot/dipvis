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
Paid Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, timedelta

from django.forms.formsets import formset_factory
from django.test import TestCase

from tournament.forms import BasePaidFormset, PaidForm
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Tournament, TournamentPlayer)
from tournament.players import Player


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

    def test_has_changed(self):
        initial = {'paid': True}
        data = {'paid': 'ok'}
        form = PaidForm(tp=self.tp, initial=initial, data=data)
        self.assertIs(False, form.has_changed())
        initial = {'paid': False}
        data = {}
        form = PaidForm(tp=self.tp, initial=initial, data=data)
        self.assertIs(False, form.has_changed())


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
