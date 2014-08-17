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

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.views import generic
from django.forms.models import inlineformset_factory
from django import forms
from django.forms.formsets import formset_factory, BaseFormSet

from tournament.models import *

# TODO Merge these two forms ?
class DrawForm(forms.Form):
    """Form for a draw vote"""
    year = forms.IntegerField(min_value=FIRST_YEAR)
    season = forms.ChoiceField(choices=SEASONS)
    proposer = forms.ModelChoiceField(queryset=GreatPower.objects.all(),
                                      to_field_name='name')
    powers = forms.ModelMultipleChoiceField(queryset=GreatPower.objects.all(),
                                            to_field_name='name',
                                            widget=forms.SelectMultiple(attrs={'size':'7'}))
    passed = forms.BooleanField(initial=False, required=False)

class DiasDrawForm(forms.Form):
    """Form for a DIAS draw vote"""
    year = forms.IntegerField(min_value=FIRST_YEAR)
    season = forms.ChoiceField(choices=SEASONS)
    proposer = forms.ModelChoiceField(queryset=GreatPower.objects.all(),
                                      to_field_name='name')
    passed = forms.BooleanField(initial=False, required=False)

class GameScoreForm(forms.Form):
    """Form for score for a single game"""
    game_name = forms.CharField(label='Game Name', max_length=10)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one score field per Great Power"""
        super(GameScoreForm, self).__init__(*args, **kwargs)

        # No changing the game name !
        attrs = self.fields['game_name'].widget.attrs
        attrs['size'] = attrs['maxlength']
        attrs['readonly'] = 'readonly'

        # Create the right country fields
        for x,c in COUNTRIES:
            # Don't require a score for every player
            self.fields[c] = forms.FloatField(required=False)
            attrs = self.fields[c].widget.attrs
            attrs['size'] = 10
            attrs['maxlength'] = 10

class GamePlayersForm(forms.Form):
    """Form for players of a single game"""
    game_name = forms.CharField(label='Game Name', max_length=10)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one player field per Great Power"""
        # Remove our special kwarg from the list
        self.the_round = kwargs.pop('round')
        super(GamePlayersForm, self).__init__(*args, **kwargs)

        attrs = self.fields['game_name'].widget.attrs
        attrs['size'] = attrs['maxlength']

        queryset = the_round.roundplayer_set.all()

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            self.fields[c] = forms.ModelChoiceField(queryset)
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
        self.the_round = kwargs.pop('round')
        super(BaseGamePlayersForm, self).__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['round'] = self.the_round
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

class PlayerRoundForm(forms.Form):
    """Form to specify which rounds a player played in"""
    # TODO this should be probably every player in the tournament, not all of them
    player = forms.ModelChoiceField(queryset=Player.objects.all())

    def __init__(self, *args, **kwargs):
        # Remove our two special kwargs from the list
        self.rounds = kwargs.pop('rounds')
        self.this_round = kwargs.pop('this_round')
        super(PlayerRoundForm, self).__init__(*args, **kwargs)

        # Create the right number of round fields, with the right ones read-only
        for i in range(1, 1 + self.rounds):
            name = 'round_%d' % i
            readonly = (i < self.this_round)
            self.fields[name] = forms.BooleanField(initial=False)
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
        # Remove our two special kwargs from the list
        self.rounds = kwargs.pop('rounds')
        self.this_round = kwargs.pop('this_round')
        super(BasePlayerRoundFormset, self).__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the two special args down to the form itself
        kwargs['rounds'] = self.rounds
        kwargs['this_round'] = self.this_round
        return super(BasePlayerRoundFormset, self)._construct_form(index, **kwargs)

class PlayerRoundScoreForm(forms.Form):
    """Form to enter round score(s) for a player"""
    # TODO this should be probably every player in the tournament, not all of them
    player = forms.ModelChoiceField(queryset=Player.objects.all())

    def __init__(self, *args, **kwargs):
        # Remove our two special kwargs from the list
        self.rounds = kwargs.pop('rounds')
        self.this_round = kwargs.pop('this_round')
        super(PlayerRoundScoreForm, self).__init__(*args, **kwargs)

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
        # Remove our two special kwargs from the list
        self.rounds = kwargs.pop('rounds')
        self.this_round = kwargs.pop('this_round')
        super(BasePlayerRoundScoreFormset, self).__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the two special args down to the form itself
        kwargs['rounds'] = self.rounds
        kwargs['this_round'] = self.this_round
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

def tournament_scores(request, tournament_id):
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

def tournament_round(request, tournament_id):
    t = get_object_or_404(Tournament, pk=tournament_id)
    rds = t.round_set.order_by('number')
    for r in rds:
        if not r.is_finished():
            # This must be the "current round"
            context = {'round': r}
            return render(request, 'rounds/detail.html', context)
    # TODO There must be a better way than this
    return HttpResponse("No round currently being played")

def round_index(request, tournament_id):
    t = get_object_or_404(Tournament, pk=tournament_id)
    the_list = t.round_set.order_by('number')
    context = {'tournament': t, 'round_list': the_list}
    return render(request, 'rounds/index.html', context)

def round_detail(request, tournament_id, round_num):
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
	r = t.round_set.get(number=round_num)
    except Round.DoesNotExist:
	raise Http404
    context = {'round': r}
    return render(request, 'rounds/detail.html', context)

def round_scores(request, tournament_id, round_num):
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
	r = t.round_set.get(number=round_num)
    except Round.DoesNotExist:
	raise Http404
    rps = r.roundplayer_set.order_by('score')
    context = {'tournament': t, 'player_list': rps}
    # TODO Render actual scores
    return HttpResponse("This is the tournament %s round %s scores" % (tournament_id, round_num))

def roll_call(request, tournament_id, round_num):
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
	r = t.round_set.get(number=round_num)
    except Round.DoesNotExist:
	raise Http404
    rps = r.roundplayer_set.order_by('score')
    context = {'tournament': t, 'player_list': rps}
    # TODO Render actual scores
    return HttpResponse("This is the tournament %s round %s roll call" % (tournament_id, round_num))

def game_index(request, tournament_id, round_num):
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
	r = t.round_set.get(number=round_num)
    except Round.DoesNotExist:
	raise Http404
    the_list = r.game_set.order_by('name')
    context = {'round': r, 'game_list': the_list}
    return render(request, 'games/index.html', context)

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

def game_news(request, tournament_id, game_name):
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
        g = Game.objects.filter(name=game_name, the_round__tournament=t).get()
    except Game.DoesNotExist:
        raise Http404
    context = {'tournament': t, 'game': g}
    # TODO Render actual news
    return HttpResponse("This is the tournament %s game %s news" % (tournament_id, game_name))

def game_background(request, tournament_id, game_name):
    t = get_object_or_404(Tournament, pk=tournament_id)
    try:
        g = Game.objects.filter(name=game_name, the_round__tournament=t).get()
    except Game.DoesNotExist:
        raise Http404
    context = {'tournament': t, 'game': g}
    # TODO Render actual background
    return HttpResponse("This is the tournament %s game %s background" % (tournament_id, game_name))

