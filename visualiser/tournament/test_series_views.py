# Diplomacy Tournament Visualiser
# Copyright (C) 2022 Chris Brand
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

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import DrawSecrecy
from tournament.models import Series, Tournament

class SeriesViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # A Tournament
        now = timezone.now()
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET)
        # And a series it belongs to
        cls.s1 = Series.objects.create(name='Test series')
        cls.s1.tournaments.add(cls.t1)

        # A pk that doesn't correspond to a Series
        cls.INVALID_S_SLUG = 'non_existent_series'


    def test_index(self):
        response = self.client.get(reverse('series_index'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_detail_invalid_series(self):
        response = self.client.get(reverse('series_detail',
                                           args=(self.INVALID_S_SLUG,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_detail(self):
        # Don't have to be logged in to see a series
        response = self.client.get(reverse('series_detail',
                                           args=(self.s1.slug,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    # TODO Improve testing (like actully add TournamentPlayers)
    def test_players(self):
        # Don't have to be logged in to see a series
        response = self.client.get(reverse('series_players',
                                           args=(self.s1.slug,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
