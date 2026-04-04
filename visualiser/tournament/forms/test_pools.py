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
Pool Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone

from django.test import TestCase

from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Pool, Round, RoundPlayer,
                               Tournament, TournamentPlayer)
from tournament.players import Player

from . import PoolForm


class PoolFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # We need a Tournament with a Round with two Pools
        # and at least seven TournamentPlayers and RoundPlayers
        today = date.today()
        cls.t = Tournament.objects.create(name='tourney',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)
        cls.r = Round.objects.create(tournament=cls.t,
                                     scoring_system=G_SCORING_SYSTEMS[0].name,
                                     dias=True,
                                     start=datetime.combine(cls.t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        cls.pool1 = Pool.objects.create(the_round=cls.r,
                                        name='Fixed',
                                        board_count=1)
        cls.pool2 = Pool.objects.create(the_round=cls.r,
                                        name='Variable')

        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        cls.p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        cls.p3 = Player.objects.create(first_name='Charlie', last_name='Celiac')
        cls.p4 = Player.objects.create(first_name='Dorothy', last_name='Deathstar')
        cls.p5 = Player.objects.create(first_name='Edward', last_name='Egalitarian')
        cls.p6 = Player.objects.create(first_name='Francine', last_name='Francophone')
        cls.p7 = Player.objects.create(first_name='Gerald', last_name='Geranium')
        cls.p8 = Player.objects.create(first_name='Hetty', last_name='Heffalump')
        cls.p9 = Player.objects.create(first_name='Ian', last_name='Inkstain')

        cls.tp1 = TournamentPlayer.objects.create(tournament=cls.t, player=cls.p1)
        cls.tp2 = TournamentPlayer.objects.create(tournament=cls.t, player=cls.p2)
        cls.tp3 = TournamentPlayer.objects.create(tournament=cls.t, player=cls.p3)
        cls.tp4 = TournamentPlayer.objects.create(tournament=cls.t, player=cls.p4)
        cls.tp5 = TournamentPlayer.objects.create(tournament=cls.t, player=cls.p5)
        cls.tp6 = TournamentPlayer.objects.create(tournament=cls.t, player=cls.p6)
        cls.tp7 = TournamentPlayer.objects.create(tournament=cls.t, player=cls.p7)
        cls.tp8 = TournamentPlayer.objects.create(tournament=cls.t, player=cls.p8)
        cls.tp9 = TournamentPlayer.objects.create(tournament=cls.t, player=cls.p9)

        cls.rp1 = RoundPlayer.objects.create(the_round=cls.r, player=cls.p1, sandboxer=True)
        cls.rp2 = RoundPlayer.objects.create(the_round=cls.r, player=cls.p2)
        cls.rp3 = RoundPlayer.objects.create(the_round=cls.r, player=cls.p3)
        cls.rp4 = RoundPlayer.objects.create(the_round=cls.r, player=cls.p4)
        cls.rp5 = RoundPlayer.objects.create(the_round=cls.r, player=cls.p5)
        cls.rp6 = RoundPlayer.objects.create(the_round=cls.r, player=cls.p6)
        cls.rp7 = RoundPlayer.objects.create(the_round=cls.r, player=cls.p7)
        cls.rp8 = RoundPlayer.objects.create(the_round=cls.r, player=cls.p8)

    def test_form_needs_pool(self):
        """Omit pool constructor parameter"""
        with self.assertRaises(KeyError):
            PoolForm()

    def test_player_fields(self):
        """Check that we have the right number of fields, with the right QuerySet"""
        form = PoolForm(None, pool=self.pool1)
        self.assertEqual(len(form.fields), 7)
        # One empty choice, plus one per RoundPlayer
        the_choices = list(form.fields['player_1'].choices)
        self.assertEqual(len(the_choices), self.r.roundplayer_set.count() + 1)
        # The keys should be the RoundPlayer pks
        self.assertEqual(the_choices[1][0], self.rp1.pk)
        # and the values should be the Player names, in alphabetical order
        # Sandboxers should not be flagged
        self.assertEqual(the_choices[1][1], self.rp1.player.sortable_str())
        self.assertEqual(the_choices[2][1], self.rp2.player.sortable_str())

    def test_success(self):
        data = {'player_1': str(self.rp1.pk),
                'player_2': str(self.rp2.pk),
                'player_3': str(self.rp3.pk),
                'player_4': str(self.rp5.pk),
                'player_5': str(self.rp6.pk),
                'player_6': str(self.rp7.pk),
                'player_7': str(self.rp8.pk)}
        form = PoolForm(data, pool=self.pool1)
        self.assertIs(True, form.is_valid())

    def test_duplicate_player(self):
        """Pick the same player more than once"""
        data = {'player_1': str(self.rp1.pk),
                'player_2': str(self.rp2.pk),
                'player_3': str(self.rp3.pk),
                'player_4': str(self.rp5.pk),
                'player_5': str(self.rp5.pk),
                'player_6': str(self.rp7.pk),
                'player_7': str(self.rp8.pk)}
        form = PoolForm(data, pool=self.pool1)
        self.assertIs(False, form.is_valid())
        self.assertFormError(form, None, 'Player Edward Egalitarian appears more than once')

    def test_invalid_player(self):
        """Pool includes an invalid choice"""
        self.assertFalse(self.pool1.roundplayer_set.filter(pk=0).exists())
        data = {'player_1': str(self.rp1.pk),
                'player_2': '0',
                'player_3': str(self.rp3.pk),
                'player_4': str(self.rp5.pk),
                'player_5': str(self.rp5.pk),
                'player_6': str(self.rp7.pk),
                'player_7': str(self.rp8.pk)}
        form = PoolForm(data, pool=self.pool1)
        self.assertIs(False, form.is_valid())
        self.assertFormError(form,
                             'player_2',
                             'Select a valid choice. That choice is not one of the available choices.')
