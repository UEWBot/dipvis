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
from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone

from django.test import TestCase

from tournament.diplomacy import GameSet, GreatPower
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS, Award,
                               AwardRecipient, DrawSecrecy, Game, GamePlayer,
                               Round, Tournament, TournamentAward,
                               TournamentPlayer)
from tournament.players import Player

from . import AwardRecipientForm, AwardRecipientFormSet


class AwardRecipientFormTest(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        p1 = Player.objects.create(first_name='Arthur', last_name='Bottom')
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
        cls.ta1 = TournamentAward.objects.create(tournament=cls.t, award=cls.a1)
        cls.tp1 = TournamentPlayer.objects.create(player=p3, tournament=cls.t)
        # Include one unranked player, who shouldn't be pickable
        cls.tp2 = TournamentPlayer.objects.create(player=p4, tournament=cls.t, unranked=True)
        cls.tp3 = TournamentPlayer.objects.create(player=p1, tournament=cls.t)
        cls.r = Round.objects.create(tournament=cls.t,
                                     scoring_system=R_SCORING_SYSTEMS[0].name,
                                     dias=True,
                                     start=datetime.combine(cls.t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        cls.g = Game.objects.create(name='g1',
                                    started_at=cls.r.start,
                                    the_round=cls.r,
                                    the_set=GameSet.objects.first())

    def test_init_needs_tournament_award(self):
        with self.assertRaises(KeyError):
            AwardRecipientForm()

    def test_tournament_player_choices_excludes_unranked(self):
        form = AwardRecipientForm(tournament_award=self.ta1)
        player_pks = {str(choice[0]) for choice in form.fields['tournament_player'].choices if choice[0]}
        self.assertNotIn(str(self.tp2.pk), player_pks)
        self.assertIn(str(self.tp1.pk), player_pks)
        self.assertIn(str(self.tp3.pk), player_pks)

    def test_game_choices_restricted_to_tournament(self):
        other_t = Tournament.objects.create(name='t2',
                                            start_date=self.t.start_date,
                                            end_date=self.t.end_date,
                                            round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                            tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                            draw_secrecy=DrawSecrecy.SECRET)
        other_r = Round.objects.create(tournament=other_t,
                                       scoring_system=R_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=datetime.combine(other_t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        other_g = Game.objects.create(name='g2',
                                      started_at=other_r.start,
                                      the_round=other_r,
                                      the_set=GameSet.objects.first())
        form = AwardRecipientForm(tournament_award=self.ta1)
        game_pks = {str(choice[0]) for choice in form.fields['game'].choices if choice[0]}
        self.assertIn(str(self.g.pk), game_pks)
        self.assertNotIn(str(other_g.pk), game_pks)
        # Cleanup
        other_t.delete()

    def test_game_field_not_required(self):
        form = AwardRecipientForm(tournament_award=self.ta1)
        self.assertFalse(form.fields['game'].required)

    def test_game_choices_restricted_to_games_player_played(self):
        other_r = Round.objects.create(tournament=self.t,
                                       scoring_system=R_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=datetime.combine(self.t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)) + timedelta(hours=1))
        other_g = Game.objects.create(name='g2',
                                      started_at=other_r.start,
                                      the_round=other_r,
                                      the_set=GameSet.objects.first())
        GamePlayer.objects.create(player=self.tp1.player, game=self.g)
        form = AwardRecipientForm(data={'tournament_player': str(self.tp1.pk),
                                        'game': str(other_g.pk)},
                                  tournament_award=self.ta1)
        choices = {str(choice[0]) for choice in form.fields['game'].choices if choice[0]}
        self.assertIn(str(self.g.pk), choices)
        self.assertNotIn(str(other_g.pk), choices)

    def test_game_not_played_by_player_fails_validation(self):
        other_r = Round.objects.create(tournament=self.t,
                                       scoring_system=R_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=datetime.combine(self.t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)) + timedelta(hours=1))
        other_g = Game.objects.create(name='g2',
                                      started_at=other_r.start,
                                      the_round=other_r,
                                      the_set=GameSet.objects.first())
        form = AwardRecipientForm(data={'tournament_player': str(self.tp1.pk),
                                        'game': str(other_g.pk)},
                                  tournament_award=self.ta1)
        self.assertFalse(form.is_valid())
        self.assertTrue(any('Select a valid choice' in message for message in form.errors['game']))

    def test_power_specific_award_game_choices_restrict_to_that_power(self):
        power = GreatPower.objects.get(abbreviation='A')
        self.ta1.award.power = power
        self.ta1.award.save()
        other_r = Round.objects.create(tournament=self.t,
                                       scoring_system=R_SCORING_SYSTEMS[0].name,
                                       dias=True,
                                       start=datetime.combine(self.t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)) + timedelta(hours=1))
        other_g = Game.objects.create(name='g2',
                                      started_at=other_r.start,
                                      the_round=other_r,
                                      the_set=GameSet.objects.first())
        GamePlayer.objects.create(player=self.tp1.player, game=self.g, power=power)
        GamePlayer.objects.create(player=self.tp1.player, game=other_g, power=GreatPower.objects.get(abbreviation='E'))
        form = AwardRecipientForm(data={'tournament_player': str(self.tp1.pk),
                                        'game': str(other_g.pk)},
                                  tournament_award=self.ta1)
        choices = {str(choice[0]) for choice in form.fields['game'].choices if choice[0]}
        self.assertIn(str(self.g.pk), choices)
        self.assertNotIn(str(other_g.pk), choices)


class AwardRecipientFormSetTest(TestCase):
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
        cls.tp1 = TournamentPlayer.objects.create(player=p1, tournament=cls.t)
        cls.tp2 = TournamentPlayer.objects.create(player=p2, tournament=cls.t)
        cls.a1 = Award.objects.create(name='Nicest Player',
                                      description='Player who was the nicest')
        cls.ta1 = TournamentAward.objects.create(tournament=cls.t, award=cls.a1)

    def setUp(self):
        self.ar1 = AwardRecipient.objects.create(tournament_award=self.ta1, tournament_player=self.tp1)

    def tearDown(self):
        AwardRecipient.objects.filter(tournament_award=self.ta1).delete()

    def test_formset_lists_existing_recipients(self):
        formset = AwardRecipientFormSet(instance=self.ta1)
        recipients = {form.instance.pk for form in formset.forms if form.instance.pk}
        self.assertIn(self.ar1.pk, recipients)

    def test_formset_has_extra_blank_forms(self):
        formset = AwardRecipientFormSet(instance=self.ta1)
        # One existing recipient, plus two blank extra forms
        self.assertEqual(len(formset.forms), 3)

    def test_formset_can_add_recipient(self):
        data = {'awardrecipient_set-TOTAL_FORMS': '3',
               'awardrecipient_set-INITIAL_FORMS': '1',
               'awardrecipient_set-MIN_NUM_FORMS': '0',
               'awardrecipient_set-MAX_NUM_FORMS': '1000',
               'awardrecipient_set-0-id': str(self.ar1.pk),
               'awardrecipient_set-0-tournament_player': str(self.tp1.id),
               'awardrecipient_set-0-game': '',
               'awardrecipient_set-1-id': '',
               'awardrecipient_set-1-tournament_player': str(self.tp2.id),
               'awardrecipient_set-1-game': '',
               'awardrecipient_set-2-id': '',
               'awardrecipient_set-2-tournament_player': '',
               'awardrecipient_set-2-game': ''}
        formset = AwardRecipientFormSet(data, instance=self.ta1)
        self.assertTrue(formset.is_valid())
        formset.save()
        self.assertEqual(self.ta1.awardrecipient_set.count(), 2)

    def test_formset_can_delete_recipient(self):
        data = {'awardrecipient_set-TOTAL_FORMS': '3',
               'awardrecipient_set-INITIAL_FORMS': '1',
               'awardrecipient_set-MIN_NUM_FORMS': '0',
               'awardrecipient_set-MAX_NUM_FORMS': '1000',
               'awardrecipient_set-0-id': str(self.ar1.pk),
               'awardrecipient_set-0-tournament_player': str(self.tp1.id),
               'awardrecipient_set-0-game': '',
               'awardrecipient_set-0-DELETE': 'on',
               'awardrecipient_set-1-id': '',
               'awardrecipient_set-1-tournament_player': '',
               'awardrecipient_set-1-game': '',
               'awardrecipient_set-2-id': '',
               'awardrecipient_set-2-tournament_player': '',
               'awardrecipient_set-2-game': ''}
        formset = AwardRecipientFormSet(data, instance=self.ta1)
        self.assertTrue(formset.is_valid())
        formset.save()
        self.assertEqual(self.ta1.awardrecipient_set.count(), 0)
