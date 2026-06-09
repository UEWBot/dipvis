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
Forms for handicaps in the Diplomacy Tournament Visualiser.
"""

from django import forms

from tournament.models import TournamentPlayer


class HandicapForm(forms.ModelForm):
    """ModelForm for setting one TournamentPlayer's handicap."""

    class Meta:
        model = TournamentPlayer
        fields = ('handicap',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['handicap'].label = str(self.instance.player)
        # Keep legacy presentation used by templates/tests.
        self.fields['handicap'].help_text = ''
