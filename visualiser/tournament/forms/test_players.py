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
Player Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, timedelta

from django.test import TestCase

from tournament.forms import PlayerForm
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Tournament, TournamentPlayer)
from tournament.players import Player


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

    def test_has_changed(self):
        data = {'player': str(self.p2.pk)}
        initial = {'player': self.p2}
        form = PlayerForm(tournament=self.t, data=data, initial=initial)
        self.assertIs(False, form.has_changed())
