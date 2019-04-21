# Diplomacy Tournament Visualiser
# Copyright (C) 2019 Chris Brand
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

from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS

class WddViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        # Published Tournament so it's visible to all
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=now,
                                          end_date=now,
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=Tournament.SECRET,
                                          is_published=True)

    def test_classification(self):
        response = self.client.get(reverse('csv_classification', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_boards(self):
        response = self.client.get(reverse('csv_boards', args=(self.t.pk,)))
        self.assertEqual(response.status_code, 200)

