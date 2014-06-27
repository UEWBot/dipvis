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

from tournament.models import Tournament, Round, Game, CentreCount, GreatPower

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
    # TODO massage ps so we have one entry per power
    players = g.players()
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
        neutrals = 34
        yscs = scs.filter(year=year)
        row = []
        row.append(year)
        for power in powers:
            sc = yscs.filter(power=power).get()
            row.append(sc.count)
            neutrals -= sc.count
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

