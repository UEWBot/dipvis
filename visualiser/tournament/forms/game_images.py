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
Forms for game images in the Diplomacy Tournament Visualiser.
"""

from django import forms

from tournament.models import Game, GameImage


class GameImageForm(forms.ModelForm):
    """Form for a single GameImage"""
    class Meta:
        model = GameImage
        fields = ('game', 'year', 'season', 'phase', 'image')

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        tournament = kwargs.pop('tournament')
        super().__init__(*args, **kwargs)
        self.fields['game'].queryset = Game.objects.filter(the_round__tournament=tournament).distinct()
