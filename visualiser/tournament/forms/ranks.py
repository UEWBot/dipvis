# Diplomacy Tournament Visualiser
# Copyright (C) 2026 Chris Brand
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

"""Forms for setting official tournament and team rank overrides."""

from django import forms

from tournament.models import Team, TournamentPlayer


class RankOverrideForm(forms.ModelForm):
    """Base form displaying calculated rank information beside an override."""

    name = forms.CharField(disabled=True)
    score = forms.FloatField(disabled=True)
    calculated_rank = forms.IntegerField(disabled=True)

    class Meta:
        fields = ('rank_override',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['name'] = self.display_name()
        self.initial['score'] = self.instance.score
        self.initial['calculated_rank'] = self.instance.calculated_rank


class TournamentPlayerRankOverrideForm(RankOverrideForm):
    """Form for setting one TournamentPlayer's official rank override."""

    class Meta(RankOverrideForm.Meta):
        model = TournamentPlayer

    def display_name(self):
        return str(self.instance.player)


class TeamRankOverrideForm(RankOverrideForm):
    """Form for setting one Team's official rank override."""

    class Meta(RankOverrideForm.Meta):
        model = Team

    def display_name(self):
        return self.instance.name