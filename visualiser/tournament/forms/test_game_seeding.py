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
Game Seeding Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone

from django.forms.formsets import formset_factory
from django.test import TestCase

from tournament.diplomacy import GameSet, GreatPower
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Game, Pool, Round, RoundPlayer,
                               Team, Tournament, TournamentPlayer)
from tournament.players import Player

from . import BaseGamePlayersFormset, GamePlayersForm


class GamePlayersFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # We need a Tournament with a Round, and some RoundPlayers to choose from
        # We'll also create some extra TournamentPlayers and Players
        # to ensure that the form doesn't pick them up
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)
        cls.r1 = Round.objects.create(tournament=cls.t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(cls.t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        r2 = Round.objects.create(tournament=cls.t,
                                  scoring_system=G_SCORING_SYSTEMS[0].name,
                                  dias=True,
                                  start=datetime.combine(cls.t.start_date, time(hour=17, tzinfo=datetime_timezone.utc)))
        p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        p3 = Player.objects.create(first_name='Christina', last_name='Calculus')
        p4 = Player.objects.create(first_name='Douglas', last_name='Dragnet')
        p7 = Player.objects.create(first_name='Georgette', last_name='Giant')
        p8 = Player.objects.create(first_name='Harold', last_name='Homeless')
        p9 = Player.objects.create(first_name='Irene', last_name='Imp')
        Player.objects.create(first_name='Julia', last_name='Jug')
        # Deliberately create these two out of alphabetical order
        p5 = Player.objects.create(first_name='Edwina', last_name='Eggplant')
        p6 = Player.objects.create(first_name='Frank', last_name='Furious')
        TournamentPlayer.objects.create(player=p1, tournament=cls.t)
        TournamentPlayer.objects.create(player=p2, tournament=cls.t)
        TournamentPlayer.objects.create(player=p3, tournament=cls.t)
        TournamentPlayer.objects.create(player=p4, tournament=cls.t)
        TournamentPlayer.objects.create(player=p5, tournament=cls.t)
        TournamentPlayer.objects.create(player=p6, tournament=cls.t)
        TournamentPlayer.objects.create(player=p7, tournament=cls.t)
        TournamentPlayer.objects.create(player=p8, tournament=cls.t)
        TournamentPlayer.objects.create(player=p9, tournament=cls.t)
        cls.rp1 = RoundPlayer.objects.create(player=p1, the_round=cls.r1)
        cls.rp2 = RoundPlayer.objects.create(player=p2, the_round=cls.r1)
        cls.rp3 = RoundPlayer.objects.create(player=p3, the_round=cls.r1, sandboxer=True)
        cls.rp5 = RoundPlayer.objects.create(player=p5, the_round=cls.r1)
        cls.rp6 = RoundPlayer.objects.create(player=p6, the_round=cls.r1)
        cls.rp7 = RoundPlayer.objects.create(player=p7, the_round=cls.r1)
        # Again, create this one out of alphabetical order
        cls.rp4 = RoundPlayer.objects.create(player=p4, the_round=cls.r1)
        cls.rp8 = RoundPlayer.objects.create(player=p8, the_round=cls.r1)
        RoundPlayer.objects.create(player=p9, the_round=r2)

    def test_init_needs_round(self):
        with self.assertRaises(KeyError):
            GamePlayersForm(pool=None)

    def test_init_needs_pool(self):
        with self.assertRaises(KeyError):
            GamePlayersForm(the_round=self.r1)

    def test_game_id_field(self):
        form = GamePlayersForm(the_round=self.r1, pool=None)
        self.assertIn('game_id', form.fields)

    def test_name_field(self):
        form = GamePlayersForm(the_round=self.r1, pool=None)
        self.assertIn('name', form.fields)
        attrs = form.fields['name'].widget.attrs
        self.assertEqual(attrs['size'], attrs['maxlength'])

    def test_set_field(self):
        form = GamePlayersForm(the_round=self.r1, pool=None)
        self.assertIn('the_set', form.fields)

    def test_top_board_field(self):
        form = GamePlayersForm(the_round=self.r1, pool=None)
        self.assertIn('top_board', form.fields)

    def test_url_field(self):
        form = GamePlayersForm(the_round=self.r1, pool=None)
        self.assertIn('external_url', form.fields)

    def test_notes_field(self):
        form = GamePlayersForm(the_round=self.r1, pool=None)
        self.assertIn('notes', form.fields)

    def test_power_fields(self):
        form = GamePlayersForm(the_round=self.r1, pool=None)
        for power in GreatPower.objects.all():
            with self.subTest(power=power.name):
                self.assertIs(True, form.fields[power.name].required)

    def test_power_choices(self):
        form = GamePlayersForm(the_round=self.r1, pool=None)
        # Pick a GreatPower at random - they will all be the same
        the_choices = list(form.fields['England'].choices)
        # We should have one per RoundPlayer, plus the initial empty choice
        self.assertEqual(len(the_choices), self.r1.roundplayer_set.count() + 1)
        # The keys should be the RoundPlayer pks
        self.assertEqual(the_choices[1][0], self.rp1.pk)
        # and the values should be the Player names, in alphabetical order
        self.assertEqual(the_choices[1][1], self.rp1.player.sortable_str())
        self.assertEqual(the_choices[2][1], self.rp2.player.sortable_str())
        # Sandboxers should be flagged
        self.assertEqual(the_choices[3][1], self.rp3.player.sortable_str()+'*')
        self.assertEqual(the_choices[4][1], self.rp4.player.sortable_str())
        self.assertEqual(the_choices[5][1], self.rp5.player.sortable_str())
        self.assertEqual(the_choices[6][1], self.rp6.player.sortable_str())
        self.assertEqual(the_choices[7][1], self.rp7.player.sortable_str())
        self.assertEqual(the_choices[8][1], self.rp8.player.sortable_str())

    def test_power_choices_with_pool(self):
        pool1 = Pool.objects.create(the_round=self.r1,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r1,
                                    name='Variable')
        pool_rps = [self.rp1, self.rp4, self.rp5]
        for rp in pool_rps:
            rp.pool = pool1
            rp.save()
        for rp in [self.rp2, self.rp3, self.rp6, self.rp7, self.rp8]:
            rp.pool = pool2
            rp.save()
        form = GamePlayersForm(the_round=self.r1, pool=pool1)
        # Pick a GreatPower at random - they will all be the same
        the_choices = list(form.fields['England'].choices)
        # We should have one per RoundPlayer in the Pool, plus the initial empty choice
        self.assertEqual(len(the_choices), len(pool_rps) + 1)
        # Cleanup
        for rp in self.r1.roundplayer_set.all():
            rp.pool = None
            rp.save()
        self.r1.pool_set.all().delete()

    def test_success(self):
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(True, form.is_valid())

    def test_success_with_id(self):
        data = {'name': 'R1G1',
                'game_id': '17',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(True, form.is_valid())

    def test_success_with_pool1(self):
        """Form pool matches Game pool"""
        pool1 = Pool.objects.create(the_round=self.r1,
                                    name='Fixed',
                                    board_count=1)
        Pool.objects.create(the_round=self.r1,
                            name='Variable')
        for rp in [self.rp1, self.rp2, self.rp3, self.rp4, self.rp5, self.rp6, self.rp7]:
            rp.pool = pool1
            rp.save()
        g = Game.objects.create(name='R1G1',
                                the_round=self.r1,
                                pool=pool1,
                                the_set=GameSet.objects.first())
        initial = {'name': g.name,
                   'game_id': g.pk,
                   'the_set': g.the_set,
                   'external_url': '',
                   'notes': ''}
        data = {'name': g.name,
                'game_id': str(g.pk),
                'the_set': str(g.the_set.pk),
                'external_url': '',
                'notes': '',
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data=data, initial=initial, the_round=self.r1, pool=pool1)
        self.assertIs(True, form.is_valid())
        # Cleanup
        g.delete()
        for rp in [self.rp1, self.rp2, self.rp3, self.rp4, self.rp5, self.rp6, self.rp7]:
            rp.pool = None
            rp.save()
        self.r1.pool_set.all().delete()

    def test_success_with_pool2(self):
        """Game pool set, Form pool not"""
        pool1 = Pool.objects.create(the_round=self.r1,
                                    name='Fixed',
                                    board_count=1)
        Pool.objects.create(the_round=self.r1,
                            name='Variable')
        for rp in [self.rp1, self.rp2, self.rp3, self.rp4, self.rp5, self.rp6, self.rp7]:
            rp.pool = pool1
            rp.save()
        g = Game.objects.create(name='R1G1',
                                the_round=self.r1,
                                pool=pool1,
                                the_set=GameSet.objects.first())
        initial = {'name': g.name,
                   'game_id': g.pk,
                   'the_set': g.the_set,
                   'external_url': '',
                   'notes': ''}
        data = {'name': g.name,
                'game_id': str(g.pk),
                'the_set': str(g.the_set.pk),
                'external_url': '',
                'notes': '',
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data=data, initial=initial, the_round=self.r1, pool=None)
        self.assertIs(True, form.is_valid())
        # Cleanup
        g.delete()
        for rp in [self.rp1, self.rp2, self.rp3, self.rp4, self.rp5, self.rp6, self.rp7]:
            rp.pool = None
            rp.save()
        self.r1.pool_set.all().delete()

    def test_has_changed(self):
        g = Game.objects.create(name='OnlyGame',
                                the_round=self.r1,
                                the_set=GameSet.objects.first())
        initial = {'name': g.name,
                   'game_id': g.pk,
                   'the_set': g.the_set,
                   'external_url': '',
                   'notes': '',
                   'Austria-Hungary': self.rp1,
                   'England': self.rp2,
                   'France': self.rp3,
                   'Germany': self.rp4,
                   'Italy': self.rp5,
                   'Russia': self.rp6,
                   'Turkey': self.rp7}
        data = {'name': g.name,
                'game_id': str(g.pk),
                'the_set': str(g.the_set.pk),
                'external_url': '',
                'notes': ''}
        for power in GreatPower.objects.all():
            data[power.name] = str(initial[power.name].pk)
        form = GamePlayersForm(data=data,
                               the_round=self.r1,
                               pool=None,
                               initial=initial)
        self.assertIs(False, form.has_changed())
        # Cleanup
        g.delete()

    def test_create_with_wrong_pool1(self):
        Pool.objects.create(the_round=self.r1,
                            name='Fixed',
                            board_count=1)
        pool2 = Pool.objects.create(the_round=self.r1,
                                    name='Variable')
        g = Game.objects.create(name='R1G1',
                                the_round=self.r1,
                                the_set=GameSet.objects.first())
        initial = {'name': g.name,
                   'game_id': g.pk,
                   'the_set': g.the_set,
                   'external_url': '',
                   'notes': '',
                   'Austria-Hungary': self.rp1,
                   'England': self.rp2,
                   'France': self.rp3,
                   'Germany': self.rp4,
                   'Italy': self.rp5,
                   'Russia': self.rp6,
                   'Turkey': self.rp7}
        with self.assertRaises(AssertionError):
            GamePlayersForm(initial=initial, the_round=self.r1, pool=pool2)
        # Cleanup
        g.delete()
        self.r1.pool_set.all().delete()

    def test_create_with_wrong_pool2(self):
        pool1 = Pool.objects.create(the_round=self.r1,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r1,
                                    name='Variable')
        g = Game.objects.create(name='R1G1',
                                the_round=self.r1,
                                pool=pool1,
                                the_set=GameSet.objects.first())
        initial = {'name': g.name,
                   'game_id': g.pk,
                   'the_set': g.the_set,
                   'external_url': '',
                   'notes': '',
                   'Austria-Hungary': self.rp1,
                   'England': self.rp2,
                   'France': self.rp3,
                   'Germany': self.rp4,
                   'Italy': self.rp5,
                   'Russia': self.rp6,
                   'Turkey': self.rp7}
        with self.assertRaises(AssertionError):
            GamePlayersForm(initial=initial, the_round=self.r1, pool=pool2)
        # Cleanup
        g.delete()
        self.r1.pool_set.all().delete()

    def test_name_error1(self):
        data = {'name': 'R1 G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'name', 'Game names cannot contain " "')

    def test_name_error2(self):
        data = {'name': 'R1/G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'name', 'Game names cannot contain "/"')

    def test_set_error(self):
        data = {'name': 'R1G1',
                'the_set': 'Non-existent set',
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'the_set', 'Select a valid choice. That choice is not one of the available choices.')

    def test_player_error(self):
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': 'None',
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'France', 'Select a valid choice. That choice is not one of the available choices.')

    def test_reject_duplicate_players(self):
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp1.pk)}
        form = GamePlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        # We should see the Player, not the RoundPlayer, in any error
        self.assertFormError(form, None, 'Player Arthur Amphitheatre appears more than once')

    def test_teammates_in_team_round(self):
        """Players from the same team in the same game in a team round"""
        self.t.team_size = 2
        self.t.save()
        self.r1.is_team_round = True
        self.r1.save()
        tm = Team.objects.create(tournament=self.t,
                                 name="The test team")
        tm.players.add(self.rp2.player)
        tm.players.add(self.rp4.player)
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, None, 'Multiple players from team The test team')
        # Cleanup
        tm.delete()
        self.t.team_size = None
        self.t.save()
        self.r1.is_team_round = False
        self.r1.save()

    def test_non_teammates_in_team_round(self):
        """No players from the same team in the same game in a team round"""
        self.t.team_size = 2
        self.t.save()
        self.r1.is_team_round = True
        self.r1.save()
        tm1 = Team.objects.create(tournament=self.t,
                                  name="The test team")
        tm1.players.add(self.rp2.player)
        tm2 = Team.objects.create(tournament=self.t,
                                  name="Another test team")
        tm2.players.add(self.rp4.player)
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(True, form.is_valid())
        # Cleanup
        tm1.delete()
        tm2.delete()
        self.t.team_size = None
        self.t.save()
        self.r1.is_team_round = False
        self.r1.save()

    def test_teammates_in_non_team_round(self):
        """Players from the same team in the same game in a non-team round"""
        self.t.team_size = 2
        self.t.save()
        tm = Team.objects.create(tournament=self.t,
                                 name="The test team")
        tm.players.add(self.rp2.player)
        tm.players.add(self.rp4.player)
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data, the_round=self.r1, pool=None)
        self.assertIs(True, form.is_valid())
        # Cleanup
        tm.delete()
        self.t.team_size = None
        self.t.save()

    def test_player_from_wrong_pool(self):
        pool1 = Pool.objects.create(the_round=self.r1,
                                    name='Fixed',
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r1,
                                    name='Variable')
        for rp in self.r1.roundplayer_set.all():
            if rp == self.rp3:
                rp.pool = pool2
            else:
                rp.pool = pool1
            rp.save()
        g = Game.objects.create(name='R1G1',
                                the_round=self.r1,
                                pool=pool1,
                                the_set=GameSet.objects.first())
        initial = {'name': g.name,
                   'game_id': g.pk,
                   'the_set': g.the_set,
                   'external_url': '',
                   'notes': ''}
        data = {'name': g.name,
                'game_id': str(g.pk),
                'the_set': str(g.the_set.pk),
                'external_url': '',
                'notes': '',
                'Austria-Hungary': str(self.rp1.pk),
                'England': str(self.rp2.pk),
                'France': str(self.rp3.pk),
                'Germany': str(self.rp4.pk),
                'Italy': str(self.rp5.pk),
                'Russia': str(self.rp6.pk),
                'Turkey': str(self.rp7.pk)}
        form = GamePlayersForm(data=data, initial=initial, the_round=self.r1, pool=pool1)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'France', 'Select a valid choice. That choice is not one of the available choices.')
        # Form should also 'inherit' pool from Game, if an existing Game is passed in initial
        form = GamePlayersForm(data=data, initial=initial, the_round=self.r1, pool=None)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'France', 'Select a valid choice. That choice is not one of the available choices.')
        # Cleanup
        g.delete()
        for rp in self.r1.roundplayer_set.all():
            rp.pool = None
            rp.save()
        self.r1.pool_set.all().delete()


class BaseGamePlayersFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        today = date.today()
        t = Tournament.objects.create(name='t1',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        cls.r = Round.objects.create(tournament=t,
                                     scoring_system=G_SCORING_SYSTEMS[0].name,
                                     dias=True,
                                     start=datetime.combine(t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        # Seven Players, all of whom are playing this Round
        p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        p3 = Player.objects.create(first_name='Christina', last_name='Calculus')
        p4 = Player.objects.create(first_name='Douglas', last_name='Dragnet')
        p5 = Player.objects.create(first_name='Edwina', last_name='Eggplant')
        p6 = Player.objects.create(first_name='Frank', last_name='Furious')
        p7 = Player.objects.create(first_name='Georgette', last_name='Giant')
        TournamentPlayer.objects.create(player=p1, tournament=t)
        TournamentPlayer.objects.create(player=p2, tournament=t)
        TournamentPlayer.objects.create(player=p3, tournament=t)
        TournamentPlayer.objects.create(player=p4, tournament=t)
        TournamentPlayer.objects.create(player=p5, tournament=t)
        TournamentPlayer.objects.create(player=p6, tournament=t)
        TournamentPlayer.objects.create(player=p7, tournament=t)
        cls.rp1 = RoundPlayer.objects.create(player=p1, the_round=cls.r)
        cls.rp2 = RoundPlayer.objects.create(player=p2, the_round=cls.r)
        cls.rp3 = RoundPlayer.objects.create(player=p3, the_round=cls.r)
        cls.rp4 = RoundPlayer.objects.create(player=p4, the_round=cls.r)
        cls.rp5 = RoundPlayer.objects.create(player=p5, the_round=cls.r)
        cls.rp6 = RoundPlayer.objects.create(player=p6, the_round=cls.r)
        cls.rp7 = RoundPlayer.objects.create(player=p7, the_round=cls.r)

        cls.GamePlayersFormset = formset_factory(GamePlayersForm,
                                                 extra=2,
                                                 formset=BaseGamePlayersFormset)
        # ManagementForm data
        cls.data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }

    def test_formset_needs_round(self):
        """Omit the_round constructor parameter"""
        with self.assertRaises(KeyError):
            self.GamePlayersFormset(pool=None)

    def test_formset_needs_pool(self):
        """Omit pool constructor parameter"""
        with self.assertRaises(KeyError):
            self.GamePlayersFormset(the_round=self.r)

    def test_formset_empty(self):
        """Leave the formset blank"""
        formset = self.GamePlayersFormset(self.data, the_round=self.r, pool=None)
        self.assertIs(True, formset.is_valid())

    def test_formset_add_one_game(self):
        """Add one Game, leave the other form blank"""
        data = self.data.copy()
        data['form-0-name'] = 'OnlyGame'
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-Austria-Hungary'] = str(self.rp1.pk)
        data['form-0-England'] = str(self.rp2.pk)
        data['form-0-France'] = str(self.rp3.pk)
        data['form-0-Germany'] = str(self.rp4.pk)
        data['form-0-Italy'] = str(self.rp5.pk)
        data['form-0-Russia'] = str(self.rp6.pk)
        data['form-0-Turkey'] = str(self.rp7.pk)
        formset = self.GamePlayersFormset(data, the_round=self.r, pool=None)
        self.assertIs(True, formset.is_valid())

    def test_formset_pool(self):
        """Formset for a Pool should pass the Pool down"""
        pool1 = Pool.objects.create(the_round=self.r,
                                    name="Fixed",
                                    board_count=1)
        pool2 = Pool.objects.create(the_round=self.r,
                                    name="Variable")
        # All except one RoundPlayer in pool1
        for rp in self.r.roundplayer_set.all():
            if rp == self.rp6:
                rp.pool = pool2
            else:
                rp.pool = pool1
            rp.save()
        data = self.data.copy()
        data['form-0-name'] = 'OnlyGame'
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-Austria-Hungary'] = str(self.rp1.pk)
        data['form-0-England'] = str(self.rp2.pk)
        data['form-0-France'] = str(self.rp3.pk)
        data['form-0-Germany'] = str(self.rp4.pk)
        data['form-0-Italy'] = str(self.rp5.pk)
        data['form-0-Russia'] = str(self.rp6.pk)
        data['form-0-Turkey'] = str(self.rp7.pk)
        formset = self.GamePlayersFormset(data, the_round=self.r, pool=pool1)
        self.assertIs(False, formset.is_valid())
        # rp6 should be invalid
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, 0, 'Russia', 'Select a valid choice. That choice is not one of the available choices.')
        # Cleanup
        for rp in self.r.roundplayer_set.all():
            rp.pool = None
            rp.save()
        self.r.pool_set.all().delete()

    def test_formset_form_error(self):
        """Add one Game with an error, leave the other form blank"""
        data = self.data.copy()
        data['form-0-name'] = ''
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-Austria-Hungary'] = str(self.rp1.pk)
        data['form-0-England'] = str(self.rp2.pk)
        data['form-0-France'] = str(self.rp3.pk)
        data['form-0-Germany'] = str(self.rp4.pk)
        data['form-0-Italy'] = str(self.rp5.pk)
        data['form-0-Russia'] = str(self.rp6.pk)
        data['form-0-Turkey'] = str(self.rp7.pk)
        formset = self.GamePlayersFormset(data, the_round=self.r, pool=None)
        self.assertIs(False, formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

    def test_formset_duplicate_names(self):
        """Add two Games, with the same name"""
        GAME_NAME = 'BestGame'
        data = self.data.copy()
        data['form-0-name'] = GAME_NAME
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data['form-0-Austria-Hungary'] = str(self.rp1.pk)
        data['form-0-England'] = str(self.rp2.pk)
        data['form-0-France'] = str(self.rp3.pk)
        data['form-0-Germany'] = str(self.rp4.pk)
        data['form-0-Italy'] = str(self.rp5.pk)
        data['form-0-Russia'] = str(self.rp6.pk)
        data['form-0-Turkey'] = str(self.rp7.pk)
        data['form-1-name'] = GAME_NAME
        data['form-1-the_set'] = str(GameSet.objects.first().pk)
        data['form-1-Austria-Hungary'] = str(self.rp7.pk)
        data['form-1-England'] = str(self.rp6.pk)
        data['form-1-France'] = str(self.rp5.pk)
        data['form-1-Germany'] = str(self.rp4.pk)
        data['form-1-Italy'] = str(self.rp3.pk)
        data['form-1-Russia'] = str(self.rp2.pk)
        data['form-1-Turkey'] = str(self.rp1.pk)
        formset = self.GamePlayersFormset(data, the_round=self.r, pool=None)
        self.assertIs(False, formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, None, None, 'Game names must be unique within the tournament')
