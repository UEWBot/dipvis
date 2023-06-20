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
Round Views for the Diplomacy Tournament Visualiser.
"""

import csv
import requests
from itertools import combinations

from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.forms.formsets import formset_factory
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _

from tournament.forms import BaseGamePlayersFormset
from tournament.forms import BasePlayerRoundFormset
from tournament.forms import BasePowerAssignFormset
from tournament.forms import GamePlayersForm
from tournament.forms import GameScoreForm
from tournament.forms import GetSevenPlayersForm
from tournament.forms import PlayerRoundForm
from tournament.forms import PowerAssignForm

from tournament.tournament_views import get_modifiable_tournament_or_404
from tournament.tournament_views import get_visible_tournament_or_404

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.email import send_board_call_email
from tournament.game_seeder import GameSeeder
from tournament.models import PowerAssignMethods
from tournament.models import Round, Game
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer

# Round views

REFRESH_TIME = 60

def get_round_or_404(tournament, round_num):
    """
    Return the specified round of the specified tournament or raise Http404.
    """
    try:
        return tournament.round_numbered(round_num)
    except Round.DoesNotExist as e:
        raise Http404 from e


def round_simple(request, tournament_id, round_num, template):
    """Just render the specified template with the round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    context = {'tournament': t, 'round': r}
    return render(request, f'rounds/{template}.html', context)


def board_call_csv(request, tournament_id, round_num):
    """CSV of the board call for the round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    # Fields to write
    headers = [_('Round'), _('Board'), _('Power'), _('Player Name'), _('Player Id'), _('Backstabbr Username')]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s%dround%sboard_call.csv"' % (t.name,
                                                                                            t.start_date.year,
                                                                                            round_num)

    writer = csv.DictWriter(response, fieldnames=headers)
    writer.writeheader()

    for g in r.game_set.all():
        for gp in g.gameplayer_set.all():
            row_dict = {_('Round'): round_num,
                        _('Board'): g.name,
                        _('Player Name'): str(gp.player),
                        _('Player Id'): gp.player.pk,
                        _('Backstabbr Username'): gp.tournamentplayer().backstabbr_username}
            if gp.power:
                row_dict[_('Power')] = _(gp.power.name)
            writer.writerow(row_dict)

    return response


@permission_required('tournament.add_roundplayer')
def roll_call(request, tournament_id, round_num):
    """Provide a form to specify which players are playing this round"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    PlayerRoundFormset = formset_factory(PlayerRoundForm,
                                         extra=2,
                                         formset=BasePlayerRoundFormset)
    r = get_round_or_404(t, round_num)
    rps = r.roundplayer_set.all()
    player_data = []
    # Go through each player in the Tournament
    for tp in t.tournamentplayer_set.prefetch_related('player'):
        current = {'player': tp.player}
        # Is this player listed as playing this round ?
        try:
            rp = rps.get(player=tp.player)
        except RoundPlayer.DoesNotExist:
            current['present'] = False
            current['standby'] = False
            current['sandboxer'] = False
            current['rounds_played'] = tp.rounds_played()
        else:
            current['present'] = True
            current['standby'] = rp.standby
            current['sandboxer'] = rp.sandboxer
            if rp.gameplayers().exists():
                # This is one of the Rounds they played
                current['rounds_played'] = tp.rounds_played() - 1
            else:
                current['rounds_played'] = tp.rounds_played()
        player_data.append(current)
    formset = PlayerRoundFormset(request.POST or None,
                                 tournament=t,
                                 round_num=int(round_num),
                                 initial=player_data)
    if formset.is_valid():
        errors_added = False
        for form in formset:
            if form.has_changed():
                try:
                    p = form.cleaned_data['player']
                except KeyError:
                    # This must be one of the extra forms, still empty
                    continue
                # Ensure that this Player is in the Tournament
                TournamentPlayer.objects.get_or_create(player=p,
                                                       tournament=t)
                if form.cleaned_data['present'] is True:
                    # Ensure that we have a corresponding RoundPlayer
                    is_standby = form.cleaned_data['standby']
                    sandboxer = form.cleaned_data['sandboxer']
                    RoundPlayer.objects.update_or_create(player=p,
                                                         the_round=r,
                                                         # Reset game_count in case we've been here before
                                                         defaults={'game_count': 0 if is_standby else 1,
                                                                   'standby': is_standby,
                                                                   'sandboxer': sandboxer})
                elif r.game_set.filter(gameplayer__player=p).exists():
                    # Refuse to delete this one
                    form.add_error(None, _('%(player)s did play this round') % {'player': p})
                    errors_added = True
                else:
                    # delete any corresponding RoundPlayer
                    # This could be a player who was previously checked-off in error
                    try:
                        RoundPlayer.objects.get(player=p,
                                                the_round=r).delete()
                    except RoundPlayer.DoesNotExist:
                        pass
        if not errors_added:
            if t.seed_games:
                # Ensure that we have the right number of players
                return HttpResponseRedirect(reverse('get_seven',
                                            args=(tournament_id,
                                                  round_num)))
            # Next job is almost certainly to create the actual games
            return HttpResponseRedirect(reverse('create_games',
                                        args=(tournament_id,
                                              round_num)))

    # Warn the user if they're changing players for an earlier round
    warning = ''
    if r.game_set.exists():
        # We already have Games for this Round
        warning = _("This page is for round %(round)s, which already has games. Submit will change attendance but won't seed games.") % {'round': round_num}

    return render(request,
                  'rounds/roll_call.html',
                  {'tournament': t,
                   'round': r,
                   'post_url': request.path_info,
                   'warning': warning,
                   'formset': formset})


@permission_required('tournament.add_game')
def get_seven(request, tournament_id, round_num):
    """Provide a form to get a multiple of seven players for a round"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    rps = r.roundplayer_set.all()
    present = rps.count()
    # If we have fewer than seven players in total, we're stuffed
    if present < 7:
        return HttpResponseRedirect(reverse('tournament_players',
                                            args=(tournament_id,)))
    playing = rps.filter(standby=False).count()
    context = {'tournament': t,
               'round': r,
               'playing': playing,
               'standbys': present - playing}
    form = GetSevenPlayersForm(request.POST or None,
                               the_round=r)
    if form.is_valid():
        # Update RoundPlayers to indicate number of games they're playing
        # First clear any old game_counts
        for rp in rps.all():
            if rp.standby and not form.all_standbys_needed:
                rp.game_count = 0
            else:
                rp.game_count = 1
            rp.save(update_fields=['game_count'])
        for i in range(form.standbys):
            rp = form.cleaned_data[f'standby_{i}']
            rp.game_count = 1
            rp.save(update_fields=['game_count'])
        for i in range(form.sitters):
            rp = form.cleaned_data[f'sitter_{i}']
            if rp:
                rp.game_count = 0
                rp.save(update_fields=['game_count'])
        for i in range(form.doubles):
            rp = form.cleaned_data[f'double_{i}']
            if rp:
                rp.game_count = 2
                rp.save(update_fields=['game_count'])
        return HttpResponseRedirect(reverse('seed_games',
                                            args=(tournament_id,
                                                  round_num)))
    context['form'] = form
    return render(request,
                  'rounds/get_seven.html',
                  context)


def _sitters_and_two_gamers(tournament, the_round):
    """Return a (sitters, two_gamers) 2-tuple"""
    tourney_players = tournament.tournamentplayer_set.prefetch_related('player')
    round_players = the_round.roundplayer_set.prefetch_related('player')
    # Get the set of players that haven't already been assigned to games for this round
    rps = []
    sitters = set()
    two_gamers = set()
    for rp in round_players:
        assert rp.gameplayers().count() == 0, "%d games already exist for %s in this round" % (rp.gameplayers().count(),
                                                                                               str(rp))
        rps.append(rp)
        if rp.game_count == 1:
            continue
        elif rp.game_count == 0:
            # This player is sitting out this round
            sitters.add(rp.tournamentplayer())
        elif rp.game_count == 2:
            # This player is playing two games this round
            two_gamers.add(rp.tournamentplayer())
        else:
            raise AssertionError('Unexpected game_count value %d for %s' % (rp.game_count, str(rp)))
    assert (not sitters) or (not two_gamers)
    if sitters:
        # Check that we have the right number of players sitting out
        assert (len(rps) - len(sitters)) % 7 == 0
    if two_gamers:
        # Check that we have the right number of players playing two games
        assert (len(rps) + len(two_gamers)) % 7 == 0
    # We also need to flag any players who aren't present for this round as sitting out
    for tp in tourney_players:
        if not round_players.filter(player=tp.player).exists():
            sitters.add(tp)
    return sitters, two_gamers


def _create_game_seeder(tournament, the_round):
    """Return a GameSeeder that knows about the tournament so far"""
    tourney_players = tournament.tournamentplayer_set.prefetch_related('seederbias_set')
    # Create the game seeder
    seeder = GameSeeder(GreatPower.objects.all(),
                        starts=100,
                        iterations=10)
    # Tell the seeder about every player in the tournament
    # (regardless of whether they're playing this round - they may have played already)
    for tp in tourney_players:
        seeder.add_player(tp)
    # Provide details of games already played this tournament
    for rnd in tournament.round_set.filter(start__lt=the_round.start):
        for g in rnd.game_set.prefetch_related('gameplayer_set'):
            game = set()
            for gp in g.gameplayer_set.prefetch_related('power', 'player', 'game__the_round'):
                game.add((gp.tournamentplayer(), gp.power))
            assert len(game) == 7
            seeder.add_played_game(game)
    # Add in any biases now that all players have been added
    for tp in tourney_players:
        # Just use seederbias_set so we only get each SeederBias once
        # because we only look at their player1
        for sb in tp.seederbias_set.all():
            seeder.add_bias(sb.player1, sb.player2)
    # If this is a team round, add biases to separate team members
    if (tournament.team_size is not None) and the_round.is_team_round:
        for t in tournament.team_set.all():
            for p1, p2 in combinations(list(t.players.all()), 2):
                tp1 = p1.tournamentplayer_set.get(tournament=tournament)
                tp2 = p2.tournamentplayer_set.get(tournament=tournament)
                seeder.add_bias(tp1, tp2)
    return seeder


def _seed_games(tournament, the_round):
    """Wrapper round GameSeeder to do the actual seeding for a round"""
    seeder = _create_game_seeder(tournament, the_round)
    sitters, two_gamers = _sitters_and_two_gamers(tournament, the_round)
    # Generate the games
    return seeder.seed_games(omitting_players=sitters,
                             players_doubling_up=two_gamers)


def _seed_games_and_powers(tournament, the_round):
    """Wrapper round GameSeeder to do the actual seeding for a round"""
    seeder = _create_game_seeder(tournament, the_round)
    sitters, two_gamers = _sitters_and_two_gamers(tournament, the_round)
    # Generate the games
    return seeder.seed_games_and_powers(omitting_players=sitters,
                                        players_doubling_up=two_gamers)


def _generate_game_name(round_num, i):
    """Generate a default name for Game n in round round_num"""
    return 'R%sG%s' % (round_num, chr(ord('A') + i - 1))


def _send_board_call_to_discord(the_round):
    """Send a board call message to the discord webhook for the tournament, if any"""
    if not the_round.tournament.discord_url:
        return
    text = the_round.board_call_msg()
    data = {
        "content": text,
        "username": "Diplomacy TV"
           }
    requests.post(the_round.tournament.discord_url, json=data)


@permission_required('tournament.add_game')
def seed_games(request, tournament_id, round_num):
    """Seed players to the games for a round"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    if request.method == 'POST':
        PowerAssignFormset = formset_factory(PowerAssignForm,
                                             formset=BasePowerAssignFormset,
                                             extra=0)
        formset = PowerAssignFormset(request.POST, the_round=r)
        if formset.is_valid():
            for f in formset:
                if f.has_changed():
                    # Update the game
                    g = f.game
                    g.name = f.cleaned_data['name']
                    g.the_set = f.cleaned_data['the_set']
                    g.external_url = f.cleaned_data['external_url']
                    g.notes = f.cleaned_data['notes']
                    try:
                        g.full_clean()
                    except ValidationError as e:
                        f.add_error(None, e)
                        return render(request,
                                      'rounds/seeded_games.html',
                                      {'tournament': t,
                                       'round': r,
                                       'formset': formset})
                    g.save()
                    # Unassign all GreatPowers first,
                    # so we never have two players for one power
                    g.gameplayer_set.update(power=None)
                    # Assign the powers to the players
                    for gp_id, field in f.cleaned_data.items():
                        if gp_id in ['the_set', 'name', 'external_url', 'notes', 'issues']:
                            continue
                        gp = GamePlayer.objects.get(id=gp_id)
                        gp.power = field
                        gp.save(update_fields=['power'])
                    # Generate initial scores
                    g.update_scores(update_round=False)
            # Now all GamePlayer scores have been updated, update the RoundPlayer scores
            r.update_scores()
            # Notify the players
            send_board_call_email(r)
            _send_board_call_to_discord(r)
            # Redirect to the board call page
            return HttpResponseRedirect(reverse('board_call',
                                                args=(tournament_id, round_num)))
    else:
        # Check for a multiple of seven players,
        # allowing for players sitting out or playing multiple games
        player_count = r.roundplayer_set.aggregate(Sum('game_count'))['game_count__sum']
        if (player_count is None) or (player_count % 7) != 0:
            # We need players to sit out or play multiple games
            return HttpResponseRedirect(reverse('get_seven',
                                                args=(tournament_id,
                                                      r.number())))
        # Delete any existing Games and GamePlayers for this round
        r.game_set.all().delete()
        # TODO It's a bit hokey to have a fixed default GameSet here
        if t.is_virtual():
            default_set = GameSet.objects.get(name='Backstabbr')
        else:
            default_set = GameSet.objects.get(pk=1)
        data = []
        # Generate a seeding, and assign powers if required
        if t.power_assignment == PowerAssignMethods.AUTO:
            games = _seed_games_and_powers(t, r)
            # Add the Games and GamePlayers to the database
            for n, (g, i) in enumerate(games, start=1):
                new_game = Game.objects.create(name=_generate_game_name(round_num, n),
                                               the_round=r,
                                               the_set=default_set)
                current = {'name': new_game.name,
                           'the_set': new_game.the_set,
                           'issues': '\n'.join(i)}
                for tp, power in g:
                    gp = GamePlayer.objects.create(player=tp.player,
                                                   game=new_game,
                                                   power=power)
                    current[gp.id] = power
                data.append(current)
        else:
            games = _seed_games(t, r)
            # Add the Games and GamePlayers to the database
            for n, g in enumerate(games, start=1):
                new_game = Game.objects.create(name=_generate_game_name(round_num, n),
                                               the_round=r,
                                               the_set=default_set)
                current = {'name': new_game.name,
                           'the_set': new_game.the_set,
                           'issues': ''}
                for tp in g:
                    gp = GamePlayer.objects.create(player=tp.player,
                                                   game=new_game)
                # If we're assigning powers from preferences, do so now
                if t.power_assignment == PowerAssignMethods.PREFERENCES:
                    new_game.assign_powers_from_prefs()
                for tp in g:
                    gp = GamePlayer.objects.get(player=tp.player,
                                                game=new_game)
                    current[gp.id] = gp.power
                data.append(current)
        # Create a form for each of the resulting games
        PowerAssignFormset = formset_factory(PowerAssignForm,
                                             formset=BasePowerAssignFormset,
                                             extra=0)
        formset = PowerAssignFormset(the_round=r, initial=data)

    context = {'tournament': t, 'round': r, 'formset': formset}
    return render(request, 'rounds/seeded_games.html', context)


@permission_required('tournament.add_game')
def create_games(request, tournament_id, round_num):
    """Provide a form to create the games for a round"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    # Do any games already exist for the round ?
    games = r.game_set.all()
    data = []
    for g in games:
        current = {'game_id': g.id,
                   'name': g.name,
                   'the_set': g.the_set,
                   'external_url': g.external_url,
                   'notes': g.notes}
        for gp in g.gameplayer_set.all():
            if gp.power:
                current[gp.power.name] = gp.roundplayer()
        data.append(current)
    # Estimate the number of games for the round
    round_players = r.roundplayer_set.count()
    expected_games = (round_players + 6) // 7
    # This can happen if there are no RoundPlayers for this round
    if expected_games < 1:
        expected_games = 1
    GamePlayersFormset = formset_factory(GamePlayersForm,
                                         extra=expected_games - games.count(),
                                         formset=BaseGamePlayersFormset)
    formset = GamePlayersFormset(request.POST or None,
                                 the_round=r,
                                 initial=data)
    if formset.is_valid():
        for f in formset:
            if f.has_changed():
                try:
                    if f.cleaned_data['game_id'] is not None:
                        # Game should exist
                        g = Game.objects.get(pk=f.cleaned_data['game_id'])
                        g.name = f.cleaned_data['name']
                        g.the_set = f.cleaned_data['the_set']
                        g.external_url = f.cleaned_data['external_url']
                        g.notes = f.cleaned_data['notes']
                    else:
                        g = Game(name=f.cleaned_data['name'],
                                 the_round=r,
                                 the_set=f.cleaned_data['the_set'],
                                 external_url=f.cleaned_data['external_url'],
                                 notes=f.cleaned_data['notes'])
                except KeyError:
                    # This must be an extra, unused formset
                    continue
                try:
                    g.full_clean()
                except ValidationError as e:
                    f.add_error(None, e)
                    return render(request,
                                  'rounds/create_games.html',
                                  {'tournament': t,
                                   'round': r,
                                   'formset': formset})
                g.save()
                # Assign the players to the game
                with transaction.atomic():
                    # We may already have a set of GamePlayers, and changing
                    # them may (temporarily) violate uniqueness constraints,
                    # so delete any that already exist and then create new ones
                    g.gameplayer_set.all().delete()
                    for power, field in f.cleaned_data.items():
                        try:
                            p = GreatPower.objects.get(name=power)
                        except GreatPower.DoesNotExist:
                            continue
                        GamePlayer.objects.create(game=g,
                                                  power=p,
                                                  player=field.player)
                # Generate initial scores
                g.update_scores(update_round=False)
        # Now all GamePlayer scores have been updated, update the RoundPlayer scores
        r.update_scores()
        # Notify the players
        send_board_call_email(r)
        _send_board_call_to_discord(r)
        # Redirect to the board call page
        return HttpResponseRedirect(reverse('board_call',
                                            args=(tournament_id, round_num)))

    return render(request,
                  'rounds/create_games.html',
                  {'tournament': t,
                   'round': r,
                   'formset': formset})


@permission_required('tournament.change_gameplayer')
def game_scores(request, tournament_id, round_num):
    """Provide a form to enter scores for all the games in a round"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    GameScoreFormset = formset_factory(GameScoreForm,
                                       extra=0)
    # Initial data
    data = []
    the_list = r.game_set.all()
    for game in the_list:
        content = {'name': game.name}
        for gp in game.gameplayer_set.all():
            content[gp.power.name] = gp.score
        data.append(content)
    formset = GameScoreFormset(request.POST or None, initial=data)
    if formset.is_valid():
        for f in formset:
            if f.has_changed():
                # Find the game
                g = Game.objects.get(name=f.cleaned_data['name'],
                                     the_round=r)
                # Set the score for each player
                for power, field in f.cleaned_data.items():
                    try:
                        p = GreatPower.objects.get(name=power)
                    except GreatPower.DoesNotExist:
                        # Ignore non-GreatPower fields (name)
                        continue
                    # Find the matching GamePlayer
                    GamePlayer.objects.filter(game=g,
                                              power=p).update(score=field)
        # Update the Round and Tournament scores to reflect the changes
        r.update_scores()
        # Redirect to the round index
        return HttpResponseRedirect(reverse('round_index',
                                            args=(tournament_id,)))

    return render(request,
                  'rounds/game_score.html',
                  {'tournament': t,
                   'round': round_num,
                   'formset': formset})


def game_index(request, tournament_id, round_num):
    """Display a list of games in the round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    the_list = r.game_set.all()
    context = {'round': r, 'game_list': the_list}
    return render(request, 'games/index.html', context)


def game_cycle(request, tournament_id, round_num, template, game_name=None):
    """Cycle through SC graphs for all games in the Round"""
    # TODO We should also be able to support cycling through SC charts here,
    #      except that the template needs more parameters. Ideally, we'd
    #      probably pass the game view function rather than the template
    #      and just call it from here, but it's tricky to figure out what
    #      redirect_url to pass to it.
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    games = r.game_set.all()
    if (len(games)) == 0:
        raise Http404
    if game_name:
        # Find the game in the list
        g = None
        for n, g1 in enumerate(games):
            if g1.name == game_name:
                # Found it
                g = g1
                break
        if not g:
            raise Http404
    else:
        g = games.first()
        n = 0
    try:
        next_game_name = games[n+1].name
    except IndexError:
        # Go back to the first game
        next_game_name = games[0].name
    context = {'game': g,
               'refresh': True,
               'redirect_time': REFRESH_TIME,
               'redirect_url': reverse(game_cycle,
                                       args=(tournament_id, r.number(), next_game_name))}
    return render(request, template, context)
