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
from urllib.parse import urlunparse

import matplotlib.pyplot as plt

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

S1901_dots = {
    'Austria': 3,
    'England': 3,
    'France': 3,
    'Germany': 3,
    'Italy': 3,
    'Russia': 4,
    'Turkey': 3,
}


def _dots(game):
    """Return a dict, keyed by year, of dicts keyed by power of SC counts"""
    retval = {1900: S1901_dots}
    for y in range(1901, game.year+1):
        sc_counts = None
        try:
            sc_counts, _, _, _, _ = game.turn_details(backstabbr.WINTER, y)
        except backstabbr.NoSuchSeason:
            pass
        else:
            retval[y] = sc_counts
            continue
        # If we couldn't read Winter, try the next Spring or Fall
        try:
            sc_counts, _, _, _, _ = game.turn_details(backstabbr.SPRING, y+1)
        except backstabbr.NoSuchSeason:
            pass
        else:
            retval[y] = sc_counts
            continue
        try:
            sc_counts, _, _, _, _ = game.turn_details(backstabbr.FALL, y+1)
        except backstabbr.NoSuchSeason:
            pass
        else:
            retval[y] = sc_counts
    return retval


def graph(request, game_type, game_number):
    """
    Just an SC graph for the specified game, as a PNG image

    game_type should be either 'game' or 'sandbox'
    """
    game_path = f'{game_type}/{game_number}'
    url = urlunparse(('https', backstabbr.BACKSTABBR_NETLOC, game_path, '', '', ''))
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
        years = dots.keys()
        for power in backstabbr.POWERS:
            colour = _power_to_fg[power]
            power_dots = [c[power] for c in dots.values()]
            # X-axis is year, y-axis is SC count. Colour by power
            ax.plot(years, power_dots, label=_(power), color=colour, linewidth=2)
        ax.axis([1900, g.year, 0, 18])
        ax.set_xlabel(_('Year'))
        ax.set_ylabel(_('Centres'))
        ax.legend(loc='upper left')
        fig.suptitle(g.name)
        fig.savefig(f, format='png')
        graphic = f.getvalue()
    response = HttpResponse(graphic, content_type="image/png")
    return response


def game_sc_graph(request, game_number, sandbox):
    """Show a Supply Centre chart for a backstabbr game"""
    if sandbox:
        game_type = 'sandbox'
    else:
        game_type = 'game'
    context = {'game_type': game_type,
               'game_number': str(game_number)}
    return render(request, 'backstabbr/sc_graph.html', context)


def url_form(request):
    """Form to enter the URL of a backstabbr game"""
    form = BackstabbrUrlForm(request.POST or None)
    if form.is_valid():
        url = form.cleaned_data['url']
        # Extract the game number from the URL
        # Note that the form checks for a backstabbr URL
        g = backstabbr.Game(url, skip_read=True)
        # If all went well, redirect
        if g.regular_game:
            return HttpResponseRedirect(reverse('game_sc_graph', args=(g.number,)))
        else:
            return HttpResponseRedirect(reverse('sandbox_sc_graph', args=(g.number,)))
    return render(request,
                  'backstabbr/enter_url.html',
                  {'form': form})
