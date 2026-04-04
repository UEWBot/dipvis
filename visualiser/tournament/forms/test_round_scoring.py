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
Round Scoring Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone

from django.forms.formsets import formset_factory
from django.test import TestCase

from tournament.diplomacy import GameSet
from tournament.forms import BasePlayerRoundScoreFormset, PlayerRoundScoreForm
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Game, Round, RoundPlayer,
                               Tournament, TournamentPlayer)
from tournament.players import Player


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

    def test_player_field(self):
        form = PlayerRoundScoreForm(tournament=self.t,
                                    last_round_num=2)
        self.assertIs(True, form.fields['player'].disabled)
        attrs = form.fields['player'].widget.attrs
        self.assertEqual(attrs['size'], '20')

    def test_game_scores_fields(self):
        """Many fields should be disabled"""
        initial = {'tp': self.tp1,
                   'player': self.tp1.player,
                  }
        form = PlayerRoundScoreForm(initial=initial,
                                    tournament=self.t,
                                    last_round_num=3)
        for field in ['game_scores_1', 'game_scores_2', 'game_scores_3']:
            with self.subTest(field=field):
                self.assertIs(True, form.fields[field].disabled)
                self.assertIs(False, form.fields[field].required)
                attrs = form.fields[field].widget.attrs
                self.assertEqual(attrs['maxlength'], '10')

    def test_round_fields(self):
        form = PlayerRoundScoreForm(tournament=self.t,
                                    last_round_num=2)
        for n in range(1, 3):
            with self.subTest(round_number=n):
                name = f'round_{n}'
                self.assertIs(False, form.fields[name].required)
                attrs = form.fields[name].widget.attrs
                self.assertEqual(attrs['size'], '10')
                self.assertEqual(attrs['maxlength'], '40')

    def test_overall_score_field(self):
        form = PlayerRoundScoreForm(tournament=self.t,
                                    last_round_num=2)
        self.assertIs(False, form.fields['overall_score'].required)
        attrs = form.fields['overall_score'].widget.attrs
        self.assertEqual(attrs['size'], '10')
        self.assertEqual(attrs['maxlength'], '20')

    def test_success(self):
        """Everything is ok"""
        initial = {'tp': self.tp1,
                   'player': self.tp1.player,
                  }
        form = PlayerRoundScoreForm({'tp': str(self.tp1.pk)},
                                    initial=initial,
                                    tournament=self.t,
                                    last_round_num=2)
        self.assertIs(True, form.is_valid())

    def test_long_name(self):
        initial = {'tp': self.tp2,
                   'player': self.tp2.player,
                  }
        form = PlayerRoundScoreForm({'tp': str(self.tp2.pk),
                                     'round_2': '57.3'},
                                    initial=initial,
                                    tournament=self.t,
                                    last_round_num=2)
        self.assertIs(True, form.is_valid())

    def test_has_changed(self):
        data = {'tp': str(self.tp2.pk),
                'overall_score': '47.3'}
        initial = {'tp': self.tp2,
                   'player': self.tp2.player,
                   'overall_score': 47.3}
        for n in range(0, 2):
            data[f'round_{n}'] = str(n)
            initial[f'round_{n}'] = n
        form = PlayerRoundScoreForm(data=data,
                                    initial=initial,
                                    tournament=self.t,
                                    last_round_num=2)
        self.assertIs(False, form.has_changed())


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
                                  start=datetime.combine(cls.t1.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        Round.objects.create(tournament=cls.t1,
                             scoring_system=G_SCORING_SYSTEMS[0].name,
                             dias=True,
                             start=datetime.combine(cls.t1.start_date, time(hour=17, tzinfo=datetime_timezone.utc)))
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
                                  start=datetime.combine(cls.t3.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
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
        self.assertIs(True, formset.is_valid())

    def test_no_players(self):
        """Should be fine for a Tournament with no TournamentPlayers"""
        data = {
            'form-TOTAL_FORMS': '0',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }
        formset = self.PlayerRoundScoreFormset(data, tournament=self.t2)
        self.assertIs(True, formset.is_valid())

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
        self.assertIs(True, formset.is_valid())
