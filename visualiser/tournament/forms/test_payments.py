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

from django.test import TestCase

from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Tournament, TournamentPlayer)
from tournament.players import Player

from . import PaidForm


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
        form = PaidForm(instance=self.tp)
        self.assertEqual(form.fields['paid'].label, 'Arthur Bottom')

    def test_paid_form_none(self):
        form = PaidForm(instance=self.tp)
        self.assertEqual(form['paid'].initial, False)

    def test_paid_form_paid_initial(self):
        form = PaidForm(instance=self.tp, initial={'paid': True})
        # Explicit initial should override implicit
        self.assertEqual(form['paid'].initial, True)

    def test_has_changed(self):
        initial = {'paid': True}
        data = {'paid': 'ok'}
        form = PaidForm(instance=self.tp, initial=initial, data=data)
        self.assertIs(False, form.has_changed())
        initial = {'paid': False}
        data = {}
        form = PaidForm(instance=self.tp, initial=initial, data=data)
        self.assertIs(False, form.has_changed())
