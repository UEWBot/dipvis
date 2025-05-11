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
from django.db import transaction
from django.forms.formsets import formset_factory
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext as _
from django.urls import reverse

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower

from tournament.email import send_roll_call_emails

from tournament.forms import AwardForm
from tournament.forms import BaseAwardsFormset
from tournament.forms import BaseHandicapsFormset
from tournament.forms import BasePlayerRoundScoreFormset
from tournament.forms import BasePrefsFormset
from tournament.forms import BaseTeamsFormset
from tournament.forms import EnableCheckInForm
from tournament.forms import HandicapForm
from tournament.forms import PlayerRoundScoreForm
from tournament.forms import PrefsForm
from tournament.forms import SeederBiasForm
from tournament.forms import TeamForm

from tournament.models import Tournament, SeederBias, Team
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
from tournament.models import InvalidPreferenceList

from tournament.news import news

# Redirect times are specified in seconds
REFRESH_TIME = 60


def tournament_index(request):
    """Display a list of tournaments"""
    # We actually retrieve two separate lists, one of all published tournaments (visible to all)
    finished_list = Tournament.objects.filter(is_published=True, is_finished=False).order_by('end_date')
    unfinished_list = Tournament.objects.filter(is_published=True, is_finished=True).order_by('-start_date')
    main_list = list(finished_list) + list(unfinished_list)
    # and a second list of unpublished tournaments visible to the current user
    if request.user.is_superuser:
        # All unpublished tournaments
        unpublished_list = Tournament.objects.filter(is_published=False).order_by('is_finished', 'end_date')
    elif request.user.is_active:
        # All unpublished tournaments where the current user is listed as a manager
        unpublished_list = request.user.tournament_set.filter(is_published=False).order_by('is_finished', 'end_date')
    else:
        # None at all
        unpublished_list = Tournament.objects.none()
    context = {'tournament_list': main_list, 'unpublished_list': unpublished_list}
    return render(request, 'tournaments/index.html', context)


# Utility functions

def tournament_is_visible(t, user):
    """
    Determine whether the specified user should be allowed to view the tournament
    """
    # Visible to all if published
    if t.is_published:
        return True
    # Also visible if the user is a manager for the tournament
    if user.is_active and t in user.tournament_set.all():
        return True
    # Superusers see all
    if user.is_superuser:
        return True
    # Default to not visible
    return False


def get_visible_tournament_or_404(pk, user):
    """
    Get the specified Tournament object, if it exists and is visible to the user.

    If it doesn't exist or isn't visible, raise Http404.
    """
    t = get_object_or_404(Tournament, pk=pk)
    if tournament_is_visible(t, user):
        return t
    raise Http404


def get_modifiable_tournament_or_404(pk, user):
    """
    Get the specified Tournament object, if it exists, is visible to the user and editable.

    If it doesn't exist or isn't editable, raise Http404.
    """
    t = get_visible_tournament_or_404(pk, user)
    if t.editable:
        return t
    raise Http404


# Tournament views

def tournament_simple(request, tournament_id, template, context={}):
    """Just render the specified template with the tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    context['tournament'] = t
    return render(request, f'tournaments/{template}.html', context)


def tournament_scores(request,
                      tournament_id,
                      refresh=False,
                      redirect_url_name='tournament_scores_refresh'):
    """Display scores of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    tps = t.tournamentplayer_set.order_by('-score',
                                          'player__last_name',
                                          'player__first_name').prefetch_related('player')
    rds = t.round_set.prefetch_related('roundplayer_set')
    if t.show_current_scores:
        # Grab the tournament scores and positions, all "if it ended now"
        t_positions_and_scores = t.positions_and_scores()
    else:
        # Get the scores after the last finished Round, if any
        r = rds.filter(is_finished=True).last()
        if r:
            t_positions_and_scores = t.positions_and_scores(after_round_num=r.number())
        else:
            # After Round 0, everyone had a score of zero
            t_positions_and_scores = t.positions_and_scores(after_round_num=0)
    # Construct a list of dicts with {rank, tournament player, [round 1 player, ..., round n player]}
    scores = []
    for tp in tps:
        rs = []
        for r in rds:
            try:
                rp = r.roundplayer_set.get(player=tp.player)
            except RoundPlayer.DoesNotExist:
                # This player didn't play this round
                rs.append(None)
            else:
                rs.append(rp)
        row = {'rank': f'{t_positions_and_scores[tp.player][0]}',
               'player': tp,
               'rounds': rs}
        scores.append(row)
    # sort rows by position (they'll retain the alphabetic sorting if equal)
    scores.sort(key=lambda row: float(row['rank']))
    # After sorting, replace UNRANKED with suitable text
    for row in scores:
        row['rank'] = row['rank'].replace(f'{Tournament.UNRANKED}', _('Unranked'))
    context = {'tournament': t, 'scores': scores, 'rounds': rds}
    if refresh:
        context['refresh'] = True
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse(redirect_url_name, args=(tournament_id,))
    # Display scores either with round scores or game scores, as appropriate
    if t.tournament_scoring_system_obj().uses_round_scores:
        template = 'tournaments/scores.html'
    else:
        template = 'tournaments/scores_no_round_scores.html'
    return render(request, template, context)


def team_scores(request,
                tournament_id,
                refresh=False,
                redirect_url_name='team_scores_refresh'):
    """Display team scores of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    # If we're showing this as part of the tournament overview,
    # skip it if either there's no team round or the first team round
    # hasn't started
    show_page = True
    if refresh and redirect_url_name != 'team_scores_refresh':
        rds = t.team_rounds()
        # If any team round has finished, show the page
        show_page = rds.filter(is_finished=True).exists()
        # Otherwise, show it if a team round is in progress
        if not show_page:
            for r in rds:
                if r.in_progress():
                    show_page = True
                    break
    elif not t.team_size:
        raise Http404
    if not show_page:
        # Redirect immediately
        return HttpResponseRedirect(reverse(redirect_url_name, args=(tournament_id,)))
    scores = []
    if t.show_current_scores:
        # Grab the team scores and positions, all "if it ended now"
        team_scores = t.team_scores()
    else:
        # Get the scores after the last finished Round, if any
        r = t.round_set.filter(is_finished=True).last()
        if r:
            team_scores = t.team_scores(after_round_num=r.number())
        else:
            # After Round 0, all teams had a score of zero
            team_scores = t.team_scores(after_round_num=0)
    for team, (rank, score) in team_scores.items():
        row = {'rank': rank,
               'team': team,
               'score': score}
        scores.append(row)
    context = {'tournament': t, 'scores': scores}
    if refresh:
        context['refresh'] = True
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse(redirect_url_name, args=(tournament_id,))
    return render(request, 'tournaments/team_scores.html', context)


def tournament_game_results(request,
                            tournament_id,
                            refresh=False,
                            redirect_url_name='tournament_game_results_refresh'):
    """Display the results of all the games of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    tps = t.tournamentplayer_set.order_by('player__last_name', 'player__first_name').prefetch_related('player__gameplayer_set')
    rds = t.round_set.prefetch_related('game_set')
    rounds = [r.number() for r in rds]
    # Grab the games for each round
    round_games = {}
    for r in rds:
        round_games[r] = r.game_set.all()
    # Construct a list of dicts with tournament player and a list of gameplayer sets, one per round
    results = []
    for tp in tps:
        # All the games (in every tournament) this player has played in
        gps = tp.player.gameplayer_set.prefetch_related('game__the_round', 'power')
        # Create a list of GamePlayers, indexed by Round
        rs = []
        for r in rds:
            # Create a list of GamePlayers for this Player and Round
            gs = gps.filter(game__the_round=r).distinct()
            rs.append(gs)
        row = {'tournament_player': tp,
               'rounds': rs}
        results.append(row)
    context = {'tournament': t, 'results': results, 'rounds': rounds}
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
    # gps is a dict, keyed by power, of lists of lists of gameplayers,
    # sorted by best country criterion
    if t.show_current_scores:
        gps = t.best_countries(whole_list=True)
    else:
        # get the best country list for the end of the last finished Round
        r = t.round_set.filter(is_finished=True).last()
        if r:
            gps = t.best_countries(whole_list=True, after_round_num=r.number())
        else:
            gps = t.best_countries(whole_list=True, after_round_num=0)
    # We have to just pick a set here. Avalon Hill is most common in North America
    set_powers = GameSet.objects.get(name='Avalon Hill').setpower_set.order_by('power').prefetch_related('power')
    # How many rows do we need?
    row_count = max((len(l) for l in (gps[power] for power in GreatPower.objects.all())))
    # TODO Sort set_powers alphabetically by translated power.name
    rows = []
    # Add a row at a time, containing the best remaining results for each power
    for i in range(row_count):
        row = []
        for p in set_powers:
            try:
                gp = gps[p.power].pop(0)
            except IndexError:
                gp = []
            row.append(gp)
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
    context = {'tournament': t, 'subject': 'News', 'content': news(t)}
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
            current[f'round_{round_num}'] = rp.score
            # Scores for any games in the round
            games = GamePlayer.objects.filter(player=tp.player,
                                              game__the_round=r).distinct()
            current[f'game_scores_{round_num}'] = ', '.join([str(g.score) for g in games])
        data.append(current)
    formset = PlayerRoundScoreFormset(request.POST or None,
                                      tournament=t,
                                      initial=data)
    if formset.is_valid():
        for form in formset:
            if form.has_changed():
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
                        RoundPlayer.objects.update_or_create(player=tp.player,
                                                             the_round=r,
                                                             defaults={'score': value})
                    elif r_name == 'overall_score':
                        # Store the player's tournament score
                        tp.score = value
                        tp.save(update_fields=['score'])
        # Redirect to the read-only version
        return HttpResponseRedirect(reverse('tournament_scores',
                                            args=(tournament_id,)))

    return render(request,
                  'tournaments/enter_scores.html',
                  {'tournament': t,
                   'formset': formset})


@permission_required('tournament.change_round')
def self_check_in_control(request, tournament_id):
    """Provide a form to control self-check-in for each round"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    round_set = t.round_set.all()
    enable_data = {}
    for r in round_set.all():
        enable_data[f'round_{r.number()}'] = r.enable_check_in
    form = EnableCheckInForm(request.POST or None,
                             tournament=t,
                             initial=enable_data)
    if form.is_valid():
        for r_name, value in form.cleaned_data.items():
            # Extract the round number from the field name
            i = int(r_name[6:])
            # Find that Round
            rd = t.round_numbered(i)
            fields=['enable_check_in']
            if (value is True) and not rd.enable_check_in:
                # send emails if not already sent
                if not rd.email_sent:
                    send_roll_call_emails(i, list(t.tournamentplayer_set.all()))
                    rd.email_sent = True
                    fields.append('email_sent')
            rd.enable_check_in = value
            rd.save(update_fields=fields)
        # Redirect to the roll call page
        return HttpResponseRedirect(reverse('round_roll_call',
                                            args=(tournament_id, t.current_round().number())))

    return render(request,
                  'tournaments/self_check_in_control.html',
                  {'tournament': t,
                   'post_url': request.path_info,
                   'form': form})


@permission_required('tournament.add_preference')
def enter_prefs(request, tournament_id):
    """Provide a form to enter player country preferences"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    if not t.powers_assigned_from_prefs():
        raise Http404
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
                   'formset': formset})


@permission_required('tournament.add_preference')
def upload_prefs(request, tournament_id):
    """Upload a CSV file to enter player country preferences"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    if not t.powers_assigned_from_prefs():
        raise Http404
    if request.method == 'GET':
        return render(request,
                      'tournaments/upload_prefs.html',
                      {'tournament': t})
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
                messages.error(request, f'Invalid preference string {ps}')
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
    response['Content-Disposition'] = f'attachment; filename="{t.name}_{t.start_date.year}_prefs.csv"'

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


@permission_required('tournament.add_seederbias')
def seeder_bias(request, tournament_id):
    """Display or add SeederBias objects for the Tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    sb_set = SeederBias.objects.filter(player1__tournament=t)
    form = SeederBiasForm(request.POST or None,
                          tournament=t)
    if request.method == 'POST':
        if t.is_finished or not t.editable:
            raise Http404
        for k in request.POST.keys():
            if k.startswith('delete_'):
                # Extract the SeederBias pk from the button name
                pk = int(k[7:])
                SeederBias.objects.filter(pk=pk).delete()
                # Redirect back here to flush the POST data
                return HttpResponseRedirect(reverse('seeder_bias',
                                                    args=(tournament_id,)))
        if form.is_valid():
            form.save()
            # Redirect back here to flush the POST data
            return HttpResponseRedirect(reverse('seeder_bias',
                                                args=(tournament_id,)))
    context = {'tournament': t,
               'biases': sb_set,
               'form': form}
    return render(request, 'tournaments/seeder_bias.html', context)


@permission_required('tournament.change_tournamentplayer')
def enter_awards(request, tournament_id):
    """Enter awards for the Tournament"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    AwardsFormset = formset_factory(AwardForm,
                                    extra=0,
                                    formset=BaseAwardsFormset)
    formset = AwardsFormset(request.POST or None, tournament=t)
    if formset.is_valid():
        with transaction.atomic():
            # Delete any existing awards
            for tp in t.tournamentplayer_set.exclude(awards=None).all():
                tp.awards.clear()
                tp.save()
            for form in formset:
                award = form.cleaned_data['award']
                tps = form.cleaned_data['players']
                for tp in tps:
                    tp.awards.add(award)
                    tp.save()
        # Redirect to the read-only version
        return HttpResponseRedirect(reverse('tournament_awards',
                                            args=(tournament_id,)))
    context = {'tournament': t,
               'formset': formset}
    return render(request, 'tournaments/awards_form.html', context)


@permission_required('tournament.change_tournamentplayer')
def enter_handicaps(request, tournament_id):
    """Enter handicaps for the Tournament"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    # Only valid for Tournaments with handicaps
    if not t.handicaps:
        raise Http404
    HandicapsFormset = formset_factory(HandicapForm,
                                       extra=0,
                                       formset=BaseHandicapsFormset)
    formset = HandicapsFormset(request.POST or None, tournament=t)
    if formset.is_valid():
        for form in formset:
            if form.has_changed():
                tp = form.tp
                tp.handicap = form.cleaned_data['handicap']
                tp.save(update_fields=['handicap'])
        # Redirect to the TP index page
        return HttpResponseRedirect(reverse('tournament_players',
                                            args=(tournament_id,)))
    return render(request,
                  'tournaments/enter_handicaps.html',
                  {'tournament': t,
                   'formset': formset})


def teams(request, tournament_id):
    """Show the registered teams"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    if not t.team_size:
        raise Http404
    context = {'tournament': t}
    return render(request, 'tournaments/teams.html', context)


@permission_required('tournament.add_team')
def enter_teams(request, tournament_id):
    """Form to create or edit teams"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    # Only valid for Tournaments with teams
    if not t.team_size:
        raise Http404
    # Calculate a sensible number of teams
    expected_teams = t.tournamentplayer_set.count() // t.team_size
    TeamsFormset = formset_factory(TeamForm,
                                   extra=max(1, expected_teams - t.team_set.count()),
                                   formset=BaseTeamsFormset)
    formset = TeamsFormset(request.POST or None, tournament=t)
    if formset.is_valid():
        for form in formset:
            if form.has_changed():
                tm = form.team
                if tm:
                    tm.name = form.cleaned_data['name']
                    tm.save()
                else:
                    tm = Team.objects.create(tournament=t,
                                             name=form.cleaned_data['name'])
                # Put together a list of players that should be on the team
                players = []
                for r_name, value in form.cleaned_data.items():
                    if r_name.startswith('player_'):
                        players.append(value)
                # Compare against the players currently on the team
                for p in tm.players.all():
                    if p in players:
                        players.remove(p)
                    else:
                        tm.players.remove(p)
                # Add any missing players
                for p in players:
                    tm.players.add(p)
        # Redirect to the teams page
        return HttpResponseRedirect(reverse('teams',
                                            args=(tournament_id,)))
    return render(request,
                  'tournaments/enter_teams.html',
                  {'tournament': t,
                   'formset': formset})


def api(request, tournament_id, version):
    """JSON API to retrieve data"""
    if version != 1:
        raise Http404(f'Invalid API version {version}')
    t = get_visible_tournament_or_404(tournament_id, request.user)
    rounds = {}
    for r in t.round_set.all():
        games = {}
        for g in r.game_set.all():
            players = {}
            for gp in g.gameplayer_set.all():
                players[str(gp.power)] = {'name': str(gp.player),
                                          'location': gp.player.location,
                                          'wdr_id': gp.player.wdr_player_id}
                if gp.score_is_final():
                    players[str(gp.power)]['score'] = gp.score
                    players[str(gp.power)]['final_scs'] = gp.final_sc_count()
            games[g.name] = {'sandbox': g.external_url,
                             'started' : g.started_at,
                             'players': players}
        rounds[r.number()] = {'scoring_system': r.scoring_system,
                              'games': games}
    data = {'name': t.name,
            'year': t.start_date.year,
            'rounds': rounds}
    return JsonResponse(data)


def round_index(request, tournament_id):
    """Display a list of rounds of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    the_list = t.round_set.all()
    context = {'tournament': t, 'round_list': the_list}
    return render(request, 'rounds/index.html', context)
