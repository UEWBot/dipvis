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

import csv
from io import StringIO

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone as django_timezone
from django.views import generic

from tournament.forms import PlayerForm
from tournament.players import Player, PlayerGameResult, add_player_bg
from tournament.wdd import validate_wdd_player_id

# Player views


class PlayerIndexView(generic.ListView):
    """Player index"""
    model = Player
    paginate_by = 25
    template_name = 'players/index.html'
    context_object_name = 'player_list'


def player_detail(request, pk):
    """Details of a single player"""
    player = get_object_or_404(Player, pk=pk)
    form = PlayerForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid() and 'versus' in request.POST.keys():
            opponent = form.cleaned_data['player']
            return HttpResponseRedirect(reverse('player_versus',
                                                args=(pk, opponent.pk)))
        else:
            # Technically, we should check permissions here,
            # but the impact of not doing so is minor
            add_player_bg(player, include_wpe=True)
            # Redirect back here to flush the POST data
            return HttpResponseRedirect(reverse('player_detail',
                                                args=(pk,)))
    return render(request,
                  'players/detail.html',
                  {'player': player,
                   'form': form})


def player_versus(request, pk1, pk2):
    """History between two players"""
    p1 = get_object_or_404(Player, pk=pk1)
    p2 = get_object_or_404(Player, pk=pk2)

    # Find all the common games
    matches = []
    r1 = None
    for r in PlayerGameResult.objects.filter(player__in=[p1, p2]).order_by('-date',
                                                                           'tournament_name',
                                                                           'round_number',
                                                                           'game_number'):
        if r1 and r1.for_same_game(r):
            if r.player == p1:
                matches.append((r, r1))
            else:
                matches.append((r1, r))
        r1 = r

    return render(request,
                  'players/versus.html',
                  {'player1': p1,
                   'player2': p2,
                   'matches': matches})


def wpe(request, pk, years=7, count=7):
    """
    World Performance Evaluation details for a single player.

    Displays the best <count> WPE numbers from the previous <years> years.
    """
    player = get_object_or_404(Player, pk=pk)
    now = django_timezone.now()
    start_date = now.replace(year=now.year - years)
    # TODO If I append [:count] here, the template doesn't work properly
    rankings = player.playertournamentranking_set.filter(date__gte=start_date).order_by('-wpe_score')
    return render(request,
                  'players/wpe.html',
                  {'start_date': start_date,
                   'player': player,
                   'rankings': rankings})


@permission_required('tournament.add_player')
def upload_players(request):
    """Upload a CSV file to add Players"""
    if request.method == 'GET':
        return render(request,
                      'players/upload_players.html')

    count = 0
    try:
        csv_file = request.FILES['csv_file']
        if csv_file.multiple_chunks():
            messages.error(request,
                           f'Uploaded file is too big ({csv_file.size / (1024 * 1024):.2f} MB)')
            return HttpResponseRedirect(reverse('upload_players'))
        # TODO How do I know what charset to use?
        fp = StringIO(csv_file.read().decode('utf8'))
        reader = csv.DictReader(fp)
        for row in reader:
            try:
                first_name = row['First Name'].strip()
            except KeyError:
                messages.error(request, 'Failed to find column First Name')
                return HttpResponseRedirect(reverse('upload_players'))

            try:
                last_name = row['Last Name'].strip()
            except KeyError:
                messages.error(request, 'Failed to find column Last Name')
                return HttpResponseRedirect(reverse('upload_players'))

            # All the other columns are optional
            try:
                email = row['Email Address'].strip()
            except KeyError:
                email = ''
            else:
                if len(email) > 0:
                    try:
                        validate_email(email)
                    except ValidationError:
                        messages.warning(request, f'Email address for {first_name} {last_name} is invalid - ignored')
                        email = ''

            try:
                bs_un = row['Backstabbr Username'].strip()
            except KeyError:
                bs_un = None

            # Accept either WDD Id or WDD URL
            # If we have a valid WDD Id, ignore WDD URL
            try:
                wdd_id = row['WDD Id'].strip()
            except KeyError:
                wdd_id = None
            else:
                try:
                    wdd_id = int(wdd_id)
                except ValueError:
                    if len(wdd_id):
                        messages.warning(request, f'WDD Id for {first_name} {last_name} is invalid - ignored')
                    wdd_id = None
                else:
                    try:
                        validate_wdd_player_id(wdd_id)
                    except ValidationError:
                        messages.warning(request, f'WDD Id for {first_name} {last_name} is invalid - ignored')
                        wdd_id = None

            if wdd_id is None:
                try:
                    wdd_url = row['WDD URL'].strip()
                except KeyError:
                    wdd_url = None
                else:
                    if len(wdd_url) > 0:
                        wdd_id = int(wdd_url.rpartition('id_player=')[-1])
                        try:
                            validate_wdd_player_id(wdd_id)
                        except ValidationError:
                            messages.warning(request, f'WDD URL for {first_name} {last_name} is invalid - ignored')
                            wdd_id = None

            # Add the Player
            p, created = Player.objects.update_or_create(first_name=first_name,
                                                         last_name=last_name,
                                                         defaults={'email': email,
                                                                   'backstabbr_username': bs_un})
            if wdd_id:
                WDDPlayer.get_or_create(wdd_player_id=wdd_id, player=p)
            if created:
                messages.info(request, f'Player {first_name} {last_name} added')
                count += 1
            else:
                # Add missing info and flag mismatches
                new_info = []
                fields = []
                if len(email) > 0:
                    if len(p.email) > 0:
                        if p.email != email:
                            messages.warning(request, f'Player {first_name} {last_name} already exists with a different email address')
                    else:
                        # Add the email address
                        p.email = email
                        new_info.append('email address')
                        fields.append('email')
                if bs_un is not None and len(bs_un) > 0:
                    if len(p.backstabbr_username) > 0:
                        if p.backstabbr_username != bs_un:
                            messages.warning(request, f'Player {first_name} {last_name} already exists with a different Backstabbr username')
                    else:
                        # Add the username
                        p.backstabbr_username = bs_un
                        new_info.append('Backstabbr username')
                        fields.append('backstabbr_username')
                if len(new_info):
                    p.save(update_fields=fields)
                    messages.info(request, f'Player {first_name} {last_name} already exists - added {", ".join(new_info)}')
                else:
                    messages.info(request, f'Player {first_name} {last_name} already exists - skipped')

    except Exception as e:
        messages.error(request, 'Unable to upload file: ' + repr(e))

    messages.success(request, f'Added {count} player(s)')

    return HttpResponseRedirect(reverse('upload_players'))
