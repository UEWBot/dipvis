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
Backstabbr Forms Tests for the Diplomacy Tournament Visualiser.
"""
from urllib.parse import urlunparse

from django.test import TestCase

from tournament.backstabbr import BACKSTABBR_NETLOC
from tournament.forms import BackstabbrUrlForm


class BackstabbrUrlFormTest(TestCase):
    def test_url_field(self):
        form = BackstabbrUrlForm()
        self.assertIn('url', form.fields)

    def test_invalid_url(self):
        url = 'monkey'
        form = BackstabbrUrlForm(data={'url': url})
        self.assertIs(False, form.is_valid())

    def test_valid_url(self):
        path = 'game/4917371326693376'
        url = urlunparse(('https', BACKSTABBR_NETLOC, path, '', '', ''))
        form = BackstabbrUrlForm(data={'url': url})
        self.assertIs(True, form.is_valid())
        self.assertEqual(form.cleaned_data['url'], url)
