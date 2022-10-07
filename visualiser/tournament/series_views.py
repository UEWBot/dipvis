# Diplomacy Tournament Visualiser
# Copyright (C) 2022 Chris Brand
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
Series Views for the Diplomacy Tournament Visualiser.
"""

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from tournament.models import Series

# Series views

class SeriesIndexView(ListView):
    """Series index"""
    model = Series
    template_name = 'series/index.html'


class SeriesDetailView(DetailView):
    """Series detail"""
    model = Series
    template_name = 'series/detail.html'
