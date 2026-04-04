# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2026 Chris Brand
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
Forms for Backstabbr in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.utils.translation import gettext as _

from tournament import backstabbr


class BackstabbrUrlForm(forms.Form):
    """Form to provide a backstabbr game URL"""
    url = forms.URLField(label=_('Backstabbr Game URL'))

    def clean_url(self):
        url = self.cleaned_data['url']
        # Check that it seems to be a backstabbr game
        try:
            backstabbr.Game(url, skip_read=True)
        except backstabbr.InvalidGameUrl as e:
            raise forms.ValidationError(_('Not a valid backstabbr game URL')) from e
        return url
