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
Award Forms Tests for the Diplomacy Tournament Visualiser.
"""
from datetime import date, timedelta

from django.forms.formsets import formset_factory
from django.test import TestCase

from tournament.diplomacy import GreatPower
from tournament.forms import AwardForm, BaseAwardsFormset
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS, Award,
                               DrawSecrecy, Tournament, TournamentPlayer)
from tournament.players import Player


class AwardFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
        # One Player who didn't participate
        Player.objects.create(first_name='Charlotte', last_name='Dotty')
        p3 = Player.objects.create(first_name='Edward', last_name='Foxtrot')
        p4 = Player.objects.create(first_name='Georgette', last_name='Halitosis')
        today = date.today()
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET)
        cls.a1 = Award.objects.create(name='Nicest Player',
                                      description='Player who was the nicest')
        cls.tp1 = TournamentPlayer.objects.create(player=p3, tournament=cls.t)
        # Include one unranked player, who shouldn't be pickable
        cls.tp2 = TournamentPlayer.objects.create(player=p4, tournament=cls.t, unranked=True)
        cls.tp3 = TournamentPlayer.objects.create(player=p1, tournament=cls.t)
        cls.t.awards.add(cls.a1)
        cls.t.save()

    def test_init_needs_tournament(self):
        with self.assertRaises(KeyError):
            AwardForm(award_name=str(self.a1))

    def test_init_needs_award_name(self):
        with self.assertRaises(KeyError):
            AwardForm(tournament=self.t)

    def test_awards_form_player_field_label(self):
        form = AwardForm(tournament=self.t, award_name=str(self.a1))
        self.assertEqual(form.fields['players'].label, str(self.a1))

    def test_awards_form_player_choices(self):
        form = AwardForm(tournament=self.t, award_name=str(self.a1))
        the_choices = list(form.fields['players'].choices)
        # We should have one per TournamentPlayer
        self.assertEqual(len(the_choices), self.t.tournamentplayer_set.filter(unranked=False).count())
        # The keys should be the TournamentPlayer pks
        self.assertEqual(the_choices[0][0].value, self.tp3.pk)
        # and the values should be the Player names, in alphabetical order
        self.assertEqual(the_choices[0][1], self.tp3.player.sortable_str())
        self.assertEqual(the_choices[1][1], self.tp1.player.sortable_str())

    def test_award_form_has_changed(self):
        self.tp3.awards.add(self.a1)
        form = AwardForm(tournament=self.t,
                         award_name=str(self.a1),
                         initial={'award': self.a1.id,
                                  'players': [self.tp3.id]},
                         data={'award': str(self.a1.id),
                               'players': [str(self.tp3.id)]})
        self.assertIs(False, form.has_changed())
        # Cleanup
        self.tp3.awards.remove(self.a1)


class AwardsFormsetTest(TestCase):
    fixtures = ['game_sets.json']

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
        p3 = Player.objects.create(first_name='Edwin', last_name='Flubber')
        cls.tp1 = TournamentPlayer.objects.create(player=p1, tournament=cls.t)
        cls.tp2 = TournamentPlayer.objects.create(player=p2, tournament=cls.t)
        cls.tp3 = TournamentPlayer.objects.create(player=p3, tournament=cls.t)
        cls.a1 = Award.objects.create(name='Nicest Player',
                                      description='Player who was the nicest')
        cls.a2 = Award.objects.create(name='Best Austria',
                                      description='Who got the best result playing Austria',
                                      power=GreatPower.objects.get(abbreviation='A'))
        cls.a3 = Award.objects.create(name='Tallest Player',
                                      description='Player of unusual size')
        cls.t.awards.add(cls.a1)
        cls.t.awards.add(cls.a2)
        cls.t.awards.add(cls.a3)
        cls.t.save()
        cls.tp1.awards.add(cls.a1)
        cls.tp2.awards.add(cls.a2)
        cls.tp3.awards.add(cls.a2)

        cls.AwardsFormset = formset_factory(AwardForm, extra=0, formset=BaseAwardsFormset)

    def test_awards_formset_creation(self):
        formset = self.AwardsFormset(tournament=self.t)
        awards = set()
        for form in formset:
            with self.subTest(award=form['award'].initial):
                if form['award'].initial == self.a1.id:
                    self.assertEqual(form['players'].initial, [self.tp1.id])
                elif form['award'].initial == self.a2.id:
                    self.assertEqual(form['players'].initial, [self.tp2.id, self.tp3.id])
                else:
                    self.assertEqual(form['players'].initial, [])
            awards.add(form['award'].initial)
        # All three Awards should be present
        self.assertEqual(len(formset), 3)
        self.assertIn(self.a1.id, awards)
        self.assertIn(self.a2.id, awards)
        self.assertIn(self.a3.id, awards)

    def test_awards_formset_initial(self):
        initial = []
        initial.append({'award': self.a1.id, 'players': [self.tp2.id]})
        formset = self.AwardsFormset(tournament=self.t, initial=initial)
        # Explicit initial should override implicit
        for form in formset:
            self.assertEqual(form['players'].initial, [self.tp2.id])
        self.assertEqual(len(formset), len(initial))
