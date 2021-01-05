# Diplomacy Tournament Visualiser
# Copyright (C) 2020-2021 Chris Brand
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
Tournament Player Views for the Diplomacy Tournament Visualiser.
"""

from django.forms.formsets import formset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext as _

from tournament.email import send_prefs_email
from tournament.forms import PlayerForm
from tournament.models import TournamentPlayer
from tournament.tournament_views import get_visible_tournament_or_404


# Tournament Player views


def index(request, tournament_id):
    """Display a list of registered players for a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    PlayerFormset = formset_factory(PlayerForm,
                                    extra=4)
    formset = PlayerFormset(request.POST or None)
    if request.method == 'POST':
        if t.is_finished() or not t.editable:
            raise Http404
        for k in request.POST.keys():
            # Send preferences email to the specified TournamentPlayer
            if k.startswith('prefs_'):
                # Extract the TournamentPlayer pk from the button name
                pk = int(k[6:])
                tp = TournamentPlayer.objects.get(pk=pk)
                send_prefs_email(tp, force=True)
                break
            # Delete the specified TournamentPlayer
            if k.startswith('unregister_'):
                # Extract the TournamentPlayer pk from the button name
                pk = int(k[11:])
                tp_qs = TournamentPlayer.objects.filter(pk=pk)
                # Also delete any corresponding RoundPlayers
                tp_qs.get().roundplayers().delete()
                tp_qs.delete()
                break
        # Create a TournamentPlayer for each player to register
        if formset.is_valid():
            for form in formset:
                try:
                    player = form.cleaned_data['player']
                except KeyError:
                    # Empty form - nothing to do
                    continue
                tp, created = TournamentPlayer.objects.get_or_create(player=player,
                                                                     tournament=t)
                if not created:
                    # TODO Because we don't pass the modified formset to render(),
                    # this error is never seen.
                    # In practice, though, the player *is* (already) registered...
                    form.add_error('player',
                                   _("Player already registered"))
        # Redirect back here to flush the POST data
        return HttpResponseRedirect(reverse('tournament_players',
                                            args=(tournament_id,)))
    context = {'tournament': t, 'formset': formset}
    return render(request, 'tournament_players/index.html', context)


def detail(request, tournament_id, tp_id):
    """Display details of a single registered player for a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    try:
        tp = t.tournamentplayer_set.get(id=int(tp_id))
    except TournamentPlayer.DoesNotExist:
        raise Http404
    context = {'tournament': t, 'player': tp}
    return render(request, 'tournament_players/detail.html', context)
