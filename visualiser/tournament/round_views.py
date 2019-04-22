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

from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.forms.formsets import formset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext as _

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

from tournament.diplomacy import GreatPower, GameSet
from tournament.email import send_board_call
from tournament.game_seeder import GameSeeder
from tournament.models import Tournament, Round, Game
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer

# Round views

def get_round_or_404(tournament, round_num):
    """Return the specified numbered round of the specified tournament or raise Http404."""
    try:
        return tournament.round_numbered(round_num)
    except Round.DoesNotExist:
        raise Http404

def round_simple(request, tournament_id, round_num, template):
    """Just render the specified template with the round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    context = {'tournament': t, 'round': r}
    return render(request, 'rounds/%s.html' % template, context)

@permission_required('tournament.add_roundplayer')
def roll_call(request, tournament_id, round_num=None):
    """Provide a form to specify which players are playing each round"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    PlayerRoundFormset = formset_factory(PlayerRoundForm,
                                         extra=2,
                                         formset=BasePlayerRoundFormset)
    if round_num:
        r = get_round_or_404(t, round_num)
        round_set = t.round_set.filter(pk=r.pk)
    else:
        round_set = t.round_set.all()
    data = []
    # Go through each player in the Tournament
    for tp in t.tournamentplayer_set.all():
        current = {'player': tp.player}
        rps = tp.roundplayers()
        # And each round of the Tournament
        for r in round_set:
            # Is this player listed as playing this round ?
            played = rps.filter(the_round=r).exists()
            current['round_%d' % r.number()] = played
        data.append(current)
    if round_num:
        formset = PlayerRoundFormset(request.POST or None,
                                     tournament=t,
                                     round_num=int(round_num),
                                     initial=data)
    else:
        formset = PlayerRoundFormset(request.POST or None,
                                     tournament=t,
                                     initial=data)
    if formset.is_valid():
        for form in formset:
            try:
                p = form.cleaned_data['player']
            except KeyError:
                # This must be one of the extra forms, still empty
                continue
            # Ensure that this Player is in the Tournament
            i, created = TournamentPlayer.objects.get_or_create(player=p,
                                                                tournament=t)
            try:
                i.full_clean()
            except ValidationError as e:
                form.add_error(form.fields['player'], e)
                i.delete()
                return render(request,
                              'tournaments/round_players.html',
                              {'title': _('Roll Call'),
                               'tournament': t,
                               'post_url': reverse('roll_call', args=(tournament_id,)),
                               'formset' : formset})
            if created:
                i.save()
            for r_name, value in form.cleaned_data.items():
                if r_name == 'player':
                    # This column is just for the user
                    continue
                # Extract the round number from the field name
                i = int(r_name[6:])
                # Find that Round
                r = t.round_numbered(i)
                # Ignore non-bool fields and ones that aren't True
                if value is True:
                    # Ensure that we have a corresponding RoundPlayer
                    i, created = RoundPlayer.objects.get_or_create(player=p,
                                                                   the_round=r)
                    try:
                        i.full_clean()
                    except ValidationError as e:
                        form.add_error(None, e)
                        i.delete()
                        return render(request,
                                      'tournaments/round_players.html',
                                      {'title': _('Roll Call'),
                                       'tournament': t,
                                       'post_url': reverse('roll_call', args=(tournament_id,)),
                                       'formset' : formset})
                    if created:
                        i.save()
                else:
                    # delete any corresponding RoundPlayer
                    # This could be a player who was previously checked-off in error
                    RoundPlayer.objects.filter(player=p,
                                               the_round=r).delete()
        r = t.current_round()
        # If we're doing a roll call for a single round,
        # we only want to seed boards if it's the current round
        if not round_num or (r.number() == round_num):
            if t.seed_games:
                if (r.roundplayer_set.count() % 7) == 0:
                    # We have an exact multiple of 7 players, so go straight to seeding
                    return HttpResponseRedirect(reverse('seed_games',
                                                        args=(tournament_id,
                                                              r.number())))
                # We need players to sit out or play multiple games
                return HttpResponseRedirect(reverse('get_seven',
                                                    args=(tournament_id,
                                                          r.number())))
            else:
                # Next job is almost certainly to create the actual games
                return HttpResponseRedirect(reverse('create_games',
                                                    args=(tournament_id,
                                                          r.number())))

    return render(request,
                  'tournaments/round_players.html',
                  {'title': _('Roll Call'),
                   'tournament': t,
                   'post_url': reverse('roll_call', args=(tournament_id,)),
                   'formset' : formset})

@permission_required('tournament.add_game')
def get_seven(request, tournament_id, round_num):
    """Provide a form to get a multiple of seven players for a round"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    count = r.roundplayer_set.count()
    sitters = count % 7
    # If we already have an exact multiple of seven players, go straight to creating games
    if sitters == 0:
        return HttpResponseRedirect(reverse('seed_games',
                                            args=(tournament_id,
                                                  round_num)))

    doubles = 7 - sitters
    context = {'tournament': t,
               'round': r,
               'count' : count,
               'sitters' : sitters,
               'doubles' : doubles}
    form = GetSevenPlayersForm(request.POST or None,
                               the_round=r)
    if form.is_valid():
        # Update RoundPlayers to indicate number of games they're playing
        # First clear any old game_counts
        for rp in r.roundplayer_set.exclude(game_count=1):
            rp.game_count = 1
            rp.save()
        for i in range(sitters):
            rp = form.cleaned_data['sitter_%d' % i]
            if rp:
                rp.game_count = 0
                rp.save()
        for i in range(doubles):
            rp = form.cleaned_data['double_%d' % i]
            if rp:
                rp.game_count = 2
                rp.save()
        return HttpResponseRedirect(reverse('seed_games',
                                            args=(tournament_id,
                                                  round_num)))
    context['form'] = form
    return render(request,
                  'rounds/get_seven.html',
                  context)

def _sitters_and_two_gamers(tournament, the_round):
    """ Return a (sitters, two_gamers) 2-tuple"""
    tourney_players = tournament.tournamentplayer_set.all()
    round_players = the_round.roundplayer_set.all()
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
            assert 0, 'Unexpected game_count value %d for %s' % (rp.game_count, str(rp))
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

def _create_game_seeder(tournament, round_number):
    """Return a GameSeeder that knows about the tournament so far"""
    tourney_players = tournament.tournamentplayer_set.all()
    # Create the game seeder
    seeder = GameSeeder(GreatPower.objects.all(),
                        starts=100,
                        iterations=10)
    # Tell the seeder about every player in the tournament
    # (regardless of whether they're playing this round - they may have played already)
    for tp in tourney_players:
        seeder.add_player(tp)
    # Provide details of games already played this tournament
    for n in range(1, round_number):
        rnd = tournament.round_numbered(n)
        for g in rnd.game_set.all():
            game = set()
            for gp in g.gameplayer_set.all():
                game.add((gp.tournamentplayer(), gp.power))
            # TODO This doesn't deal with replacement players
            assert len(game) == 7
            seeder.add_played_game(game)
    # Add in any biases now that all players have been added
    for tp in tourney_players:
        # Just use seederbias_set so we only get each SeederBias once
        # because we only look at their player1
        for sb in tp.seederbias_set.all():
            seeder.add_bias(sb.player1, sb.player2, sb.weight)
    return seeder

def _seed_games(tournament, the_round):
    """Wrapper round GameSeeder to do the actual seeding for a round"""
    seeder = _create_game_seeder(tournament, the_round.number())
    sitters, two_gamers = _sitters_and_two_gamers(tournament, the_round)
    # Generate the games
    return seeder.seed_games(omitting_players=sitters,
                             players_doubling_up=two_gamers)

def _seed_games_and_powers(tournament, the_round):
    """Wrapper round GameSeeder to do the actual seeding for a round"""
    seeder = _create_game_seeder(tournament, the_round.number())
    sitters, two_gamers = _sitters_and_two_gamers(tournament, the_round)
    # Generate the games
    return seeder.seed_games_and_powers(omitting_players=sitters,
                                        players_doubling_up=two_gamers)

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
                # Update the game
                g = f.game
                g.name = f.cleaned_data['game_name']
                g.the_set = f.cleaned_data['the_set']
                try:
                    g.full_clean()
                except ValidationError as e:
                    f.add_error(None, e)
                    return render(request,
                                  'rounds/seeded_games.html',
                                  {'tournament': t,
                                   'round': r,
                                   'formset' : formset})
                g.save()
                # Assign the powers to the players
                for gp_id, field in f.cleaned_data.items():
                    if gp_id in ['the_set', 'game_name']:
                        continue
                    gp = GamePlayer.objects.get(id=gp_id)
                    gp.power = field
                    try:
                        gp.full_clean()
                    except ValidationError as e:
                        f.add_error(None, e)
                        return render(request,
                                      'rounds/seeded_games.html',
                                      {'tournament': t,
                                       'round': r,
                                       'formset' : formset})
                    gp.save()
            # Notify the players
            send_board_call(r)
            # Redirect to the index of games in the round
            return HttpResponseRedirect(reverse('game_index',
                                                args=(tournament_id, round_num)))
    else:
        # Delete any existing Games and GamePlayers for this round
        r.game_set.all().delete()
        # TODO It's a bit hokey to have a fixed default GameSet here
        default_set = GameSet.objects.get(pk=1)
        data = []
        # Generate a seeding, and assign powers if required
        if t.power_assignment == Tournament.AUTO:
            games = _seed_games_and_powers(t, r)
            # Add the Games and GamePlayers to the database
            for i, g in enumerate(games, start=1):
                new_game = Game.objects.create(name='R%sG%d' % (round_num, i),
                                               the_round=r,
                                               the_set=default_set)
                current = {'game_name': new_game.name,
                           'the_set': new_game.the_set}
                for tp, power in g:
                    gp = GamePlayer.objects.create(player=tp.player,
                                                   game=new_game,
                                                   power=power)
                    current[gp.id] = power
                data.append(current)
        else:
            games = _seed_games(t, r)
            # Add the Games and GamePlayers to the database
            for i, g in enumerate(games, start=1):
                new_game = Game.objects.create(name='R%sG%d' % (round_num, i),
                                               the_round=r,
                                               the_set=default_set)
                current = {'game_name': new_game.name,
                           'the_set': new_game.the_set}
                for tp in g:
                    gp = GamePlayer.objects.create(player=tp.player,
                                                   game=new_game)
                # If we're assigning powers from preferences, do so now
                if t.power_assignment == Tournament.PREFERENCES:
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
    # Note that we wait for confirmation before adding them to the database
    context = {'tournament': t, 'round': r, 'games': games, 'formset': formset}
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
        current = {'game_name': g.name,
                   'the_set': g.the_set}
        for gp in g.gameplayer_set.all():
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
            # Update/create the game
            try:
                g, created = Game.objects.get_or_create(name=f.cleaned_data['game_name'],
                                                        the_round=r,
                                                        the_set=f.cleaned_data['the_set'])
            except KeyError:
                # This must be an extra, unused formset
                continue
            try:
                g.full_clean()
            except ValidationError as e:
                f.add_error(None, e)
                g.delete()
                return render(request,
                              'rounds/create_games.html',
                              {'tournament': t,
                               'round': r,
                               'formset' : formset})
            if created:
                g.save()
            # Assign the players to the game
            for power, field in f.cleaned_data.items():
                try:
                    p = GreatPower.objects.get(name=power)
                except GreatPower.DoesNotExist:
                    continue
                # Is there already a player for this power in this game ?
                try:
                    i = GamePlayer.objects.get(game=g,
                                               power=p)
                except GamePlayer.DoesNotExist:
                    # Create one (default first_season and first_year)
                    i = GamePlayer(player=field.player, game=g, power=p)
                else:
                    # Change the player (if necessary)
                    i.player = field.player
                try:
                    i.full_clean()
                except ValidationError as e:
                    f.add_error(None, e)
                    # TODO Not 100% certain that this is the right thing to do here
                    i.delete()
                    return render(request,
                                  'rounds/create_games.html',
                                  {'tournament': t,
                                   'round': r,
                                   'formset' : formset})
                i.save()
        # Notify the players
        send_board_call(r)
        # Redirect to the index of games in the round
        return HttpResponseRedirect(reverse('game_index',
                                            args=(tournament_id, round_num)))

    return render(request,
                  'rounds/create_games.html',
                  {'tournament': t,
                   'round': r,
                   'formset' : formset})

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
        content = {'game_name': game.name}
        for gp in game.gameplayer_set.all():
            content[gp.power.name] = gp.score
        data.append(content)
    formset = GameScoreFormset(request.POST or None, initial=data)
    if formset.is_valid():
        for f in formset:
            # Find the game
            g = Game.objects.get(name=f.cleaned_data['game_name'],
                                 the_round=r)
            # Set the score for each player
            for power, field in f.cleaned_data.items():
                # Ignore non-GreatPower fields (game_name)
                try:
                    p = GreatPower.objects.get(name=power)
                except GreatPower.DoesNotExist:
                    continue
                # Find the matching GamePlayer
                # TODO This will fail if there was a replacement
                i = GamePlayer.objects.get(game=g,
                                           power=p)
                # Set the score
                i.score = field
                try:
                    i.full_clean()
                except ValidationError as e:
                    f.add_error(None, e)
                    return render(request,
                                  'rounds/game_score.html',
                                  {'tournament': t,
                                   'round': round_num,
                                   'formset' : formset})
                i.save()
        # Redirect to the round index
        return HttpResponseRedirect(reverse('round_index',
                                            args=(tournament_id)))

    return render(request,
                  'rounds/game_score.html',
                  {'tournament': t,
                   'round': round_num,
                   'formset' : formset})

def game_index(request, tournament_id, round_num):
    """Display a list of games in the round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    the_list = r.game_set.all()
    context = {'round': r, 'game_list': the_list}
    return render(request, 'games/index.html', context)
