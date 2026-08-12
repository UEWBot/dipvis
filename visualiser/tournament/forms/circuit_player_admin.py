# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016 Chris Brand
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

from django import forms

from tournament.circuits import CircuitPlayer
from tournament.models import TournamentPlayer


class CircuitPlayerAdminForm(forms.ModelForm):
    class Meta:
        model = CircuitPlayer
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        """Restrict tournamentplayers queryset to matching player and tournaments"""
        super().__init__(*args, **kwargs)
        qs = TournamentPlayer.objects.all()
        player_id = self.instance.player_id
        if player_id:
            qs = qs.filter(player_id=player_id)
        circuit_id = self.instance.circuit_id
        if circuit_id:
            qs = qs.filter(tournament__in=self.instance.circuit.tournaments.all())
        self.fields['tournamentplayers'].queryset = qs
