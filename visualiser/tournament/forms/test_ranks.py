# Diplomacy Tournament Visualiser
# Copyright (C) 2026 Chris Brand
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

"""Rank override form tests for the Diplomacy Tournament Visualiser."""
from datetime import date, timedelta

from django.test import TestCase

from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Team, Tournament,
                               TournamentPlayer)
from tournament.players import Player

from . import TeamRankOverrideForm, TournamentPlayerRankOverrideForm


class RankOverrideFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = date.today()
        cls.tournament = Tournament.objects.create(
            name='Rank form tournament',
            start_date=today,
            end_date=today + timedelta(hours=24),
            round_scoring_system=R_SCORING_SYSTEMS[0].name,
            tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
            draw_secrecy=DrawSecrecy.SECRET,
            team_size=2,
        )
        cls.player = Player.objects.create(first_name='Arthur', last_name='Bottom')
        cls.tournament_player = TournamentPlayer.objects.create(
            player=cls.player,
            tournament=cls.tournament,
            score=42.5,
            calculated_rank=3,
        )
        cls.team = Team.objects.create(
            tournament=cls.tournament,
            name='The Team',
            score=84.0,
            calculated_rank=2,
        )

    def test_tournament_player_form_displays_calculated_values(self):
        form = TournamentPlayerRankOverrideForm(instance=self.tournament_player)
        self.assertEqual(form['name'].initial, 'Arthur Bottom')
        self.assertEqual(form['score'].initial, 42.5)
        self.assertEqual(form['calculated_rank'].initial, 3)
        self.assertTrue(form.fields['name'].disabled)
        self.assertTrue(form.fields['score'].disabled)
        self.assertTrue(form.fields['calculated_rank'].disabled)

    def test_tournament_player_form_saves_and_clears_override(self):
        form = TournamentPlayerRankOverrideForm(instance=self.tournament_player,
                                                 data={'rank_override': '1'})
        self.assertTrue(form.is_valid())
        form.save()
        self.tournament_player.refresh_from_db()
        self.assertEqual(self.tournament_player.rank_override, 1)

        form = TournamentPlayerRankOverrideForm(instance=self.tournament_player,
                                                 data={'rank_override': ''})
        self.assertTrue(form.is_valid())
        form.save()
        self.tournament_player.refresh_from_db()
        self.assertIsNone(self.tournament_player.rank_override)

    def test_team_form_displays_calculated_values(self):
        form = TeamRankOverrideForm(instance=self.team)
        self.assertEqual(form['name'].initial, 'The Team')
        self.assertEqual(form['score'].initial, 84.0)
        self.assertEqual(form['calculated_rank'].initial, 2)
        self.assertTrue(form.fields['name'].disabled)
        self.assertTrue(form.fields['score'].disabled)
        self.assertTrue(form.fields['calculated_rank'].disabled)

    def test_team_form_allows_tied_and_gapped_overrides(self):
        other = Team.objects.create(tournament=self.tournament,
                                    name='Other Team',
                                    calculated_rank=1)
        form = TeamRankOverrideForm(instance=self.team, data={'rank_override': '1'})
        other_form = TeamRankOverrideForm(instance=other, data={'rank_override': '4'})
        self.assertTrue(form.is_valid())
        self.assertTrue(other_form.is_valid())
        form.save()
        other_form.save()
        self.team.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(self.team.rank_override, 1)
        self.assertEqual(other.rank_override, 4)
