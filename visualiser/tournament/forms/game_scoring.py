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
Forms for game scoring in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.utils.translation import gettext as _

from tournament.diplomacy import GreatPower
from tournament.models import Game


class GameScoreForm(forms.Form):
    """Form for score for a single game"""
    name = forms.CharField(label=_(u'Game Name'),
                           max_length=Game.MAX_NAME_LENGTH,
                           disabled=True,
                           widget=forms.TextInput(attrs={'size': f'{Game.MAX_NAME_LENGTH}'}))

    def __init__(self, *args, **kwargs):
        """Dynamically creates one score field per Great Power"""
        super().__init__(*args, **kwargs)

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            # Don't require a score for every player
            self.fields[c] = forms.FloatField(label=_(c),
                                              required=False,
                                              widget=forms.TextInput(attrs={'size': '10',
                                                                            'maxlength': '10'}))
