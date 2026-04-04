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
Game Ended Forms Tests for the Diplomacy Tournament Visualiser.
"""
from django.test import TestCase

from . import GameEndedForm


class GameEndedFormTest(TestCase):

    def test_is_finished_not_required(self):
        form = GameEndedForm()
        self.assertIs(False, form.fields['is_finished'].required)
