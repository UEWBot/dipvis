# Diplomacy Tournament Visualiser
# Copyright (C) 2026 Chris Brand

from datetime import date, timedelta

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from tournament.circuits import Circuit, CircuitPlayer, CircuitSeries
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS, DrawSecrecy,
                               Tournament, TournamentPlayer)
from tournament.players import Player


class CircuitViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.today = date.today()
        cls.t1 = Tournament.objects.create(name='Circuit Tournament 1',
                                           start_date=cls.today,
                                           end_date=cls.today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           editable=False,
                                           is_published=True)
        cls.t2 = Tournament.objects.create(name='Circuit Tournament 2',
                                           start_date=cls.today + timedelta(days=7),
                                           end_date=cls.today + timedelta(days=7, hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           editable=False,
                                           is_published=True)

        cls.p1 = Player.objects.create(first_name='Alice', last_name='Alpha')
        cls.p2 = Player.objects.create(first_name='Bob', last_name='Beta')

        TournamentPlayer.objects.create(player=cls.p1, tournament=cls.t1, score=10.0)
        TournamentPlayer.objects.create(player=cls.p2, tournament=cls.t1, score=5.0)
        TournamentPlayer.objects.create(player=cls.p1, tournament=cls.t2, score=7.0)
        TournamentPlayer.objects.create(player=cls.p2, tournament=cls.t2, score=9.0)

        cls.circuit = Circuit.objects.create(name='Test Circuit',
                                             start_date=cls.today,
                                             end_date=cls.today + timedelta(days=14),
                                             scoring_system='Sum best 3 tournament percentiles')
        cls.circuit.tournaments.add(cls.t1, cls.t2)

        cls.series = CircuitSeries.objects.create(name='Circuit Series One',
                                                  description='Series for tests')
        cls.series.circuits.add(cls.circuit)

    def test_circuit_index(self):
        response = self.client.get(reverse('circuit_index'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuits/index.html')
        self.assertContains(response, 'Test Circuit')

    def test_circuit_series_detail(self):
        response = self.client.get(reverse('circuit_series_detail', args=(self.series.slug,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuits/series_detail.html')
        self.assertContains(response, 'Test Circuit')
        self.assertContains(response, 'Series for tests')

    def test_circuit_series_detail_invalid(self):
        response = self.client.get(reverse('circuit_series_detail', args=('missing-series',)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_circuit_series_detail_shows_empty_circuits_message(self):
        empty_series = CircuitSeries.objects.create(name='Empty circuit series',
                                                    description='No circuits yet')
        response = self.client.get(reverse('circuit_series_detail',
                                           args=(empty_series.slug,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No circuits in the database')

    def test_circuit_detail(self):
        response = self.client.get(reverse('circuit_detail', args=(self.circuit.id,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuits/detail.html')
        self.assertContains(response, 'Test Circuit')
        self.assertContains(response, 'Scores')
        self.assertContains(response, 'Part of the following series:')
        self.assertContains(response, self.series.get_absolute_url())

    def test_circuit_detail_shows_empty_tournaments_message(self):
        empty_circuit = Circuit.objects.create(name='Empty Circuit',
                                               start_date=self.today,
                                               end_date=self.today,
                                               scoring_system='Sum best 3 tournament percentiles')
        response = self.client.get(reverse('circuit_detail', args=(empty_circuit.id,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No tournaments in this circuit yet.')

    def test_circuit_detail_prefers_wdr_link_over_wdd(self):
        self.circuit.wdr_circuit_id = 456
        self.circuit.wdd_circuit_id = 123
        self.circuit.save(update_fields=['wdr_circuit_id', 'wdd_circuit_id'])
        response = self.client.get(reverse('circuit_detail', args=(self.circuit.id,)),
                                   secure=True)
        self.assertContains(response, 'View on WDR')
        self.assertNotContains(response, 'View on WDD')

    def test_circuit_detail_shows_wdd_link_when_no_wdr(self):
        self.circuit.wdr_circuit_id = None
        self.circuit.wdd_circuit_id = 123
        self.circuit.save(update_fields=['wdr_circuit_id', 'wdd_circuit_id'])
        response = self.client.get(reverse('circuit_detail', args=(self.circuit.id,)),
                                   secure=True)
        self.assertContains(response, 'View on WDD')

    def test_circuit_detail_invalid(self):
        response = self.client.get(reverse('circuit_detail', args=(999999,)), secure=True)
        self.assertEqual(response.status_code, 404)

    def test_circuit_scores(self):
        response = self.client.get(reverse('circuit_scores', args=(self.circuit.id,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuits/scores.html')
        # Derived rows show "percentile (tournament score)" values.
        self.assertContains(response, '0.500 ')
        self.assertContains(response, '>10.00<')
        self.assertContains(response, '0.000 ')
        self.assertContains(response, '>5.00<')
        self.assertContains(response, '0.000 ')
        self.assertContains(response, '>7.00<')
        self.assertContains(response, '0.500 ')
        self.assertContains(response, '>9.00<')

    def test_circuit_scores_handles_missing_tp_link(self):
        cp = CircuitPlayer.objects.get(circuit=self.circuit, player=self.p1)
        dropped_tp = TournamentPlayer.objects.get(player=self.p1, tournament=self.t2)
        cp.tournamentplayers.remove(dropped_tp)

        response = self.client.get(reverse('circuit_scores', args=(self.circuit.id,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuits/scores.html')
        self.assertContains(response, 'Circuit Tournament 2')
        self.assertNotContains(response, dropped_tp.get_absolute_url())

    def test_circuit_player_detail(self):
        cp = CircuitPlayer.objects.filter(circuit=self.circuit, player=self.p1).first()
        response = self.client.get(reverse('circuit_player_detail',
                                           args=(self.circuit.id, cp.id)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuits/player_detail.html')
        self.assertContains(response, str(self.p1))

    def test_circuit_player_detail_wrong_circuit(self):
        other = Circuit.objects.create(name='Other Circuit',
                                       start_date=self.today,
                                       end_date=self.today + timedelta(days=14),
                                       scoring_system='Sum best 3 tournament percentiles')
        cp = CircuitPlayer.objects.filter(circuit=self.circuit, player=self.p1).first()
        response = self.client.get(reverse('circuit_player_detail', args=(other.id, cp.id)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_circuit_scores_query_count_scales_well_with_more_players(self):
        url = reverse('circuit_scores', args=(self.circuit.id,))

        with CaptureQueriesContext(connection) as baseline_ctx:
            response = self.client.get(url, secure=True)
            self.assertEqual(response.status_code, 200)
        baseline_queries = len(baseline_ctx)

        extra_players = [
            Player.objects.create(first_name=f'Extra{i}', last_name='Player')
            for i in range(10)
        ]
        for i, player in enumerate(extra_players):
            TournamentPlayer.objects.create(player=player, tournament=self.t1, score=20.0 + i)
            TournamentPlayer.objects.create(player=player, tournament=self.t2, score=10.0 + i)
        self.circuit.add_or_update_circuit_players()

        with CaptureQueriesContext(connection) as expanded_ctx:
            response = self.client.get(url, secure=True)
            self.assertEqual(response.status_code, 200)
        expanded_queries = len(expanded_ctx)

        # Rendering more rows should not trigger N+1 database behaviour.
        self.assertLessEqual(expanded_queries, baseline_queries + 2)
