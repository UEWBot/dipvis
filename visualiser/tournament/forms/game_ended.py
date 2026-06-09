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
Forms for game ending in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.utils.translation import gettext as _

from tournament.models import Game


class GameEndedForm(forms.ModelForm):
    """ModelForm that provides a checkbox to indicate that a Game is over."""

    class Meta:
        model = Game
        fields = ('is_finished',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_finished'].label = _('Game ended')
        self.fields['is_finished'].required = False
