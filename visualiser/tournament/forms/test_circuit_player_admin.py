# Diplomacy Tournament Visualiser
# Copyright (C) 2026 Chris Brand
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
CircuitPlayerAdminForm tests for the Diplomacy Tournament Visualiser.
"""

from datetime import date

from django.test import TestCase

from tournament.circuits import Circuit, CircuitPlayer
from tournament.models import R_SCORING_SYSTEMS, DrawSecrecy, Tournament, TournamentPlayer
from tournament.players import Player

from . import CircuitPlayerAdminForm


class CircuitPlayerAdminFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.today = date.today()

        cls.p1 = Player.objects.create(first_name='Alpha', last_name='Player')
        cls.p2 = Player.objects.create(first_name='Bravo', last_name='Player')

        cls.circuit = Circuit.objects.create(name='Circuit form test',
                                             start_date=cls.today,
                                             end_date=cls.today,
                                             scoring_system='Sum best 3 tournament percentiles')
        cls.other_circuit = Circuit.objects.create(name='Other circuit form test',
                                                   start_date=cls.today,
                                                   end_date=cls.today,
                                                   scoring_system='Sum best 3 tournament percentiles')

        cls.t1 = Tournament.objects.create(name='Circuit form t1',
                                           start_date=cls.today,
                                           end_date=cls.today,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system='Sum all round scores',
                                           draw_secrecy=DrawSecrecy.SECRET)
        cls.t2 = Tournament.objects.create(name='Circuit form t2',
                                           start_date=cls.today,
                                           end_date=cls.today,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system='Sum all round scores',
                                           draw_secrecy=DrawSecrecy.SECRET)
        cls.t3 = Tournament.objects.create(name='Circuit form t3',
                                           start_date=cls.today,
                                           end_date=cls.today,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system='Sum all round scores',
                                           draw_secrecy=DrawSecrecy.SECRET)

        cls.circuit.tournaments.add(cls.t1, cls.t2)
        cls.other_circuit.tournaments.add(cls.t3)

        cls.tp_p1_t1 = TournamentPlayer.objects.create(player=cls.p1,
                                                       tournament=cls.t1)
        cls.tp_p1_t2 = TournamentPlayer.objects.create(player=cls.p1,
                                                       tournament=cls.t2)
        cls.tp_p1_t3 = TournamentPlayer.objects.create(player=cls.p1,
                                                       tournament=cls.t3)
        cls.tp_p2_t1 = TournamentPlayer.objects.create(player=cls.p2,
                                                       tournament=cls.t1)

    def test_queryset_restricted_to_same_player_and_circuit_tournaments(self):
        cp = CircuitPlayer.objects.create(player=self.p1, circuit=self.circuit)

        form = CircuitPlayerAdminForm(instance=cp)
        allowed_ids = set(form.fields['tournamentplayers'].queryset.values_list('id', flat=True))

        self.assertIn(self.tp_p1_t1.id, allowed_ids)
        self.assertIn(self.tp_p1_t2.id, allowed_ids)
        self.assertNotIn(self.tp_p1_t3.id, allowed_ids)
        self.assertNotIn(self.tp_p2_t1.id, allowed_ids)

    def test_queryset_unfiltered_for_unsaved_instance_without_player(self):
        form = CircuitPlayerAdminForm(instance=CircuitPlayer())
        self.assertEqual(
            form.fields['tournamentplayers'].queryset.count(),
            TournamentPlayer.objects.count()
        )

    def test_queryset_unfiltered_when_instance_is_none(self):
        form = CircuitPlayerAdminForm(instance=None)
        self.assertEqual(
            form.fields['tournamentplayers'].queryset.count(),
            TournamentPlayer.objects.count()
        )
