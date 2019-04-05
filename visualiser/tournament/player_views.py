# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2019 Chris Brand
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
Player Views for the Diplomacy Tournament Visualiser.
"""

from django.views import generic

from tournament.players import Player

# Player views

class PlayerIndexView(generic.ListView):
    """Player index"""
    model = Player
    paginate_by = 25
    template_name = 'players/index.html'
    context_object_name = 'player_list'

class PlayerDetailView(generic.DetailView):
    """Details of a single player"""
    model = Player
    template_name = 'players/detail.html'
