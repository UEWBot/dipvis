# Diplomacy Tournament Visualiser
# Copyright (C) 2023 Chris Brand
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

from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone

from django.test import TestCase
from django.urls import reverse

import tournament

from tournament.models import G_SCORING_SYSTEMS, R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import DrawSecrecy, Round, Tournament

class ViewIndexTests(TestCase):
    """Test the various index views with no objects of that type"""

    def test_series_index(self):
        response = self.client.get(reverse('series_index'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_index(self):
        response = self.client.get(reverse('index'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_tournamentplayer_index(self):
        today = date.today()
        t = Tournament.objects.create(name='A Tournament',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET,
                                      is_published=True)
        response = self.client.get(reverse('tournament_players',
                                           args=(t.id,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_round_index(self):
        today = date.today()
        t = Tournament.objects.create(name='A Tournament',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET,
                                      is_published=True)
        response = self.client.get(reverse('round_index',
                                           args=(t.id,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_game_index(self):
        today = date.today()
        t = Tournament.objects.create(name='A Tournament',
                                      start_date=today,
                                      end_date=today + timedelta(hours=24),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET,
                                      is_published=True)
        Round.objects.create(tournament=t,
                             scoring_system=G_SCORING_SYSTEMS[0].name,
                             dias=False,
                             start=datetime.combine(t.start_date, time(hour=8, tzinfo=datetime_timezone.utc)))
        response = self.client.get(reverse('game_index',
                                           args=(t.id, 1)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_player_index(self):
        response = self.client.get(reverse('player_index'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
