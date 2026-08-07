# Diplomacy Tournament Visualiser
# Copyright (C) 2024 Chris Brand
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
Tests for Circuit models
"""

from datetime import date
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from tournament.circuits import (_percentiles, Circuit, CircuitPlayer,
                                 CircuitSeries,
                                 CScoringSumPercentiles,
                                 _sync_circuit_players_on_tournament_m2m_change,
                                 find_circuit_scoring_system,
                                 validate_circuit_scoring_system)
from tournament.models import (DrawSecrecy, InvalidScoringSystem,
                               R_SCORING_SYSTEMS, Tournament,
                               TournamentPlayer)
from tournament.players import Player


class CircuitScoringTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    def test_c_scoring_sum_percentiles_str(self):
        scoring = CScoringSumPercentiles('My circuit scoring', 3)
        self.assertEqual(str(scoring), 'My circuit scoring')

    def test_c_scoring_sum_percentiles(self):
        today = date.today()
        t = Tournament.objects.create(name='Circuit percentile test',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system='Sum all round scores',
                                      draw_secrecy=DrawSecrecy.SECRET)
        p1, p2, p3 = list(Player.objects.order_by('pk')[:3])
        tp1 = t.tournamentplayer_set.create(player=p1, score=10.0)
        tp2 = t.tournamentplayer_set.create(player=p2, score=20.0)
        tp3 = t.tournamentplayer_set.create(player=p3, score=30.0)

        percentiles = _percentiles([tp1, tp2, tp3])

        self.assertEqual(percentiles[p1], 0.0)
        self.assertEqual(percentiles[p2], 1 / 3)
        self.assertEqual(percentiles[p3], 2 / 3)

    def test_c_scoring_sum_percentiles_empty(self):
        percentiles = _percentiles([])
        self.assertEqual(percentiles, {})

    def test_c_scoring_sum_percentiles_ties_share_percentile(self):
        today = date.today()
        t = Tournament.objects.create(name='Circuit percentile ties test',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system='Sum all round scores',
                                      draw_secrecy=DrawSecrecy.SECRET)
        p1, p2, p3 = list(Player.objects.order_by('pk')[:3])
        tp1 = t.tournamentplayer_set.create(player=p1, score=10.0)
        tp2 = t.tournamentplayer_set.create(player=p2, score=10.0)
        tp3 = t.tournamentplayer_set.create(player=p3, score=30.0)

        percentiles = _percentiles([tp1, tp2, tp3])

        self.assertEqual(percentiles[p1], 0.0)
        self.assertEqual(percentiles[p2], 0.0)
        self.assertEqual(percentiles[p3], 2 / 3)

    def test_c_percentiles_single_player(self):
        today = date.today()
        t = Tournament.objects.create(name='Circuit percentile single test',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system='Sum all round scores',
                                      draw_secrecy=DrawSecrecy.SECRET)
        p1 = Player.objects.order_by('pk').first()
        tp1 = t.tournamentplayer_set.create(player=p1, score=10.0)
        percentiles = _percentiles([tp1])
        self.assertEqual(percentiles[p1], 0.0)

    def test_c_percentiles_all_tied(self):
        today = date.today()
        t = Tournament.objects.create(name='Circuit percentile all tied test',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system='Sum all round scores',
                                      draw_secrecy=DrawSecrecy.SECRET)
        p1, p2, p3 = list(Player.objects.order_by('pk')[:3])
        tp1 = t.tournamentplayer_set.create(player=p1, score=10.0)
        tp2 = t.tournamentplayer_set.create(player=p2, score=10.0)
        tp3 = t.tournamentplayer_set.create(player=p3, score=10.0)
        percentiles = _percentiles([tp1, tp2, tp3])
        self.assertEqual(percentiles[p1], 0.0)
        self.assertEqual(percentiles[p2], 0.0)
        self.assertEqual(percentiles[p3], 0.0)

    def test_c_scoring_sum_percentiles_uses_best_three_scores_only(self):
        today = date.today()
        p1 = Player.objects.order_by('pk').first()
        p2 = Player.objects.order_by('pk')[1]

        circuit = Circuit.objects.create(name='Four tournament circuit',
                                         start_date=today,
                                         end_date=today,
                                         scoring_system='Sum best 3 tournament percentiles')
        tournaments = [
            Tournament.objects.create(name=f'Circuit best-three test {n}',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system='Sum all round scores',
                                      draw_secrecy=DrawSecrecy.SECRET)
            for n in range(4)
        ]

        p1_tp_ids = []
        for score, t in zip([10.0, 20.0, 30.0, 40.0], tournaments):
            tp1 = t.tournamentplayer_set.create(player=p1, score=score)
            p1_tp_ids.append(tp1.id)
            t.tournamentplayer_set.create(player=p2, score=score - 5.0)

        circuit.tournaments.set(tournaments)

        scoring = circuit.scoring_system_obj()
        scores = scoring.scores(circuit, circuit.circuitplayer_set.all())

        # p1 beats p2 in each tournament -> percentile 0.5 each time. Best 3 count.
        self.assertEqual(scores[p1], 1.5)

    def test_c_scoring_sum_percentiles_player_absent_from_some_tournaments(self):
        """A circuit player who didn't attend every tournament should score only from attended ones."""
        today = date.today()
        p1, p2 = list(Player.objects.order_by('pk')[:2])

        circuit = Circuit.objects.create(name='Absent player circuit',
                                         start_date=today,
                                         end_date=today,
                                         scoring_system='Sum best 3 tournament percentiles')
        t1 = Tournament.objects.create(name='Absent player t1',
                                       start_date=today,
                                       end_date=today,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system='Sum all round scores',
                                       draw_secrecy=DrawSecrecy.SECRET)
        t2 = Tournament.objects.create(name='Absent player t2',
                                       start_date=today,
                                       end_date=today,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system='Sum all round scores',
                                       draw_secrecy=DrawSecrecy.SECRET)
        circuit.tournaments.set([t1, t2])

        # p1 played in both tournaments; p2 played only in t1
        tp1_t1 = t1.tournamentplayer_set.create(player=p1, score=20.0)
        tp2_t1 = t1.tournamentplayer_set.create(player=p2, score=10.0)
        tp1_t2 = t2.tournamentplayer_set.create(player=p1, score=30.0)

        cp1 = CircuitPlayer.objects.create(player=p1, circuit=circuit)
        cp1.tournamentplayers.set([tp1_t1, tp1_t2])
        cp2 = CircuitPlayer.objects.create(player=p2, circuit=circuit)
        cp2.tournamentplayers.set([tp2_t1])

        scoring = circuit.scoring_system_obj()
        scores = scoring.scores(circuit, circuit.circuitplayer_set.all())

        # p1 is the only circuit player in t2, so percentile there is 0.0.
        # In t1, p1 beats p2, so p1's percentile is 0.5, p2's is 0.0.
        # p1 circuit score = 0.5 + 0.0 = 0.5; p2 circuit score = 0.0.
        self.assertIn(p1, scores)
        self.assertIn(p2, scores)
        self.assertAlmostEqual(scores[p1], 0.5)
        self.assertAlmostEqual(scores[p2], 0.0)

    def test_c_scoring_scored_rounds_exceeds_tournaments_attended(self):
        """When scored_rounds > tournaments attended, all attended tournaments count."""
        today = date.today()
        p1, p2 = list(Player.objects.order_by('pk')[:2])
        circuit = Circuit.objects.create(name='Too few tournaments circuit',
                                         start_date=today,
                                         end_date=today,
                                         scoring_system='Sum best 3 tournament percentiles')
        # scored_rounds=3 but circuit only has 2 tournaments
        t1 = Tournament.objects.create(name='Too few t1',
                                       start_date=today,
                                       end_date=today,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system='Sum all round scores',
                                       draw_secrecy=DrawSecrecy.SECRET)
        t2 = Tournament.objects.create(name='Too few t2',
                                       start_date=today,
                                       end_date=today,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system='Sum all round scores',
                                       draw_secrecy=DrawSecrecy.SECRET)
        circuit.tournaments.set([t1, t2])
        tp1_t1 = t1.tournamentplayer_set.create(player=p1, score=20.0)
        tp2_t1 = t1.tournamentplayer_set.create(player=p2, score=10.0)
        tp1_t2 = t2.tournamentplayer_set.create(player=p1, score=30.0)
        tp2_t2 = t2.tournamentplayer_set.create(player=p2, score=20.0)
        cp1 = CircuitPlayer.objects.create(player=p1, circuit=circuit)
        cp1.tournamentplayers.set([tp1_t1, tp1_t2])
        cp2 = CircuitPlayer.objects.create(player=p2, circuit=circuit)
        cp2.tournamentplayers.set([tp2_t1, tp2_t2])
        scoring = circuit.scoring_system_obj()
        scores = scoring.scores(circuit, circuit.circuitplayer_set.all())
        # p1 beats p2 in both; percentile 0.5 each time; scored_rounds=3 but only 2 available
        self.assertAlmostEqual(scores[p1], 1.0)
        self.assertAlmostEqual(scores[p2], 0.0)

    def test_c_scoring_scored_rounds_zero(self):
        """When scored_rounds=0, all circuit scores are zero regardless of tournament results."""
        today = date.today()
        p1 = Player.objects.order_by('pk').first()
        circuit = Circuit.objects.create(name='Zero rounds circuit',
                                         start_date=today,
                                         end_date=today,
                                         scoring_system='Sum best 3 tournament percentiles')
        t1 = Tournament.objects.create(name='Zero rounds t1',
                                       start_date=today,
                                       end_date=today,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system='Sum all round scores',
                                       draw_secrecy=DrawSecrecy.SECRET)
        circuit.tournaments.add(t1)
        tp1 = t1.tournamentplayer_set.create(player=p1, score=30.0)
        cp1 = CircuitPlayer.objects.create(player=p1, circuit=circuit)
        cp1.tournamentplayers.add(tp1)
        scoring = CScoringSumPercentiles('Zero rounds', scored_rounds=0)
        scores = scoring.scores(circuit, circuit.circuitplayer_set.all())
        self.assertEqual(scores[p1], 0.0)


class CircuitUtilsTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    def test_find_c_scoring_system_invalid(self):
        self.assertIsNone(find_circuit_scoring_system('not-a-system'))

    def test_find_c_scoring_system_valid(self):
        system = find_circuit_scoring_system('Sum best 3 tournament percentiles')
        self.assertIsNotNone(system)

    def test_validate_c_scoring_system_invalid(self):
        with self.assertRaises(ValidationError):
            validate_circuit_scoring_system('not-a-system')

    def test_validate_c_scoring_system_valid(self):
        validate_circuit_scoring_system('Sum best 3 tournament percentiles')


class CircuitTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.today = date.today()
        cls.p1, cls.p2, cls.p3 = list(Player.objects.order_by('pk')[:3])

    def _new_tournament(self, name):
        return Tournament.objects.create(name=name,
                                         start_date=self.today,
                                         end_date=self.today,
                                         round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                         tournament_scoring_system='Sum all round scores',
                                         draw_secrecy=DrawSecrecy.SECRET)

    def test_circuit_save_accepts_update_fields(self):
        circuit = Circuit.objects.create(name='Save update_fields',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.scoring_system = 'Sum best 3 tournament percentiles'
        circuit.save(update_fields=['scoring_system'])

    def test_circuit_str(self):
        circuit = Circuit.objects.create(name='String circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        self.assertEqual(str(circuit), f'String circuit {self.today.year}')

    def test_circuit_get_absolute_url(self):
        circuit = Circuit.objects.create(name='Missing route circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        self.assertEqual(circuit.get_absolute_url(),
                         reverse('circuit_detail', args=(circuit.id,)))

    def test_scoring_system_obj_invalid_raises(self):
        circuit = Circuit.objects.create(name='Invalid scoring obj circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.scoring_system = 'not-a-system'
        with self.assertRaises(InvalidScoringSystem):
            circuit.scoring_system_obj()

    def test_save_non_scoring_update_fields_skips_update_scores(self):
        circuit = Circuit.objects.create(name='Skip update_scores circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.name = 'Skip update_scores circuit v2'

        with patch.object(Circuit, 'update_scores', autospec=True) as mock_update:
            circuit.save(update_fields=['name'])
        mock_update.assert_not_called()

    def test_save_invalid_scoring_system_hits_validation_branch(self):
        circuit = Circuit.objects.create(name='Invalid scoring save circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.scoring_system = 'not-a-system'

        with patch.object(Circuit, 'update_scores', autospec=True) as mock_update:
            circuit.save(update_fields=['scoring_system'])
        mock_update.assert_called_once_with(circuit)

    def test_update_scores_uses_associated_tournament_players(self):
        t = self._new_tournament('Scoring source tournament')
        circuit = Circuit.objects.create(name='Scoped scoring circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.tournaments.add(t)

        tp1 = t.tournamentplayer_set.create(player=self.p1, score=10.0)
        tp2 = t.tournamentplayer_set.create(player=self.p2, score=5.0)
        t.tournamentplayer_set.create(player=self.p3, score=100.0)

        cp1 = CircuitPlayer.objects.create(player=self.p1, circuit=circuit)
        cp1.tournamentplayers.add(tp1)
        cp2 = CircuitPlayer.objects.create(player=self.p2, circuit=circuit)
        cp2.tournamentplayers.add(tp2)

        circuit.update_scores()

        cp1.refresh_from_db()
        cp2.refresh_from_db()
        self.assertEqual(cp1.score, 0.5)
        self.assertEqual(cp2.score, 0.0)

    def test_update_scores_excludes_unlinked_tp_from_percentile(self):
        """A player with a CircuitPlayer but whose TournamentPlayer is deliberately
        not linked to it must be excluded from the percentile calculation for that
        tournament, and must not inflate other players' percentiles."""
        t = self._new_tournament('Unlinked TP tournament')
        circuit = Circuit.objects.create(name='Unlinked TP circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.tournaments.add(t)

        # p1 score=20 (excluded), p2 score=10 (included), p3 score=5 (included)
        tp1 = t.tournamentplayer_set.create(player=self.p1, score=20.0)
        tp2 = t.tournamentplayer_set.create(player=self.p2, score=10.0)
        tp3 = t.tournamentplayer_set.create(player=self.p3, score=5.0)

        # p1 has a CircuitPlayer but tp1 is intentionally NOT linked to it
        CircuitPlayer.objects.create(player=self.p1, circuit=circuit)
        cp2 = CircuitPlayer.objects.create(player=self.p2, circuit=circuit)
        cp2.tournamentplayers.add(tp2)
        cp3 = CircuitPlayer.objects.create(player=self.p3, circuit=circuit)
        cp3.tournamentplayers.add(tp3)

        circuit.update_scores()

        # Only p2 and p3 participate in the percentile. With 2 players:
        #   p3 percentile = 0/2 = 0.0, p2 percentile = 1/2 = 0.5
        # If p1 were wrongly included the denominator would be 3, giving p2 = 1/3.
        cp2.refresh_from_db()
        cp3.refresh_from_db()
        self.assertAlmostEqual(cp2.score, 0.5)
        self.assertAlmostEqual(cp3.score, 0.0)

    def test_update_scores_empty_circuit_is_no_op(self):
        circuit = Circuit.objects.create(name='Empty update_scores circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.update_scores()  # must not raise

    def test_update_scores_unchanged_scores_no_db_write(self):
        t = self._new_tournament('Unchanged scores tournament')
        circuit = Circuit.objects.create(name='Unchanged scores circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.tournaments.add(t)
        tp1 = t.tournamentplayer_set.create(player=self.p1, score=10.0)
        tp2 = t.tournamentplayer_set.create(player=self.p2, score=5.0)
        cp1 = CircuitPlayer.objects.create(player=self.p1, circuit=circuit)
        cp1.tournamentplayers.add(tp1)
        cp2 = CircuitPlayer.objects.create(player=self.p2, circuit=circuit)
        cp2.tournamentplayers.add(tp2)
        circuit.update_scores()  # set scores
        with CaptureQueriesContext(connection) as ctx:
            circuit.update_scores()  # scores unchanged — no UPDATE expected
        update_queries = [q for q in ctx.captured_queries
                          if q['sql'].upper().startswith('UPDATE')]
        self.assertEqual(len(update_queries), 0)

    def test_update_scores_query_count_does_not_scale_with_tournament_count(self):
        """update_scores() should use a fixed number of queries regardless of
        how many tournaments or circuit players are involved."""
        def _make_circuit_with_n_tournaments(name, n):
            circuit = Circuit.objects.create(name=name,
                                             start_date=self.today,
                                             end_date=self.today,
                                             scoring_system='Sum best 3 tournament percentiles')
            for i in range(n):
                t = self._new_tournament(f'{name} t{i}')
                tp1 = t.tournamentplayer_set.create(player=self.p1, score=10.0 * (i + 1))
                tp2 = t.tournamentplayer_set.create(player=self.p2, score=5.0 * (i + 1))
                tp3 = t.tournamentplayer_set.create(player=self.p3, score=1.0 * (i + 1))
                circuit.tournaments.add(t)
                # Link TPs to their CircuitPlayers (created by the m2m signal)
                for player, tp in [(self.p1, tp1), (self.p2, tp2), (self.p3, tp3)]:
                    cp = CircuitPlayer.objects.get(circuit=circuit, player=player)
                    cp.tournamentplayers.add(tp)
            return circuit

        small = _make_circuit_with_n_tournaments('Query count small', 2)
        large = _make_circuit_with_n_tournaments('Query count large', 6)

        with CaptureQueriesContext(connection) as small_ctx:
            small.update_scores()
        with CaptureQueriesContext(connection) as large_ctx:
            large.update_scores()

        # Query count must be identical: the optimised implementation fetches
        # all tournaments' TPs in two fixed queries rather than one per tournament.
        self.assertEqual(len(small_ctx), len(large_ctx),
                         msg=f'small={len(small_ctx)} queries, large={len(large_ctx)} queries')

    def test_add_or_update_circuit_players_adds_ranked_only_and_is_idempotent(self):
        t = self._new_tournament('Add CP tournament')
        circuit = Circuit.objects.create(name='CP creation circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.tournaments.add(t)

        ranked_tp = t.tournamentplayer_set.create(player=self.p1, score=10.0, unranked=False)
        t.tournamentplayer_set.create(player=self.p2, score=10.0, unranked=True)

        circuit.add_or_update_circuit_players()
        circuit.add_or_update_circuit_players()

        cps = CircuitPlayer.objects.filter(circuit=circuit)
        self.assertEqual(cps.count(), 1)
        cp = cps.get(player=self.p1)
        self.assertEqual(cp.tournamentplayers.count(), 1)
        self.assertEqual(cp.tournamentplayers.first(), ranked_tp)

    def test_add_or_update_circuit_players_second_run_is_not_more_expensive(self):
        t1 = self._new_tournament('Sync query budget tournament 1')
        t2 = self._new_tournament('Sync query budget tournament 2')
        for idx, player in enumerate([self.p1, self.p2, self.p3], start=1):
            t1.tournamentplayer_set.create(player=player, score=10.0 * idx, unranked=False)
            t2.tournamentplayer_set.create(player=player, score=7.0 * idx, unranked=False)

        circuit = Circuit.objects.create(name='Sync query budget circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.tournaments.add(t1, t2)

        with CaptureQueriesContext(connection) as first_ctx:
            circuit.add_or_update_circuit_players()
        with CaptureQueriesContext(connection) as second_ctx:
            circuit.add_or_update_circuit_players()

        self.assertLessEqual(len(second_ctx), len(first_ctx))

    def test_tournaments_m2m_post_add_triggers_circuitplayer_sync(self):
        t = self._new_tournament('Signal sync tournament')
        ranked_tp = t.tournamentplayer_set.create(player=self.p1, score=7.0, unranked=False)

        circuit = Circuit.objects.create(name='Signal sync circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')

        circuit.tournaments.add(t)

        cp = CircuitPlayer.objects.get(circuit=circuit, player=self.p1)
        self.assertEqual(cp.tournamentplayers.count(), 1)
        self.assertEqual(cp.tournamentplayers.first(), ranked_tp)

    def test_tournaments_m2m_post_remove_prunes_orphaned_circuit_players(self):
        t1 = self._new_tournament('Signal remove tournament 1')
        t2 = self._new_tournament('Signal remove tournament 2')
        tp1 = t1.tournamentplayer_set.create(player=self.p1, score=7.0, unranked=False)
        tp2 = t2.tournamentplayer_set.create(player=self.p1, score=9.0, unranked=False)

        circuit = Circuit.objects.create(name='Signal remove circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')

        circuit.tournaments.add(t1, t2)
        cp = CircuitPlayer.objects.get(circuit=circuit, player=self.p1)
        self.assertEqual(set(cp.tournamentplayers.values_list('id', flat=True)), {tp1.id, tp2.id})

        circuit.tournaments.remove(t2)

        cp.refresh_from_db()
        self.assertEqual(list(cp.tournamentplayers.values_list('id', flat=True)), [tp1.id])

        circuit.tournaments.remove(t1)
        self.assertFalse(CircuitPlayer.objects.filter(circuit=circuit, player=self.p1).exists())

    def test_tournaments_m2m_post_clear_prunes_all_orphaned_circuit_players(self):
        t = self._new_tournament('Signal clear tournament')
        tp = t.tournamentplayer_set.create(player=self.p1, score=7.0, unranked=False)

        circuit = Circuit.objects.create(name='Signal clear circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')

        circuit.tournaments.add(t)
        cp = CircuitPlayer.objects.get(circuit=circuit, player=self.p1)
        self.assertEqual(list(cp.tournamentplayers.values_list('id', flat=True)), [tp.id])

        circuit.tournaments.clear()
        self.assertFalse(CircuitPlayer.objects.filter(circuit=circuit, player=self.p1).exists())

    def test_add_or_update_invalid_scoring_system_does_not_raise(self):
        t = self._new_tournament('Invalid scoring add/update tournament')
        t.tournamentplayer_set.create(player=self.p1, score=7.0, unranked=False)
        circuit = Circuit.objects.create(name='Invalid add/update circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.tournaments.add(t)
        circuit.scoring_system = 'not-a-system'

        circuit.add_or_update_circuit_players()

    def test_remove_orphan_invalid_scoring_system_does_not_raise(self):
        t = self._new_tournament('Invalid scoring remove-orphan tournament')
        t.tournamentplayer_set.create(player=self.p1, score=7.0, unranked=False)
        circuit = Circuit.objects.create(name='Invalid remove-orphan circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.tournaments.add(t)
        circuit.scoring_system = 'not-a-system'

        circuit.remove_orphan_circuit_players()

    def test_tournaments_m2m_reverse_post_add_triggers_circuitplayer_sync(self):
        t = self._new_tournament('Signal reverse add tournament')
        ranked_tp = t.tournamentplayer_set.create(player=self.p1, score=7.0, unranked=False)

        circuit = Circuit.objects.create(name='Signal reverse add circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')

        t.circuit_set.add(circuit)

        cp = CircuitPlayer.objects.get(circuit=circuit, player=self.p1)
        self.assertEqual(cp.tournamentplayers.count(), 1)
        self.assertEqual(cp.tournamentplayers.first(), ranked_tp)

    def test_tournaments_m2m_reverse_post_remove_prunes_circuitplayer_links(self):
        t = self._new_tournament('Signal reverse remove tournament')
        tp = t.tournamentplayer_set.create(player=self.p1, score=7.0, unranked=False)

        circuit = Circuit.objects.create(name='Signal reverse remove circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')

        t.circuit_set.add(circuit)
        cp = CircuitPlayer.objects.get(circuit=circuit, player=self.p1)
        self.assertEqual(list(cp.tournamentplayers.values_list('id', flat=True)), [tp.id])

        t.circuit_set.remove(circuit)
        self.assertFalse(CircuitPlayer.objects.filter(circuit=circuit, player=self.p1).exists())

    def test_tournaments_m2m_reverse_clear_leaves_orphan_circuit_players(self):
        """Tournament.circuit_set.clear() fires reverse post_clear with pk_set=None.
        The signal handler returns early for this case, so CircuitPlayers are not cleaned up."""
        # This behaviour is not great. Test documents it. Ideally we wouldn't leave orphan rows.
        t = self._new_tournament('Reverse clear orphan tournament')
        tp = t.tournamentplayer_set.create(player=self.p1, score=7.0, unranked=False)
        circuit = Circuit.objects.create(name='Reverse clear orphan circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        t.circuit_set.add(circuit)
        self.assertTrue(CircuitPlayer.objects.filter(circuit=circuit, player=self.p1).exists())
        t.circuit_set.clear()
        # Orphan remains: reverse clear is not handled by the signal
        self.assertTrue(CircuitPlayer.objects.filter(circuit=circuit, player=self.p1).exists())

    def test_circuit_urls(self):
        circuit = Circuit.objects.create(name='URL circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles',
                                         wdd_circuit_id=123,
                                         wdr_circuit_id=456)

        self.assertEqual(circuit.wdd_url(),
                         'https://world-diplomacy-database.com/php/results/circuit_class.php?id_circuit=123')
        self.assertEqual(circuit.wdr_url(),
                         'https://www.world-diplomacy-reference.com/tournaments/456')

    def test_circuit_urls_empty_when_ids_missing(self):
        circuit = Circuit.objects.create(name='URL empty circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        self.assertEqual(circuit.wdd_url(), '')
        self.assertEqual(circuit.wdr_url(), '')

    def test_circuit_player_str(self):
        circuit = Circuit.objects.create(name='CP string circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        cp = CircuitPlayer.objects.create(player=self.p1, circuit=circuit)
        self.assertIn(str(self.p1), str(cp))
        self.assertIn(str(circuit), str(cp))

    def test_circuit_player_get_absolute_url(self):
        circuit = Circuit.objects.create(name='CP URL circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        cp = CircuitPlayer.objects.create(player=self.p1, circuit=circuit)
        self.assertEqual(cp.get_absolute_url(),
                         reverse('circuit_player_detail', args=(circuit.id, cp.id)))

    def test_positions_and_scores_assigns_tied_ranks(self):
        circuit = Circuit.objects.create(name='Position tie circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        CircuitPlayer.objects.create(player=self.p1, circuit=circuit, score=9.0)
        CircuitPlayer.objects.create(player=self.p2, circuit=circuit, score=9.0)
        CircuitPlayer.objects.create(player=self.p3, circuit=circuit, score=3.0)

        ranking = circuit.positions_and_scores()

        self.assertEqual(ranking[self.p1], (1, 9.0))
        self.assertEqual(ranking[self.p2], (1, 9.0))
        self.assertEqual(ranking[self.p3], (3, 3.0))

    def test_positions_and_scores_empty_circuit(self):
        circuit = Circuit.objects.create(name='Empty positions circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        self.assertEqual(circuit.positions_and_scores(), {})

    def test_circuit_tracks_tournamentplayer_lifecycle_cleanly(self):
        # Create a circuit and add a tournament before any players are registered.
        t = self._new_tournament('Lifecycle tournament')
        circuit = Circuit.objects.create(name='Lifecycle circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.tournaments.add(t)
        self.assertEqual(CircuitPlayer.objects.filter(circuit=circuit).count(), 0)

        # While the tournament is editable/running, adding players should not sync circuits.
        tp1 = t.tournamentplayer_set.create(player=self.p1, score=10.0)
        tp2 = t.tournamentplayer_set.create(player=self.p2, score=0.0)
        self.assertEqual(CircuitPlayer.objects.filter(circuit=circuit).count(), 0)

        # Completing the tournament should sync CircuitPlayers and circuit scores.
        t.editable = False
        t.save(update_fields=['editable'])

        cp1 = CircuitPlayer.objects.get(circuit=circuit, player=self.p1)
        cp2 = CircuitPlayer.objects.get(circuit=circuit, player=self.p2)
        cp1.refresh_from_db()
        cp2.refresh_from_db()
        self.assertEqual(list(cp1.tournamentplayers.values_list('id', flat=True)), [tp1.id])
        self.assertEqual(list(cp2.tournamentplayers.values_list('id', flat=True)), [tp2.id])
        self.assertEqual(cp1.score, 0.5)
        self.assertEqual(cp2.score, 0.0)

    def test_completion_signal_no_sync_on_create(self):
        """Creating a tournament must not trigger circuit sync even if editable=False."""
        with patch.object(Circuit, 'add_or_update_circuit_players', autospec=True) as mock:
            Tournament.objects.create(name='Created editable false',
                                      start_date=self.today,
                                      end_date=self.today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system='Sum all round scores',
                                      draw_secrecy=DrawSecrecy.SECRET,
                                      editable=False)
        mock.assert_not_called()

    def test_completion_signal_no_sync_when_editable_stays_true(self):
        """Saving a tournament while editable remains True must not trigger circuit sync."""
        t = self._new_tournament('Stays-true tournament')
        circuit = Circuit.objects.create(name='Stays-true circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.tournaments.add(t)
        t.tournamentplayer_set.create(player=self.p1, score=10.0)
        with patch.object(Circuit, 'add_or_update_circuit_players', autospec=True) as mock:
            t.save()  # editable still True
        mock.assert_not_called()

    def test_completion_signal_no_sync_on_second_false_save(self):
        """Re-saving an already-completed tournament must not re-trigger circuit sync."""
        t = self._new_tournament('Already-done tournament')
        circuit = Circuit.objects.create(name='Already-done circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.tournaments.add(t)
        t.tournamentplayer_set.create(player=self.p1, score=10.0)
        t.editable = False
        t.save(update_fields=['editable'])  # first completion — sync fires
        with patch.object(Circuit, 'add_or_update_circuit_players', autospec=True) as mock:
            t.save(update_fields=['editable'])  # editable False→False — no re-sync
        mock.assert_not_called()

    def test_reverse_signal_with_empty_pk_set_returns_early(self):
        circuit = Circuit.objects.create(name='Reverse empty pk_set circuit',
                                         start_date=self.today,
                                         end_date=self.today,
                                         scoring_system='Sum best 3 tournament percentiles')
        _sync_circuit_players_on_tournament_m2m_change(
            sender=Circuit.tournaments.through,
            instance=circuit,
            action='post_remove',
            reverse=True,
            model=Circuit,
            pk_set=set(),
        )

    def test_circuit_series_str(self):
        series = CircuitSeries.objects.create(name='World Circuit',
                                              description='Annual world circuit')
        self.assertEqual(str(series), 'World Circuit')

    def test_circuit_series_get_absolute_url(self):
        series = CircuitSeries.objects.create(name='Euro Circuit',
                                              description='Annual euro circuit')
        self.assertEqual(series.get_absolute_url(),
                         reverse('circuit_series_detail', args=(series.slug,)))

