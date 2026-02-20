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

from django.shortcuts import get_object_or_404, render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from tournament.models import Formats, Series, TournamentPlayer
from tournament.players import Player
from tournament.tournament_views import tournament_is_visible


class SeriesIndexView(ListView):
    """Series index"""
    model = Series
    template_name = 'series/index.html'


class SeriesDetailView(DetailView):
    """Series detail"""
    model = Series
    template_name = 'series/detail.html'


def series_players(request, slug, include_ftf=True, include_vftf=True):
    """Show all the registered players of all the tournaments in the series"""
    assert include_vftf or include_ftf
    s = get_object_or_404(Series, slug=slug)
    qs = s.tournaments.all()
    # If the series contains both FTF and vFTF events,
    # let the user pick a subset of interest
    show_filter = qs.filter(format=Formats.FTF).count() and qs.filter(format=Formats.VFTF).count()
    if not include_ftf:
        qs = qs.exclude(format=Formats.FTF)
    if not include_vftf:
        qs = qs.exclude(format=Formats.VFTF)
    # Only show tournaments the user should be able to see
    t_list = list(filter(lambda t: tournament_is_visible(t, request.user),
                         qs.order_by('start_date')))
    tp_list = TournamentPlayer.objects.filter(tournament__in=t_list)
    p_list = Player.objects.filter(tournamentplayer__in=tp_list).distinct()
    context = {'series': s,
               'show_filter': show_filter,
               'include_ftf': include_ftf,
               'include_vftf': include_vftf,
               'tournaments': t_list,
               'players': p_list,
               'tplayers': tp_list}
    return render(request, 'series/players.html', context)
