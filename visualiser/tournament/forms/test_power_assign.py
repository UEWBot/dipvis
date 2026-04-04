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
Power Assignment Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone

from django.forms.formsets import formset_factory
from django.test import TestCase

from tournament.diplomacy import GameSet, GreatPower
from tournament.forms import BasePowerAssignFormset, PowerAssignForm
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Game, GamePlayer, Round,
                               RoundPlayer, Tournament, TournamentPlayer)
from tournament.players import Player


class PowerAssignFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # We need a Tournament with a Round and a Game with seven GamePlayers
        # Add in an extra player for the Round to ensure that they don't get picked up
        today = date.today()
        t = Tournament.objects.create(name='t1',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        r = Round.objects.create(tournament=t,
                                 scoring_system=G_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 start=datetime.combine(t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        cls.g = Game.objects.create(name='Test Game',
                                    the_round=r,
                                    the_set=GameSet.objects.first())

        cls.p1 = Player.objects.create(first_name='Arthur', last_name='Amphitheatre')
        cls.p2 = Player.objects.create(first_name='Beatrice', last_name='Brontosaurus')
        cls.p3 = Player.objects.create(first_name='Christina', last_name='Calculus')
        cls.p4 = Player.objects.create(first_name='Douglas', last_name='Dragnet')
        cls.p5 = Player.objects.create(first_name='Edwina', last_name='Eggplant')
        cls.p6 = Player.objects.create(first_name='Frank', last_name='Furious')
        cls.p7 = Player.objects.create(first_name='Georgette', last_name='Giant')
        p8 = Player.objects.create(first_name='Harold', last_name='Homeless')
        TournamentPlayer.objects.create(player=cls.p1, tournament=t)
        TournamentPlayer.objects.create(player=cls.p2, tournament=t)
        TournamentPlayer.objects.create(player=cls.p3, tournament=t)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t)
        TournamentPlayer.objects.create(player=cls.p5, tournament=t)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t)
        TournamentPlayer.objects.create(player=p8, tournament=t)
        RoundPlayer.objects.create(player=cls.p1, the_round=r)
        RoundPlayer.objects.create(player=cls.p2, the_round=r)
        RoundPlayer.objects.create(player=cls.p3, the_round=r, sandboxer=True)
        RoundPlayer.objects.create(player=cls.p4, the_round=r)
        RoundPlayer.objects.create(player=cls.p5, the_round=r)
        RoundPlayer.objects.create(player=cls.p6, the_round=r)
        RoundPlayer.objects.create(player=cls.p7, the_round=r)
        RoundPlayer.objects.create(player=p8, the_round=r)
        cls.gp1 = GamePlayer.objects.create(player=cls.p1, game=cls.g)
        cls.gp2 = GamePlayer.objects.create(player=cls.p2, game=cls.g)
        cls.gp3 = GamePlayer.objects.create(player=cls.p3, game=cls.g)
        cls.gp4 = GamePlayer.objects.create(player=cls.p4, game=cls.g)
        cls.gp5 = GamePlayer.objects.create(player=cls.p5, game=cls.g)
        cls.gp6 = GamePlayer.objects.create(player=cls.p6, game=cls.g)
        cls.gp7 = GamePlayer.objects.create(player=cls.p7, game=cls.g)

    def test_init_needs_game(self):
        with self.assertRaises(KeyError):
            PowerAssignForm()

    def test_name_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('name', form.fields)
        attrs = form.fields['name'].widget.attrs
        self.assertEqual(attrs['size'], attrs['maxlength'])

    def test_set_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('the_set', form.fields)

    def test_top_board_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('top_board', form.fields)

    def test_url_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('external_url', form.fields)

    def test_notes_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('notes', form.fields)

    def test_player_fields(self):
        form = PowerAssignForm(game=self.g)
        for gp in self.g.gameplayer_set.all():
            with self.subTest(gp=str(gp)):
                self.assertIs(True, form.fields[str(gp.pk)].required)
                # TODO verify sandboxer annotation

    def test_issues_field(self):
        form = PowerAssignForm(game=self.g)
        self.assertIn('issues', form.fields)
        self.assertIs(True, form.fields['issues'].disabled)
        self.assertIs(False, form.fields['issues'].required)

    def test_player_choices(self):
        """Each player should have a choice of all seven GreatPowers"""
        form = PowerAssignForm(game=self.g)
        # Pick a Player at random - they will all be the same
        the_choices = list(form.fields[str(self.g.gameplayer_set.first().pk)].choices)
        # We should have one per GreatPower, plus the initial empty choice
        self.assertEqual(len(the_choices), 8)
        # Key should be the GreatPower pk, value should be the name
        for i, power in enumerate(GreatPower.objects.all(), 1):
            with self.subTest(power=str(power)):
                self.assertEqual(the_choices[i][0], power.pk)
                self.assertEqual(the_choices[i][1], power.name)

    def test_player_labels(self):
        """The label for each power choice should be the Player's name"""
        form = PowerAssignForm(game=self.g)
        for gp in self.g.gameplayer_set.all():
            with self.subTest(gp=str(gp)):
                # Sandboxers should be flagged
                if gp.roundplayer().sandboxer:
                    self.assertEqual(form.fields[str(gp.pk)].label, str(gp.player)+'*')
                else:
                    self.assertEqual(form.fields[str(gp.pk)].label, str(gp.player))

    def test_success(self):
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.austria.pk),
                str(self.gp3.pk): str(self.england.pk),
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data, game=self.g)
        self.assertIs(True, form.is_valid())

    def test_has_changed(self):
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.austria.pk),
                str(self.gp3.pk): str(self.england.pk),
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data,
                               game=self.g,
                               initial={'name': 'R1G1',
                                        'the_set': GameSet.objects.first(),
                                        str(self.gp1.pk): self.turkey,
                                        str(self.gp2.pk): self.austria,
                                        str(self.gp3.pk): self.england,
                                        str(self.gp4.pk): self.france,
                                        str(self.gp5.pk): self.germany,
                                        str(self.gp6.pk): self.italy,
                                        str(self.gp7.pk): self.russia,
                                        'issues': ''})
        self.assertIs(False, form.has_changed())

    def test_name_error1(self):
        data = {'name': 'R1 G1',
                'the_set': str(GameSet.objects.first().pk),
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.austria.pk),
                str(self.gp3.pk): str(self.england.pk),
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data, game=self.g)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'name', 'Game names cannot contain " "')

    def test_name_error2(self):
        data = {'name': 'R1/G1',
                'the_set': str(GameSet.objects.first().pk),
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.austria.pk),
                str(self.gp3.pk): str(self.england.pk),
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data, game=self.g)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'name', 'Game names cannot contain "/"')

    def test_field_error(self):
        data = {'name': 'R1G1',
                'the_set': 'Non-existent set',
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.austria.pk),
                str(self.gp3.pk): str(self.england.pk),
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data, game=self.g)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, 'the_set', 'Select a valid choice. That choice is not one of the available choices.')

    def test_power_error(self):
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.austria.pk),
                str(self.gp3.pk): 'None',
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data, game=self.g)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, str(self.gp3.pk), 'Select a valid choice. That choice is not one of the available choices.')

    def test_reject_duplicate_powers(self):
        data = {'name': 'R1G1',
                'the_set': str(GameSet.objects.first().pk),
                str(self.gp1.pk): str(self.turkey.pk),
                str(self.gp2.pk): str(self.france.pk),
                str(self.gp3.pk): str(self.england.pk),
                str(self.gp4.pk): str(self.france.pk),
                str(self.gp5.pk): str(self.germany.pk),
                str(self.gp6.pk): str(self.italy.pk),
                str(self.gp7.pk): str(self.russia.pk),
                'issues': ''}
        form = PowerAssignForm(data, game=self.g)
        self.assertIs(False, form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        # Non-field errors still count as errors
        self.assertEqual(len(form.errors), 1)
        self.assertFormError(form, None, 'Power France appears more than once')


class BasePowerAssignFormsetTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # We need two Games with GamePlayers and a Round with no Games
        today = date.today()
        t = Tournament.objects.create(name='t1',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        cls.r1 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        cls.r2 = Round.objects.create(tournament=t,
                                      scoring_system=G_SCORING_SYSTEMS[0].name,
                                      dias=True,
                                      start=datetime.combine(t.start_date, time(hour=17, tzinfo=datetime_timezone.utc)))
        # Deliberately not in alphabetical order
        g1 = Game.objects.create(name='Test Game 2',
                                 the_round=cls.r1,
                                 the_set=GameSet.objects.first())
        g2 = Game.objects.create(name='Test Game 1',
                                 the_round=cls.r1,
                                 the_set=GameSet.objects.first())
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
        RoundPlayer.objects.create(player=p1, the_round=cls.r1)
        RoundPlayer.objects.create(player=p2, the_round=cls.r1)
        RoundPlayer.objects.create(player=p3, the_round=cls.r1)
        RoundPlayer.objects.create(player=p4, the_round=cls.r1)
        RoundPlayer.objects.create(player=p5, the_round=cls.r1)
        RoundPlayer.objects.create(player=p6, the_round=cls.r1)
        RoundPlayer.objects.create(player=p7, the_round=cls.r1)
        cls.gp1 = GamePlayer.objects.create(player=p1, game=g1, power=cls.russia)
        cls.gp2 = GamePlayer.objects.create(player=p2, game=g1, power=cls.turkey)
        cls.gp3 = GamePlayer.objects.create(player=p3, game=g1, power=cls.austria)
        cls.gp4 = GamePlayer.objects.create(player=p4, game=g1, power=cls.england)
        cls.gp5 = GamePlayer.objects.create(player=p5, game=g1, power=cls.france)
        cls.gp6 = GamePlayer.objects.create(player=p6, game=g1, power=cls.germany)
        cls.gp7 = GamePlayer.objects.create(player=p7, game=g1, power=cls.italy)
        cls.gp8 = GamePlayer.objects.create(player=p1, game=g2, power=cls.france)
        cls.gp9 = GamePlayer.objects.create(player=p2, game=g2, power=cls.germany)
        cls.gp10 = GamePlayer.objects.create(player=p3, game=g2, power=cls.russia)
        cls.gp11 = GamePlayer.objects.create(player=p4, game=g2, power=cls.turkey)
        cls.gp12 = GamePlayer.objects.create(player=p5, game=g2, power=cls.italy)
        cls.gp13 = GamePlayer.objects.create(player=p6, game=g2, power=cls.england)
        cls.gp14 = GamePlayer.objects.create(player=p7, game=g2, power=cls.austria)

        cls.PowerAssignFormset = formset_factory(PowerAssignForm,
                                                 extra=0,
                                                 formset=BasePowerAssignFormset)
        # ManagementForm data
        cls.data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '2',
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
        }
        cls.initial = []
        # Ordering must match that used inside the formset
        for game in cls.r1.game_set.order_by('name'):
            game_dict = {'name': game.name,
                         'the_set': game.the_set,
                         'top_board': game.is_top_board,
                         'external_url': game.external_url,
                         'notes': game.notes}
            for gp in game.gameplayer_set.order_by():
                game_dict[str(gp.id)] = gp.power
            cls.initial.append(game_dict)

    def test_formset_needs_round(self):
        """Omit the_round constructor parameter"""
        with self.assertRaises(KeyError):
            self.PowerAssignFormset()

    def test_formset_extra(self):
        """extra must be zero"""
        PowerAssignFormset = formset_factory(PowerAssignForm,
                                             extra=1,
                                             formset=BasePowerAssignFormset)
        with self.assertRaises(AssertionError):
            PowerAssignFormset(the_round=self.r1)

    def test_formset_no_games(self):
        with self.assertRaises(AssertionError):
            self.PowerAssignFormset(the_round=self.r2)

    # TODO Check ordering of games when the Round has Pools

    def test_formset_initial(self):
        """Pass in initial"""
        formset = self.PowerAssignFormset(initial=self.initial, the_round=self.r1)
        # Players should all have their powers assigned
        self.assertNotIn('value="" selected', str(formset))
        #print(str(formset))

    def test_formset_success(self):
        """Complete the form correctly"""
        data = self.data.copy()
        data['form-0-name'] = 'Game1'
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data[f'form-0-{self.gp8.pk}'] = str(self.austria.pk)
        data[f'form-0-{self.gp9.pk}'] = str(self.england.pk)
        data[f'form-0-{self.gp10.pk}'] = str(self.france.pk)
        data[f'form-0-{self.gp11.pk}'] = str(self.germany.pk)
        data[f'form-0-{self.gp12.pk}'] = str(self.italy.pk)
        data[f'form-0-{self.gp13.pk}'] = str(self.russia.pk)
        data[f'form-0-{self.gp14.pk}'] = str(self.turkey.pk)
        data['form-0-issues'] = ''
        data['form-1-name'] = 'Game2'
        data['form-1-the_set'] = str(GameSet.objects.first().pk)
        data[f'form-1-{self.gp1.pk}'] = str(self.austria.pk)
        data[f'form-1-{self.gp2.pk}'] = str(self.england.pk)
        data[f'form-1-{self.gp3.pk}'] = str(self.france.pk)
        data[f'form-1-{self.gp4.pk}'] = str(self.germany.pk)
        data[f'form-1-{self.gp5.pk}'] = str(self.italy.pk)
        data[f'form-1-{self.gp6.pk}'] = str(self.russia.pk)
        data[f'form-1-{self.gp7.pk}'] = str(self.turkey.pk)
        data['form-1-issues'] = ''
        formset = self.PowerAssignFormset(data, the_round=self.r1)
        self.assertIs(True, formset.is_valid())

    def test_formset_form_error(self):
        """Complete the form with an error in one field"""
        data = self.data.copy()
        data['form-0-name'] = 'Game1'
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data[f'form-0-{self.gp8.pk}'] = str(self.austria.pk)
        data[f'form-0-{self.gp9.pk}'] = str(self.england.pk)
        data[f'form-0-{self.gp10.pk}'] = str(self.france.pk)
        data[f'form-0-{self.gp11.pk}'] = str(self.germany.pk)
        data[f'form-0-{self.gp12.pk}'] = str(self.italy.pk)
        data[f'form-0-{self.gp13.pk}'] = str(self.russia.pk)
        data[f'form-0-{self.gp14.pk}'] = str(self.turkey.pk)
        data['form-0-issues'] = ''
        data['form-1-name'] = 'RidiculouslyLongGameName'
        data['form-1-the_set'] = str(GameSet.objects.first().pk)
        data[f'form-1-{self.gp1.pk}'] = str(self.austria.pk)
        data[f'form-1-{self.gp2.pk}'] = str(self.england.pk)
        data[f'form-1-{self.gp3.pk}'] = str(self.france.pk)
        data[f'form-1-{self.gp4.pk}'] = str(self.germany.pk)
        data[f'form-1-{self.gp5.pk}'] = str(self.italy.pk)
        data[f'form-1-{self.gp6.pk}'] = str(self.russia.pk)
        data[f'form-1-{self.gp7.pk}'] = str(self.turkey.pk)
        data['form-1-issues'] = ''
        formset = self.PowerAssignFormset(data, the_round=self.r1)
        self.assertIs(False, formset.is_valid())
        # Should have just one form error, no formset errors
        self.assertEqual(sum(len(err) for err in formset.errors), 1)
        self.assertEqual(formset.total_error_count(), 1)

    def test_formset_duplicate_names(self):
        """Give both Games the same name"""
        GAME_NAME = 'BestGame'
        data = self.data.copy()
        data['form-0-name'] = GAME_NAME
        data['form-0-the_set'] = str(GameSet.objects.first().pk)
        data[f'form-0-{self.gp8.pk}'] = str(self.austria.pk)
        data[f'form-0-{self.gp9.pk}'] = str(self.england.pk)
        data[f'form-0-{self.gp10.pk}'] = str(self.france.pk)
        data[f'form-0-{self.gp11.pk}'] = str(self.germany.pk)
        data[f'form-0-{self.gp12.pk}'] = str(self.italy.pk)
        data[f'form-0-{self.gp13.pk}'] = str(self.russia.pk)
        data[f'form-0-{self.gp14.pk}'] = str(self.turkey.pk)
        data['form-0-issues'] = ''
        data['form-1-name'] = GAME_NAME
        data['form-1-the_set'] = str(GameSet.objects.first().pk)
        data[f'form-1-{self.gp1.pk}'] = str(self.austria.pk)
        data[f'form-1-{self.gp2.pk}'] = str(self.england.pk)
        data[f'form-1-{self.gp3.pk}'] = str(self.france.pk)
        data[f'form-1-{self.gp4.pk}'] = str(self.germany.pk)
        data[f'form-1-{self.gp5.pk}'] = str(self.italy.pk)
        data[f'form-1-{self.gp6.pk}'] = str(self.russia.pk)
        data[f'form-1-{self.gp7.pk}'] = str(self.turkey.pk)
        data['form-1-issues'] = ''
        formset = self.PowerAssignFormset(data, the_round=self.r1)
        self.assertIs(False, formset.is_valid())
        # Should have no form errors, one formset error
        self.assertEqual(sum(len(err) for err in formset.errors), 0)
        self.assertEqual(formset.total_error_count(), 1)
        self.assertFormSetError(formset, None, None, 'Game names must be unique within the tournament')
