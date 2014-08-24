# Diplomacy Tournament Visualiser
# Copyright (C) 2014 Chris Brand
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

from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views import generic
from django.forms.models import inlineformset_factory
from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.template import RequestContext

from tournament.models import *

from datetime import datetime

class DrawForm(forms.Form):
    """Form for a draw vote"""
    year = forms.IntegerField(min_value=FIRST_YEAR)
    season = forms.ChoiceField(choices=SEASONS)
    proposer = forms.ModelChoiceField(queryset=GreatPower.objects.all(),
                                      to_field_name='name')
    passed = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        """Adds powers field if game is not set Draws Include All Survivors"""
        # Remove our special kwarg from the list
        is_dias = kwargs.pop('dias')
        super(DrawForm, self).__init__(*args, **kwargs)

        if not is_dias:
            self.fields['powers'] = forms.ModelMultipleChoiceField(queryset=GreatPower.objects.all(),
                                                                   to_field_name='name',
                                                                   widget=forms.SelectMultiple(attrs={'size':'7'}))

class GameScoreForm(forms.Form):
    """Form for score for a single game"""
    # TODO With game names in URLs, they can't contain spaces
    game_name = forms.CharField(label='Game Name', max_length=10)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one score field per Great Power"""
        super(GameScoreForm, self).__init__(*args, **kwargs)

        # No changing the game name !
        attrs = self.fields['game_name'].widget.attrs
        attrs['size'] = attrs['maxlength']
        attrs['readonly'] = 'readonly'

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            # Don't require a score for every player
            self.fields[c] = forms.FloatField(required=False)
            attrs = self.fields[c].widget.attrs
            attrs['size'] = 10
            attrs['maxlength'] = 10

class RoundPlayerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.player.__unicode__()

class GamePlayersForm(forms.Form):
    """Form for players of a single game"""
    game_name = forms.CharField(label='Game Name', max_length=10)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one player field per Great Power"""
        # Remove our special kwarg from the list
        self.the_round = kwargs.pop('the_round')
        super(GamePlayersForm, self).__init__(*args, **kwargs)

        attrs = self.fields['game_name'].widget.attrs
        attrs['size'] = attrs['maxlength']

        queryset = self.the_round.roundplayer_set.all()

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            self.fields[c] = RoundPlayerChoiceField(queryset)
            self.fields[c].widget.attrs['size'] = 20

    def clean(self):
        """Checks that no player is playing multiple powers"""
        cleaned_data = self.cleaned_data
        players = []
        for power in GreatPower.objects.all():
            c = power.name
            player = cleaned_data.get(c)
            # If the field itself didn't validate, drop out
            if player == None:
                return cleaned_data
            if player in players:
                raise forms.ValidationError('Player %s appears more than once' % player)
            players.append(player)

        return cleaned_data

class BaseGamePlayersForm(BaseFormSet):
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.the_round = kwargs.pop('the_round')
        super(BaseGamePlayersForm, self).__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['the_round'] = self.the_round
        return super(BaseGamePlayersForm, self)._construct_form(index, **kwargs)

class SCCountForm(forms.Form):
    """Form for a Supply Centre count"""
    # Allow for an initial game-start SC count
    year = forms.IntegerField(min_value=FIRST_YEAR-1)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one count field per Great Power"""
        super(SCCountForm, self).__init__(*args, **kwargs)

        self.fields['year'].widget.attrs['size'] = 4

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            # TODO It may make sense to use required=False
            # and to default any not provided to zero
            # It may also make sense for that default to be in the model...
            self.fields[c] = forms.IntegerField(min_value=0, max_value=TOTAL_SCS)
            self.fields[c].widget.attrs['size'] = 2
            self.fields[c].widget.attrs['maxlength'] = 2

    def clean(self):
        """Checks that the total SC count is reasonable"""
        cleaned_data = self.cleaned_data
        year = self.cleaned_data.get('year')
        total_scs = 0
        for power in GreatPower.objects.all():
            c = power.name
            dots = cleaned_data.get(c)
            # If the field itself didn't validate, drop out
            if dots == None:
                return cleaned_data
            total_scs += dots
        if total_scs > TOTAL_SCS:
            raise forms.ValidationError("Total SC count for %d is %d, more than %d" % (year, total_scs, TOTAL_SCS))
        # Add a pseudo-field with the number of neutrals, for convenience
        self.cleaned_data['neutral'] = TOTAL_SCS - total_scs

        return cleaned_data

class BaseSCCountFormset(BaseFormSet):
    def clean(self):
        """
        Checks that no year appears more than once,
        and that neutrals always decrease
        """
        if any(self.errors):
            return
        years = {}
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            year = form.cleaned_data.get('year')
            if not year:
                continue
            if year in years:
                raise forms.ValidationError('Year %s appears more than once' % year)
            # For convenience, store the number of neutrals left each year
            years[year] = form.cleaned_data.get('neutral')
        # Now check that the number of neutrals only goes down
        neutrals = TOTAL_SCS
        for year in sorted(years.iterkeys()):
            if years[year] > neutrals:
                raise forms.ValidationError('Neutrals increases from %d to %d in %d' % (neutrals, years[year], year))
            neutrals = years[year]

class TournamentPlayerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.player.__unicode__()

class PlayerRoundForm(forms.Form):
    """Form to specify which rounds a player played in"""
    player = TournamentPlayerChoiceField(queryset=Tournament.objects.none())

    def __init__(self, *args, **kwargs):
        # Remove our three special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        self.rounds = kwargs.pop('rounds')
        self.this_round = kwargs.pop('this_round')
        super(PlayerRoundForm, self).__init__(*args, **kwargs)
        self.fields['player'].queryset = self.tournament.tournamentplayer_set.all()

        # Create the right number of round fields, with the right ones read-only
        for i in range(1, 1 + self.rounds):
            name = 'round_%d' % i
            readonly = (i < self.this_round)
            self.fields[name] = forms.BooleanField(required=False, initial=False)
            if readonly:
                # "readonly" on checkboxes is purely visual, but good enough for now
                self.fields[name].widget.attrs['readonly'] = 'readonly'

class BasePlayerRoundFormset(BaseFormSet):
    def clean(self):
        """Checks that no player appears more than once"""
        if any(self.errors):
            return
        players = []
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            player = form.cleaned_data.get('player')
            if not player:
                continue
            if player in players:
                raise forms.ValidationError('Player %s appears more than once' % player)
            players.append(player)

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        super(BasePlayerRoundFormset, self).__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the three special args down to the form itself
        kwargs['tournament'] = self.tournament
        kwargs['rounds'] = self.tournament.round_set.count()
        # TODO current_round() could return None, if all rounds are over
        kwargs['this_round'] = self.tournament.current_round().number
        return super(BasePlayerRoundFormset, self)._construct_form(index, **kwargs)

class PlayerRoundScoreForm(forms.Form):
    """Form to enter round score(s) for a player"""
    player = TournamentPlayerChoiceField(queryset=Tournament.objects.none())

    def __init__(self, *args, **kwargs):
        # Remove our three special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        self.rounds = kwargs.pop('rounds')
        self.this_round = kwargs.pop('this_round')
        super(PlayerRoundScoreForm, self).__init__(*args, **kwargs)
        self.fields['player'].queryset = self.tournament.tournamentplayer_set.all()

        self.fields['player'].widget.attrs['readonly'] = 'readonly'

        # Create the right number of round fields, with the right ones read-only
        for i in range(1, 1 + self.rounds):
            name = 'round_%d' % i
            readonly = (i < self.this_round)
            if not readonly:
                # Create an additional field to show the game scores for that round
                game_scores_name = 'game_scores_%d' %i
                self.fields[game_scores_name] = forms.CharField(max_length=10,
                                                                required=False)
                attrs = self.fields[game_scores_name].widget.attrs
                attrs['readonly'] = 'readonly'
            self.fields[name] = forms.FloatField(required=False)
            attrs = self.fields[name].widget.attrs
            attrs['size'] = 10
            attrs['maxlength'] = 10
            if readonly:
                # "readonly" on checkboxes is purely visual, but good enough for now
                self.fields[name].widget.attrs['readonly'] = 'readonly'

class BasePlayerRoundScoreFormset(BaseFormSet):
    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        super(BasePlayerRoundScoreFormset, self).__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the three special args down to the form itself
        kwargs['tournament'] = self.tournament
        kwargs['rounds'] = self.tournament.round_set.count()
        # TODO current_round() could return None, if all rounds are over
        kwargs['this_round'] = self.tournament.current_round().number
        return super(BasePlayerRoundScoreFormset, self)._construct_form(index, **kwargs)

class TourneyIndexView(generic.ListView):
    template_name = 'tournaments/index.html'
    context_object_name = 'tournament_list'

    def get_queryset(self):
        """Sort in date order, latest at the top"""
        return Tournament.objects.order_by('-start_date')

class TourneyDetailView(generic.DetailView):
    model = Tournament
    template_name = 'tournaments/detail.html'

# Tournament views

def tournament_scores(request, tournament_id):
    """Display scores of a tournament"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    tps = t.tournamentplayer_set.order_by('-score')
    rds = t.round_set.order_by('number')
    rounds = [r.number for r in rds]
    # Construct a list of lists with [player name, round 1 score, ..., round n score, tournament score]
    scores = []
    for p in tps:
        rs = []
        for r in rds:
            rp = p.player.roundplayer_set.filter(the_round=r)
            if rp:
                rs.append(rp.score)
            else:
                rs.append('')
        scores.append(['%s' % p.player] + rs + ['%f' % p.score])
    context = {'tournament': t, 'scores': scores, 'rounds': rounds}
    return render(request, 'tournaments/scores.html', context)

def tournament_background(request, tournament_id):
    """Display background info for a tournament"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    context = {'tournament': t, 'background': t.background()}
    return render(request, 'tournaments/background.html', context)

def tournament_news(request, tournament_id):
    """Display the latest news of a tournament"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    context = {'tournament': t, 'news': t.news()}
    return render(request, 'tournaments/news.html', context)

def tournament_round(request, tournament_id):
    """Display details of the currently in-progress round of a tournament"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    r = t.current_round()
    if r:
        context = {'round': r}
        return render(request, 'rounds/detail.html', context)
    # TODO There must be a better way than this
    return HttpResponse("No round currently being played")

# TODO Name is confusing - sounds like it takes a round_num
def round_scores(request, tournament_id):
    """Provide a form to enter each player's score for each round"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    round_set = t.round_set.all()
    PlayerRoundScoreFormset = formset_factory(PlayerRoundScoreForm,
                                              extra=0,
                                              formset=BasePlayerRoundScoreFormset)
    if request.method == 'POST':
        formset = PlayerRoundScoreFormset(request.POST, tournament=t)
        if formset.is_valid():
            for form in formset:
                player = form.cleaned_data['player']
                for r_name,value in f.cleaned_data.iteritems():
                    # We're only interested in the round score fields
                    if not r_name.startswith('round_'):
                        continue
                    # Extract the round number from the field name
                    i = int(r_name[6:])
                    # Find that Round
                    r = round_set.get(number=i)
                    # Update the score
                    i, created = RoundPlayer.objects.get_or_create(player=player,
                                                                   the_round=r)
                    i.score = value
                    i.save()
            # Redirect to the read-only version
            return HttpResponseRedirect(reverse('tournament_scores',
                                                args=(tournament_id,)))
    else:
        data = []
        # Go through each player in the Tournament
        for tp in t.tournamentplayer_set.all():
            current = {'player': tp}
            for rp in tp.player.roundplayer_set.all():
                current['round_%d'%rp.the_round.number] = rp.score
                # Scores for any games in the round
                games = GamePlayer.objects.filter(player=tp.player,
                                                  game__the_round=r)
                current['game_scores_%d'%i] = ', '.join(str(g.score) for g in games)
            data.append(current)
        formset = PlayerRoundScoreFormset(tournament=t, initial=data)

    return render_to_response('tournaments/round_players.html',
                              {'title': 'Scores',
                               'tournament': t,
                               'formset' : formset},
                              context_instance = RequestContext(request))

def roll_call(request, tournament_id):
    """Provide a form to specify which players are playing each round"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    round_set = t.round_set.all()
    PlayerRoundFormset = formset_factory(PlayerRoundForm,
                                         extra=2,
                                         formset=BasePlayerRoundFormset)
    if request.method == 'POST':
        formset = PlayerRoundFormset(request.POST, tournament=t)
        if formset.is_valid():
            for form in formset:
                try:
                    tp = form.cleaned_data['player']
                except KeyError:
                    # This must be one of the extra forms, still empty
                    continue
                for r_name,value in form.cleaned_data.iteritems():
                    # Ignore non-bool fields and ones that aren't True
                    if value != True:
                        continue
                    # Extract the round number from the field name
                    i = int(r_name[6:])
                    # Find that Round
                    r = round_set.get(number=i)
                    # Ensure that we have a corresponding RoundPlayer
                    i, created = RoundPlayer.objects.get_or_create(player=tp.player,
                                                                   the_round=r)
                    i.save()
            # Next job is almost certainly to create the actual games
            return HttpResponseRedirect(reverse('create_games',
                                                args=(tournament_id, t.current_round().number)))
    else:
        data = []
        # Go through each player in the Tournament
        for tp in t.tournamentplayer_set.all():
            current = {'player':tp}
            # And each round of the Tournament
            for r in t.round_set.order_by('number'):
                i = r.number
                # Is this player listed as playing this round ?
                played = r.roundplayer_set.filter(player=tp.player).exists()
                current['round_%d'%i] = played
            data.append(current)
        formset = PlayerRoundFormset(tournament=t, initial=data)

    return render_to_response('tournaments/round_players.html',
                              {'title': 'Roll Call',
                               'tournament': t,
                               'formset' : formset},
                              context_instance = RequestContext(request))

def round_index(request, tournament_id):
    """Display a list of rounds of a tournament"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    the_list = t.round_set.order_by('number')
    context = {'tournament': t, 'round_list': the_list}
    return render(request, 'rounds/index.html', context)

# Round views

def round_detail(request, tournament_id, round_num):
    """Display the details of a round"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
	r = t.round_set.get(number=round_num)
    except Round.DoesNotExist:
	raise Http404
    context = {'round': r}
    return render(request, 'rounds/detail.html', context)

def create_games(request, tournament_id, round_num):
    """Provide a form to create the games for a round"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
	r = t.round_set.get(number=round_num)
    except Round.DoesNotExist:
	raise Http404
    if request.method == 'POST':
        GamePlayersFormset = formset_factory(GamePlayersForm, formset=BaseGamePlayersForm)
        formset = GamePlayersFormset(request.POST, the_round=r)
        if formset.is_valid():
            for f in formset:
                # Update/create the game
                try:
                    g, created = Game.objects.get_or_create(name=f.cleaned_data['game_name'],
                                                            started_at=datetime.now(),
                                                            the_round=r)
                except KeyError:
                    # This must be an extra, unused formset
                    continue
                g.save()
                # Assign the players to the game
                for power, field in f.cleaned_data.iteritems():
                    try:
                        p = GreatPower.objects.get(name=power)
                    except GreatPower.DoesNotExist:
                        continue
                    i, created = GamePlayer.objects.get_or_create(player=field.player,
                                                                  game = g,
                                                                  power=p)
                    i.save()
            # Redirect to the index of games in the round
            return HttpResponseRedirect(reverse('game_index',
                                                args=(tournament_id, round_num)))
    else:
        # Estimate the number of games for the round
        round_players = r.roundplayer_set.count()
        expected_games = (round_players + 6) / 7
        if expected_games < 1:
            expected_games = 1
        GamePlayersFormset = formset_factory(GamePlayersForm,
                                             extra=expected_games,
                                             formset=BaseGamePlayersForm)
        formset = GamePlayersFormset(the_round=r)

    return render_to_response('rounds/create_games.html',
                              {'tournament': t,
                               'round': r,
                               'formset' : formset},
                              context_instance = RequestContext(request))

def game_scores(request, tournament_id, round_num):
    """Provide a form to enter scores for all the games in a round"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
	r = t.round_set.get(number=round_num)
    except Round.DoesNotExist:
	raise Http404
    GameScoreFormset = formset_factory(GameScoreForm,
                                       extra=0)
    if request.method == 'POST':
        formset = GameScoreFormset(request.POST)
        if formset.is_valid():
            for f in formset:
                # Find the game
                g = Game.objects.get(name=f.cleaned_data['game_name'],
                                     the_round=r)
                # Set the score for each player
                for power, field in f.cleaned_data.iteritems():
                    # Ignore non-GreatPower fields (game_name)
                    try:
                        p = GreatPower.objects.get(name=power)
                    except GreatPower.DoesNotExist:
                        continue
                    # Find the matching GamePlayer
                    # TODO This will fail if there was a replacement
                    i = GamePlayer.objects.get(game=g, power=p)
                    # Set the score
                    i.score = field
                    i.save()
            # TODO Redirect to somewhere that actually exists...
            return HttpResponseRedirect('/thanks/')
    else:
        # Initial data
        data = []
        the_list = r.game_set.order_by('name')
        for game in the_list:
            data.append({'game_name': game.name})
        formset = GameScoreFormset(initial=data)

    return render_to_response('rounds/game_score.html',
                              {'tournament': t,
                               'round': r,
                               'formset' : formset},
                              context_instance = RequestContext(request))

def game_index(request, tournament_id, round_num):
    """Display a list of games in the round"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
	r = t.round_set.get(number=round_num)
    except Round.DoesNotExist:
	raise Http404
    the_list = r.game_set.order_by('name')
    context = {'round': r, 'game_list': the_list}
    return render(request, 'games/index.html', context)

# Game views

def game_detail(request, tournament_id, game_name):
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
        g = Game.objects.filter(name=game_name, the_round__tournament=t).get()
    except Game.DoesNotExist:
        raise Http404
    context = {'tournament': t, 'game': g}
    # TODO Render actual game detail
    return HttpResponse("This is the tournament %s game %s detail" % (tournament_id, game_name))

def game_sc_chart(request, tournament_id, game_name):
    """Display the SupplyCentre chart for a game"""
    #CentreCountFormSet = inlineformset_factory(Game, CentreCount)
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
        g = Game.objects.filter(name=game_name, the_round__tournament=t).get()
    except Game.DoesNotExist:
        raise Http404
    powers = GreatPower.objects.all()
    # Massage ps so we have one entry per power
    players = g.players(latest=False)
    ps = []
    for power in powers:
        names = '<br>'.join(map(unicode, players[power]))
        ps.append(names)
    scs = g.centrecount_set.order_by('power', 'year')
    # Create a list of years that have been played
    years = g.years_played()
    # Create a list of rows, each with a year and each power's SC count
    rows = []
    for year in years:
        neutrals = TOTAL_SCS
        yscs = scs.filter(year=year)
        row = []
        row.append(year)
        for power in powers:
            try:
                sc = yscs.filter(power=power).get()
                row.append(sc.count)
                neutrals -= sc.count
            except CentreCount.DoesNotExist:
                # This is presumably because they were eliminated
                row.append(0)
        row.append(neutrals)
        rows.append(row)
    context = {'game': g, 'powers': powers, 'players': ps, 'rows': rows}
    #formset = CentreCountFormSet(instance=g, queryset=scs)
    return render(request, 'games/sc_count.html', context)

def sc_counts(request, tournament_id, game_name):
    """Provide a form to enter SC counts for a game"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
        g = Game.objects.filter(name=game_name, the_round__tournament=t).get()
    except Game.DoesNotExist:
        raise Http404
    SCCountFormset = formset_factory(SCCountForm,
                                     extra=2,
                                     formset=BaseSCCountFormset)
    if request.method == 'POST':
        formset = SCCountFormset(request.POST)
        if formset.is_valid():
            for form in formset:
                year = form.cleaned_data['year']
                for name, value in form.cleaned_data.iteritems():
                    try:
                        power = GreatPower.objects.get(name=name)
                    except:
                        continue
                    # Can't use get_or_create() here,
                    # because count has no default and may have changed
                    try:
                        i = CentreCount.objects.get(power=power,
                                                    game=g,
                                                    year=year)
                        # Ensure the count has the value we want
                        i.count = value
                    except CentreCount.DoesNotExist:
                        i = CentreCount(power=power,
                                        game=g,
                                        year=year,
                                        count=value)
                    i.save()
            # Redirect to the read-only version
            return HttpResponseRedirect(reverse('game_sc_chart',
                                                args(tournament_id, game_name)))
    else:
        # Put in all the existing CentreCounts for this game
        data = []
        for year in g.years_played():
            scs = {'year': year}
            counts = g.centrecount_set.filter(year=year)
            for c in counts:
                scs[c.power.name] = c.count
            data.append(scs)
        formset = SCCountFormset(initial=data)

    return render_to_response('games/sc_counts_form.html',
                              {'formset': formset,
                               'tournament': t,
                               'game': g},
                              context_instance = RequestContext(request))

def game_news(request, tournament_id, game_name):
    """Display news for a game"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
        g = Game.objects.filter(name=game_name, the_round__tournament=t).get()
    except Game.DoesNotExist:
        raise Http404
    context = {'tournament': t, 'game': g, 'news': g.news()}
    return render(request, 'games/news.html', context)

def game_background(request, tournament_id, game_name):
    """Display background info for a game"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
        g = Game.objects.filter(name=game_name, the_round__tournament=t).get()
    except Game.DoesNotExist:
        raise Http404
    context = {'tournament': t, 'game': g, 'background': g.background()}
    return render(request, 'games/background.html', context)

def draw_vote(request, tournament_id, game_name):
    """Provide a form to enter a draw vote for a game"""
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
        g = Game.objects.filter(name=game_name, the_round__tournament=t).get()
    except Game.DoesNotExist:
        raise Http404
    form = DrawForm(request.POST or None, dias=g.is_dias())
    if form.is_valid():
        year = form.cleaned_data['year']
        try:
            countries = form.cleaned_data['powers']
        except KeyError:
            # Must be DIAS
            scs = g.centrecount_set.filter(year=year, count__gt=0)
            countries = [sc.power for sc in scs]

        # Create a dict from countries, to pass as kwargs
        kwargs = {}
        for i in range(0,len(countries)):
            kwargs['power_%d'%(i+1)] = countries[i]

        # Create the DrawProposal
        dp = DrawProposal(game=g,
                          year = year,
                          season=form.cleaned_data['season'],
                          passed=form.cleaned_data['passed'],
                          proposer=form.cleaned_data['proposer'],
                          **kwargs)
        dp.save()
        # TODO Redirect to somewhere that actually exists...
        return HttpResponseRedirect('/thanks/')

    return render_to_response('games/vote.html',
                              {'tournament': t,
                               'game': g,
                               'form' : form},
                              context_instance = RequestContext(request))

