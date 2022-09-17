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

from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.forms.formsets import formset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _

from tournament.diplomacy.models.great_power import GreatPower
from tournament.email import send_prefs_email
from tournament.forms import AuctionBidForm
from tournament.forms import PlayerForm
from tournament.forms import PrefsForm
from tournament.models import PowerBid, Tournament, TournamentPlayer
from tournament.tournament_views import get_visible_tournament_or_404


# Tournament Player views


def index(request, tournament_id):
    """Display a list of registered players for a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)

    # Non-managers just get a simple list of players
    if not (t.editable and request.user.has_perm('tournament.delete_tournamentplayer')):
        context = {'tournament': t}
        return render(request, 'tournament_players/index.html', context)

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
                # Can't use QuerySet.delete() after distinct()
                for rp in tp_qs.get().roundplayers():
                    rp.delete()
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
    return render(request, 'tournament_players/index_form.html', context)


def detail(request, tournament_id, tp_id):
    """Display details of a single registered player for a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    try:
        tp = t.tournamentplayer_set.get(id=int(tp_id))
    except TournamentPlayer.DoesNotExist as e:
        raise Http404 from e
    context = {'tournament': t, 'player': tp}
    return render(request, 'tournament_players/detail.html', context)


# Note: No permission_required decorator
# because this one should be available to any who have the URL
def player_prefs(request, tournament_id, uuid):
    """
    Display the current preferences for a single TournamentPlayer,
    and give them the ability to change them.
    TournamentPlayer is (indirectly) identified by the uuid string.
    """
    # Allow access regardless of published state
    t = get_object_or_404(Tournament, pk=tournament_id)
    # But don't allow modification of archived tournaments
    if not t.editable:
        raise Http404
    # Fail if the last round already has Games (too late)
    r = t.round_set.last()
    if r and r.game_set.exists():
        raise Http404
    # Find the TournamentPlayer in question
    try:
        tp = t.tournamentplayer_set.get(uuid_str=uuid)
    except TournamentPlayer.DoesNotExist as e:
        raise Http404 from e

    prefs_form = PrefsForm(request.POST or None,
                           tp=tp)

    if prefs_form.is_valid() and prefs_form.has_changed():
        ps = prefs_form.cleaned_data['prefs']
        # Set preferences for this TournamentPlayer
        tp.create_preferences_from_string(ps)

        # Redirect back here to flush the POST data
        return HttpResponseRedirect(reverse('player_prefs',
                                            args=(tournament_id, uuid)))

    return render(request,
                  'tournaments/player_entry.html',
                  {'tournament': t,
                   'uuid': uuid,
                   'prefs_list': tp.preference_set.all(),
                   'form': prefs_form})


# Note: No permission_required decorator
# because this one should be available to any who have the URL
def auction_bids(request, tournament_id, uuid):
    """
    Display the current bids for a single TournamentPlayer,
    and give them the ability to change them.
    TournamentPlayer is (indirectly) identified by the uuid string.
    """
    # Allow access regardless of published state
    t = get_object_or_404(Tournament, pk=tournament_id)
    # But don't allow modification of archived tournaments
    if not t.editable:
        raise Http404
    # Find the first round without Games
    all_rounds_qs = t.round_set.all()
    for_round = None
    for r in all_rounds_qs:
        if not r.game_set.exists():
            for_round = r
            break;
    # Fail if the last round already has Games (too late)
    if for_round is None:
        raise Http404
    # Find the TournamentPlayer in question
    try:
        tp = t.tournamentplayer_set.get(uuid_str=uuid)
    except TournamentPlayer.DoesNotExist as e:
        raise Http404 from e

    # Find any existing bids
    data = {}
    tp_bids_qs = tp.powerbid_set.all()
    for power in GreatPower.objects.all():
        try:
            bid = tp_bids_qs.get(power=power, the_round=for_round)
        except PowerBid.DoesNotExist:
            pass
        else:
            data[_(power.name)] = bid.bid

    # Which style of auction is it?
    if t.power_assignment == t.AUCTION_PER_ROUND:
        funds = PowerBid.BID_TOTAL_PER_ROUND
    elif t.power_assignment == t.AUCTION_TOTAL:
        # How much do they get in total?
        total_rounds = len(all_rounds_qs)
        funds = PowerBid.BID_TOTAL_PER_ROUND * total_rounds
        print('Initial total funds is %d' % funds)
        # How much did they spend in previous rounds ?
        for r in all_rounds_qs:
            # Stop when we get to the round we're bidding for
            if r is for_round:
                break;
            spent = tp_bids_qs.filter(the_round=r).aggregate(Sum('bid'))['bid__sum']
            if spent is not None:
                funds -= spent
            print('Minus spend in %s leaves %d' % (str(r), funds))
        # And how much do they need to save for future rounds?
        # TODO "21" should be derived from the number of GreatPowers
        funds -= (21 * (total_rounds - for_round.number()))
        print('Minus 21 per future round leaves %d' % funds)

    bids_form = AuctionBidForm(request.POST or None,
                               funds=funds,
                               initial=data)

    if bids_form.is_valid() and bids_form.has_changed():
        with transaction.atomic():
            for power in GreatPower.objects.all():
                bid = bids_form.cleaned_data[_(power.name)]

                PowerBid.objects.update_or_create(player=tp,
                                                  power=power,
                                                  the_round=for_round,
                                                  defaults={'bid': bid})

        # Redirect back here to flush the POST data
        return HttpResponseRedirect(reverse('auction_bids',
                                            args=(tournament_id, uuid)))

    return render(request,
                  'tournaments/auction_bids.html',
                  {'tournament': t,
                   'player': tp,
                   'uuid': uuid,
                   'round_num': for_round.number(),
                   'min_bid': PowerBid.MIN_BID,
                   'max_bid': PowerBid.MAX_BID,
                   'bid_total': funds,
                   'form': bids_form})
