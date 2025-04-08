# Copyright 2025 Chris Brand
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
Show info about a Diplomacy game on Backstabbr.com.
"""

import io
import matplotlib.pyplot as plt
from urllib.parse import urlunparse

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _

from tournament import backstabbr
from tournament.forms import BackstabbrUrlForm


_power_to_fg = {
    'Austria': 'red',
    'England': 'blue',
    'France':  'cyan',
    'Germany': 'black',
    'Italy':   'green',
    'Russia':  'grey',
    'Turkey':  'yellow',
}

def _dots(game):
    """Return a dict, keyed by power, of lists of SC counts for the specified power"""
    retval = {}
    sc_counts, _, _, _, _ = game.turn_details(backstabbr.SPRING, 1901)
    for power in backstabbr.POWERS:
        retval[power] = [sc_counts[power]]
    for y in range(1901, game.year):
        sc_counts, _, _, _, _ = game.turn_details(backstabbr.WINTER, y)
        for power in backstabbr.POWERS:
            retval[power].append(sc_counts[power])
    return retval

def graph(request, game_number):
    """Just an SC graph for the specified game, as a PNG image"""
    # TODO Ideally, we'd support sandoxes as well as games
    url = urlunparse(('https', backstabbr.BACKSTABBR_NETLOC, f'game/{game_number}', '', '', ''))
    try:
        g = backstabbr.Game(url)
    except backstabbr.InvalidGameUrl as e:
        raise Http404 from e

    # Read the game history
    dots = _dots(g)

    # TODO lots of overlap here with game_views.graph()
    with io.BytesIO() as f:
        # plot the SC counts
        fig, ax = plt.subplots()
        years = range(1900, g.year)
        for power in backstabbr.POWERS:
            colour = _power_to_fg[power]
            # X-axis is year, y-axis is SC count. Colour by power
            ax.plot(years, dots[power], label=_(power), color=colour, linewidth=2)
        ax.axis([1900, g.year, 0, 18])
        ax.set_xlabel(_('Year'))
        ax.set_ylabel(_('Centres'))
        ax.legend(loc='upper left')
        fig.suptitle(g.name)
        fig.savefig(f, format='png')
        graphic = f.getvalue()
    response = HttpResponse(graphic, content_type="image/png")
    return response

def game_sc_graph(request, game_number):
    """Show a Supply Centre chart for a backstabbr game"""
    context = {'game_number': str(game_number)}
    return render(request, 'backstabbr/sc_graph.html', context)

def url_form(request):
    """Form to enter the URL of a backstabbr game"""
    form = BackstabbrUrlForm(request.POST or None)
    if form.is_valid():
        url = form.cleaned_data['url']
        # extract the game number from the URL
        # Note that the form checks for a backstabbr URL
        g = backstabbr.Game(url, skip_read=True)
        game_num = g.number
        # If all went well, redirect
        return HttpResponseRedirect(reverse('game_sc_graph', args=(game_num,)))
    return render(request,
                  'backstabbr/enter_url.html',
                  {'form': form})
