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
Seeder Bias Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, timedelta

from django.test import TestCase

from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Tournament, TournamentPlayer)
from tournament.players import Player

from . import SeederBiasForm


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
        self.assertIs(True, form.is_valid())

    def test_self_bias(self):
        """Can't keep a player away from themselves"""
        form = SeederBiasForm({'player1': str(self.tp1.pk),
                               'player2': str(self.tp1.pk)},
                              tournament=self.t)
        self.assertIs(False, form.is_valid())

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

    def test_has_changed(self):
        data = {'player1': str(self.tp1.pk),
                'player2': str(self.tp2.pk)}
        initial = {'player1': self.tp1,
                   'player2': self.tp2}
        form = SeederBiasForm(tournament=self.t,
                              data=data,
                              initial=initial)
        self.assertIs(False, form.has_changed())
