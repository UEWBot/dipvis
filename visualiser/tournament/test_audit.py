import json
import datetime as dt

from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import AnonymousUser, User
from django.forms import modelformset_factory
from django.test import TestCase

from tournament.audit import log_form_action, log_formset_actions, log_objects_change
from tournament.forms import PaidForm
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS, DrawSecrecy, Tournament, TournamentPlayer
from tournament.players import Player


class AuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='audit-user')
        cls.tournament = Tournament.objects.create(
            name='Audit tournament',
            start_date=dt.date(2026, 1, 1),
            end_date=dt.date(2026, 1, 2),
            round_scoring_system=R_SCORING_SYSTEMS[0].name,
            tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
            draw_secrecy=DrawSecrecy.SECRET,
        )
        player = Player.objects.create(first_name='Audit', last_name='Player')
        cls.tournament_player = TournamentPlayer.objects.create(
            tournament=cls.tournament,
            player=player,
        )

    def test_log_form_action_uses_structured_change_message(self):
        form = PaidForm(instance=self.tournament_player,
                        data={'paid': 'on'})
        self.assertTrue(form.is_valid())
        obj = form.save()
        log_form_action(self.user, form, obj, CHANGE)

        entry = LogEntry.objects.get()
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.action_flag, CHANGE)
        self.assertEqual(json.loads(entry.change_message), [
            {'changed': {'fields': ['Audit Player']}},
            {'form': {'name': 'PaidForm'}},
        ])

    def test_log_formset_actions_bulk_logs_changed_objects(self):
        player = Player.objects.create(first_name='Second', last_name='Player')
        second = TournamentPlayer.objects.create(tournament=self.tournament,
                                                 player=player)
        formset_type = modelformset_factory(TournamentPlayer,
                                             form=PaidForm,
                                             extra=0)
        formset = formset_type(data={
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '2',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id': str(self.tournament_player.pk),
            'form-0-paid': 'on',
            'form-1-id': str(second.pk),
            'form-1-paid': 'on',
        }, queryset=TournamentPlayer.objects.filter(pk__in=[self.tournament_player.pk, second.pk]))
        self.assertTrue(formset.is_valid())
        formset.save()
        log_formset_actions(self.user, formset)

        self.assertEqual(LogEntry.objects.count(), 2)
        self.assertTrue(all(entry.action_flag == CHANGE for entry in LogEntry.objects.all()))
        messages = [json.loads(entry.change_message) for entry in LogEntry.objects.all()]
        expected_form_marker = {'form': {'name': formset.forms[0].__class__.__name__}}
        for message in messages:
            self.assertIn(expected_form_marker, message)

    def test_log_form_action_skips_anonymous_user(self):
        form = PaidForm(instance=self.tournament_player,
                        data={'paid': 'on'})
        self.assertTrue(form.is_valid())
        obj = form.save()
        log_form_action(AnonymousUser(), form, obj, CHANGE)
        self.assertFalse(LogEntry.objects.exists())

    def test_log_objects_change_records_fields_and_form(self):
        log_objects_change(self.user,
                           [self.tournament_player],
                           ['Paid'],
                           form_name='PaidForm')

        entry = LogEntry.objects.get()
        self.assertEqual(entry.action_flag, CHANGE)
        self.assertEqual(json.loads(entry.change_message), [
            {'changed': {'fields': ['Paid']}},
            {'form': {'name': 'PaidForm'}},
        ])
