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
Tournament Views for the Diplomacy Tournament Visualiser.
"""

import csv
from io import StringIO

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.forms.formsets import formset_factory
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext as _

from tournament.email import send_prefs_email
from tournament.forms import BasePlayerRoundScoreFormset
from tournament.forms import BasePrefsFormset
from tournament.forms import PlayerForm
from tournament.forms import PlayerRoundScoreForm
from tournament.forms import PrefsForm

from tournament.diplomacy import GameSet
from tournament.models import Tournament, Game
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
from tournament.models import InvalidPreferenceList

# Redirect times are specified in seconds
REFRESH_TIME = 60

# Index of Tournaments

def tournament_index(request):
    """Display a list of tournaments"""
    # We actually retrieve two separate lists, one of all published tournaments (visible to all)
    main_list = Tournament.objects.filter(is_published=True)
    # and a second list of unpublished tournaents visible to the current user
    if request.user.is_superuser:
        # All unpublished tournaments
        unpublished_list = Tournament.objects.filter(is_published=False)
    elif request.user.is_active:
        # All unpublished tournaments where the current user is listed as a manager
        unpublished_list = request.user.tournament_set.filter(is_published=False)
    else:
        # None at all
        unpublished_list = Tournament.objects.none()
    context = {'tournament_list': main_list, 'unpublished_list': unpublished_list}
    return render(request, 'tournaments/index.html', context)

# Tournament views

def get_visible_tournament_or_404(pk, user):
    """
    Get the specified Tournament object, if it exists, and check that it is visible to the user.
    If it doesn't exist or isn't visible, raise Http404.
    """
    t = get_object_or_404(Tournament, pk=pk)
    # Visible to all if published
    if t.is_published:
        return t
    # Also visible if the user is a manager for the tournament
    if user.is_active and t in user.tournament_set.all():
        return t
    # Superusers see all
    if user.is_superuser:
        return t
    # Default to not visible
    raise Http404

def get_modifiable_tournament_or_404(pk, user):
    """
    Get the specified Tournament object, if it exists, and check that it is visible to the user and editable.
    If it doesn't exist or isn't editable, raise Http404.
    """
    t = get_visible_tournament_or_404(pk, user)
    if t.editable:
        return t
    raise Http404

def tournament_simple(request, tournament_id, template):
    """Just render the specified template with the tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    context = {'tournament': t}
    return render(request, 'tournaments/%s.html' % template, context)

def tournament_scores(request,
                      tournament_id,
                      refresh=False,
                      redirect_url_name='tournament_scores_refresh'):
    """Display scores of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    tps = t.tournamentplayer_set.order_by('-score', 'player__last_name', 'player__first_name')
    rds = t.round_set.all()
    rounds = [r.number() for r in rds]
    # Grab the tournament scores and positions and round scores, all "if it ended now"
    t_positions_and_scores, r_scores = t.positions_and_scores()
    # Construct a list of lists with [position, player name, round 1 score, ..., round n score, tournament score]
    scores = []
    for p in tps:
        rs = []
        for r in rds:
            try:
                rs.append('%.2f' % r_scores[r][p.player])
            except KeyError:
                # This player didn't play this round
                rs.append('')
        scores.append(['%d' % t_positions_and_scores[p.player][0]]
                      + ['<a href="%s">%s</a>' % (p.player.get_absolute_url(), p.player)]
                      + rs
                      + ['%.2f' % t_positions_and_scores[p.player][1]])
    # sort rows by position (they'll retain the alphabetic sorting if equal)
    scores.sort(key=lambda row: float(row[0]))
    # After sorting, replace UNRANKED with suitable text
    for row in scores:
        row[0] = row[0].replace('%d' % Tournament.UNRANKED, 'Unranked')
    # Add one final row showing whether each round is ongoing or not
    row = ['', '']
    for r in rds:
        if r.is_finished():
            row.append(_(u'Final'))
        else:
            row.append('')
    if t.is_finished():
        row.append(_(u'Final'))
    else:
        row.append('')
    scores.append(row)
    context = {'tournament': t, 'scores': scores, 'rounds': rounds}
    if refresh:
        context['refresh'] = True
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse(redirect_url_name, args=(tournament_id,))
    return render(request, 'tournaments/scores.html', context)

def tournament_game_results(request,
                            tournament_id,
                            refresh=False,
                            redirect_url_name='tournament_game_results_refresh'):
    """Display the results of all the games of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    tps = t.tournamentplayer_set.order_by('player__last_name', 'player__first_name')
    rds = t.round_set.all()
    rounds = [r.number() for r in rds]
    # Grab the games for each round
    round_games = {}
    for r in rds:
        round_games[r] = r.game_set.all()
    # Construct a list of lists with [player name, round 1 game results, ..., round n game results]
    results = []
    for p in tps:
        # All the games (in every tournament) this player has played in
        gps = p.player.gameplayer_set.all()
        rs = []
        for r in rds:
            gs = ''
            for g in round_games[r]:
                # Is this game one that this player played in?
                try:
                    gp = gps.get(game=g)
                except GamePlayer.DoesNotExist:
                    pass
                else:
                    # New line if they played multiple games in this round
                    if gs:
                        gs += '<br>'
                    # Final CentreCount for this player in this game
                    final_sc = g.centrecount_set.filter(power=gp.power).order_by('-year').first()
                    if final_sc.count == 0:
                        # We need to look back to find the first CentreCount with no dots
                        final_sc = g.centrecount_set.filter(power=gp.power).filter(count=0).order_by('year').first()
                        gs += _('Eliminated as %(power)s in %(year)d') % {'year': final_sc.year,
                                                                          'power': gp.power.name}
                    else:
                        if final_sc.count == 1:
                            centre_str = _('centre')
                        else:
                            centre_str = _('centres')
                        # Final year of the game as a whole
                        final_year = g.centrecount_set.order_by('-year').first().year
                        # Was the game soloed ?
                        soloer = g.soloer()
                        if gp == soloer:
                            gs += _('Solo as %(power)s with %(dots)d %(dot_str)s in %(year)d') % {'year': final_year,
                                                                                                  'power': gp.power.name,
                                                                                                  'dot_str': centre_str,
                                                                                                  'dots': final_sc.count}
                        elif soloer is not None:
                            gs += _('Loss as %(power)s with %(dots)d %(dot_str)s in %(year)d') % {'year': final_sc.year,
                                                                                                  'power': gp.power.name,
                                                                                                  'dot_str': centre_str,
                                                                                                  'dots': final_sc.count}
                        else:
                            # Did a draw vote pass ?
                            res = g.passed_draw()
                            if res:
                                if gp.power in res.powers():
                                    gs += _('%(n)d-way draw as %(power)s with %(dots)d %(dot_str)s in %(year)d') % {'n': res.draw_size(),
                                                                                                                    'power': gp.power.name,
                                                                                                                    'dots': final_sc.count,
                                                                                                                    'dot_str': centre_str,
                                                                                                                    'year': final_year}
                                else:
                                    gs += _('Loss as %(power)s with %(dots)d %(dot_str)s in %(year)d') % {'year': final_sc.year,
                                                                                                          'power': gp.power.name,
                                                                                                          'dot_str': centre_str,
                                                                                                          'dots': final_sc.count}
                            else:
                                # Game is either ongoing or reached a timed end
                                gs += _('%(dots)d %(dot_str)s as %(power)s in %(year)d') % {'year': final_sc.year,
                                                                                            'power': gp.power.name,
                                                                                            'dot_str': centre_str,
                                                                                            'dots': final_sc.count}
                    # game name and link
                    gs += _(' in <a href="%(url)s">%(game)s</a>') % {'game': g.name,
                                                                     'url': g.get_absolute_url()}
                    # Additional info
                    if g.is_top_board:
                        gs += _(' [Top Board]')
                    if not g.is_finished:
                        gs += _(' [Ongoing]')
            rs.append(gs)
        results.append(['<a href=%s>%s</a>' % (p.player.get_absolute_url(), p.player)] + rs)
    # Add one final row showing whether each round is ongoing or not
    row = ['']
    for r in rds:
        if r.is_finished():
            row.append(_(u'Final'))
        else:
            row.append('')
    results.append(row)
    context = {'tournament': t, 'scores': results, 'rounds': rounds}
    if refresh:
        context['refresh'] = True
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse(redirect_url_name, args=(tournament_id,))
    return render(request, 'tournaments/game_results.html', context)

def tournament_best_countries(request,
                              tournament_id,
                              refresh=False,
                              redirect_url_name='tournament_best_countries_refresh'):
    """Display best countries of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    # We're going to need all the scores and URLs for every game in the tournament
    # Best to avoid deriving this information seven times for each game
    all_games = Game.objects.filter(the_round__tournament=t)
    all_urls_and_scores = {}
    for g in all_games:
        all_urls_and_scores[g] = (g.get_absolute_url(), g.name, g.scores())
    # gps is a list of all gameplayers, sorted by current score for each power
    # GamePlayer.score only gets a value when the game has ended
    # so we have to do the sort manually
    gps = list(GamePlayer.objects.filter(game__the_round__tournament=t).distinct())
    gps.sort(key=lambda gp: all_urls_and_scores[gp.game][2][gp.power], reverse=True)
    # Shift any unranked players to the end of the list, regardless of score
    gps.sort(key=lambda gp: t.tournamentplayer_set.get(player=gp.player).unranked)
    # We have to just pick a set here. Avalon Hill is most common in North America
    set_powers = GameSet.objects.get(name='Avalon Hill').setpower_set.order_by('power')
    # TODO Sort set_powers alphabetically by translated power.name
    rows = []
    # Add a row at a time, containing the best remaining result for each power
    while gps:
        row = []
        for p in set_powers:
            # Find the first in gps for this power
            for gp in gps:
                if gp.power == p.power:
                    gps.remove(gp)
                    break
            row.append('<a href="%s">%s</a><br/><a href="%s">%s</a><br/>%f'
                       % (gp.player.get_absolute_url(),
                          gp.player,
                          all_urls_and_scores[gp.game][0], # URL
                          all_urls_and_scores[gp.game][1], # name
                          all_urls_and_scores[gp.game][2][gp.power])) # score
        rows.append(row)
    context = {'tournament': t, 'powers': set_powers, 'rows': rows}
    if refresh:
        context['refresh'] = True
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse(redirect_url_name, args=(tournament_id,))
    return render(request, 'tournaments/best_countries.html', context)

def tournament_background(request, tournament_id, as_ticker=False):
    """Display background info for a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    context = {'tournament': t, 'subject': 'Background', 'content': t.background()}
    if as_ticker:
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse('tournament_ticker',
                                          args=(tournament_id,))
        return render(request, 'tournaments/info_ticker.html', context)
    return render(request, 'tournaments/info.html', context)

def tournament_news(request, tournament_id, as_ticker=False):
    """Display the latest news of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    context = {'tournament': t, 'subject': 'News', 'content': t.news()}
    if as_ticker:
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse('tournament_ticker',
                                          args=(tournament_id,))
        return render(request, 'tournaments/info_ticker.html', context)
    return render(request, 'tournaments/info.html', context)

def tournament_round(request, tournament_id):
    """Display details of the currently in-progress round of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = t.current_round()
    if r:
        context = {'tournament': t, 'round': r}
        return render(request, 'rounds/detail.html', context)
    # TODO There must be a better way than this
    return HttpResponse("No round currently being played")

# TODO Name is confusing - sounds like it takes a round_num
@permission_required('tournament.change_roundplayer')
def round_scores(request, tournament_id):
    """Provide a form to enter each player's score for each round"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    PlayerRoundScoreFormset = formset_factory(PlayerRoundScoreForm,
                                              extra=0,
                                              formset=BasePlayerRoundScoreFormset)
    data = []
    # Go through each player in the Tournament
    for tp in t.tournamentplayer_set.all():
        current = {'tp': tp, 'player': tp.player, 'overall_score': tp.score}
        for rp in tp.roundplayers():
            r = rp.the_round
            round_num = r.number()
            current['round_%d' % round_num] = rp.score
            # Scores for any games in the round
            games = GamePlayer.objects.filter(player=tp.player,
                                              game__the_round=r).distinct()
            current['game_scores_%d' % round_num] = ', '.join([str(g.score) for g in games])
        data.append(current)
    formset = PlayerRoundScoreFormset(request.POST or None,
                                      tournament=t,
                                      initial=data)
    if formset.is_valid():
        for form in formset:
            tp = form.cleaned_data['tp']
            for r_name, value in form.cleaned_data.items():
                # Skip if no score was entered
                if not value:
                    continue
                # We're only interested in the round score fields
                if r_name.startswith('round_'):
                    # Extract the round number from the field name
                    i = int(r_name[6:])
                    # Find that Round
                    r = t.round_numbered(i)
                    # Update the score
                    i = RoundPlayer.objects.get_or_create(player=tp.player,
                                                          the_round=r)[0]
                    i.score = value
                    try:
                        i.full_clean()
                    except ValidationError as e:
                        form.add_error(form.fields[r_name], e)
                        i.delete()
                        return render(request,
                                      'tournaments/round_players.html',
                                      {'title': _('Scores'),
                                       'tournament': t,
                                       'post_url': reverse('enter_scores',
                                                           args=(tournament_id,)),
                                       'formset' : formset})

                    i.save()
                elif r_name == 'overall_score':
                    # Store the player's tournament score
                    tp.score = value
                    try:
                        tp.full_clean()
                    except ValidationError as e:
                        form.add_error(form.fields[r_name], e)
                        return render(request,
                                      'tournaments/round_players.html',
                                      {'title': _('Scores'),
                                       'tournament': t,
                                       'post_url': reverse('enter_scores',
                                                           args=(tournament_id,)),
                                       'formset' : formset})
                    tp.save()
        # Redirect to the read-only version
        return HttpResponseRedirect(reverse('tournament_scores',
                                            args=(tournament_id)))

    return render(request,
                  'tournaments/round_players.html',
                  {'title': _('Scores'),
                   'tournament': t,
                   'post_url': reverse('enter_scores', args=(tournament_id,)),
                   'formset' : formset})

# Note: No permission_required decorator
# because this one should be available to any who have the URL
def player_prefs(request, tournament_id, uuid):
    """
    Display the current preferences for a single TournamentPlayer,
    and give them the ability to change them.
    TournamentPlayer is (indirectly) identified by the uuid string.
    """
    # Note that this effectively means that the URL only works for a published Tournament
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    # Fail if the preferences would be ignored anyway
    r = t.round_set.last()
    if r and r.in_progress():
        raise Http404
    # Find the TournamentPlayer in question
    try:
        tp = t.tournamentplayer_set.get(uuid_str=uuid)
    except TournamentPlayer.DoesNotExist:
        raise Http404
    form = PrefsForm(request.POST or None,
                     tp=tp)
    if form.is_valid() and form.has_changed():
        ps = form.cleaned_data['prefs']
        # Set preferences for this TournamentPlayer
        tp.create_preferences_from_string(ps)
        # Redirect back here to flush the POST data
        return HttpResponseRedirect(reverse('player_prefs',
                                            args=(tournament_id, uuid)))
    return render(request,
                  'tournaments/player_prefs.html',
                  {'tournament': t,
                   'uuid': uuid,
                   'prefs_list': tp.preference_set.all(),
                   'form' : form})

@permission_required('tournament.add_preference')
def enter_prefs(request, tournament_id):
    """Provide a form to enter player country preferences"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    PrefsFormset = formset_factory(PrefsForm,
                                   extra=0,
                                   formset=BasePrefsFormset)
    formset = PrefsFormset(request.POST or None, tournament=t)
    if formset.is_valid():
        for form in formset:
            if form.has_changed():
                tp = form.tp
                ps = form.cleaned_data['prefs']
                # Set preferences for this TournamentPlayer
                tp.create_preferences_from_string(ps)
        # If all went well, re-direct
        return HttpResponseRedirect(reverse('tournament_detail',
                                            args=(tournament_id,)))
    return render(request,
                  'tournaments/enter_prefs.html',
                  {'tournament': t,
                   'formset' : formset})

@permission_required('tournament.add_preference')
def upload_prefs(request, tournament_id):
    """Upload a CSV file to enter player country preferences"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    if request.method == 'GET':
        return render(request,
                      'tournaments/upload_prefs.html',
                      {'tournament':t})
    try:
        csv_file = request.FILES['csv_file']
        if csv_file.multiple_chunks():
            messages.error(request,
                           'Uploaded file is too big (%.2f MB)' % csv_file.size / (1024 * 1024))
            return HttpResponseRedirect(reverse('upload_prefs',
                                                args=(tournament_id,)))
        # TODO How do I know what charset to use?
        fp = StringIO(csv_file.read().decode('utf8'))
        reader = csv.DictReader(fp)
        for row in reader:
            try:
                tp = TournamentPlayer.objects.get(pk=row['Id'])
            except KeyError:
                messages.error(request, 'Failed to find player Id')
                return HttpResponseRedirect(reverse('upload_prefs',
                                                    args=(tournament_id,)))
            p = tp.player
            try:
                if p.first_name != row['First Name']:
                    messages.error(request, "Player first name doesn't match id")
                    return HttpResponseRedirect(reverse('upload_prefs',
                                                        args=(tournament_id,)))
            except KeyError:
                messages.error(request, 'Failed to find player First Name')
                return HttpResponseRedirect(reverse('upload_prefs',
                                                    args=(tournament_id,)))
            try:
                if p.last_name != row['Last Name']:
                    messages.error(request, "Player last name doesn't match id")
                    return HttpResponseRedirect(reverse('upload_prefs',
                                                        args=(tournament_id,)))
            except KeyError:
                messages.error(request, 'Failed to find player Last Name')
                return HttpResponseRedirect(reverse('upload_prefs',
                                                    args=(tournament_id,)))
            # Player data matches, so go ahead and parse the preferences
            try:
                ps = row['Preferences']
            except KeyError:
                messages.error(request, 'Failed to find player Preferences')
                return HttpResponseRedirect(reverse('upload_prefs',
                                                    args=(tournament_id,)))
            try:
                tp.create_preferences_from_string(ps)
            except InvalidPreferenceList:
                messages.error(request, 'Invalid preference string %s' % ps)
                return HttpResponseRedirect(reverse('upload_prefs',
                                                    args=(tournament_id,)))
    except Exception as e:
        messages.error(request, 'Unable to upload file: ' + repr(e))

    return HttpResponseRedirect(reverse('enter_prefs',
                                        args=(tournament_id,)))

def prefs_csv(request, tournament_id):
    """Download a template CSV file to enter player country preferences"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    # Want the default player order
    tps = t.tournamentplayer_set.all()
    # What fields we want to write
    headers = ['Id',
               'First Name',
               'Last Name',
               'Preferences',
              ]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%d_prefs.csv"' % (t.name,
                                                                                  t.start_date.year)

    writer = csv.DictWriter(response, fieldnames=headers)
    writer.writeheader()
    # One row per player (row order and field order don't matter)
    for tp in tps:
        p = tp.player
        row_dict = {'Id': tp.id,
                    'First Name': p.first_name,
                    'Last Name': p.last_name,
                    'Preferences': tp.prefs_string(),
                   }
        # Write this player's row out
        writer.writerow(row_dict)

    return response

def tournament_players(request, tournament_id):
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
                else:
                    tp.save()
        # Redirect back here to flush the POST data
        return HttpResponseRedirect(reverse('tournament_players',
                                            args=(tournament_id,)))
    context = {'tournament': t, 'formset': formset}
    return render(request, 'tournaments/tournament_players.html', context)

def round_index(request, tournament_id):
    """Display a list of rounds of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    the_list = t.round_set.all()
    context = {'tournament': t, 'round_list': the_list}
    return render(request, 'rounds/index.html', context)
