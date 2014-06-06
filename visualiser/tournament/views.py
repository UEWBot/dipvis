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
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.views import generic

from tournament.models import Tournament, Round, Game

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
    return render(request, 'tournaments/scores.html', {'tournament': t, 'scores': scores, 'rounds': rounds})

def tournament_round(request, tournament_id):
    t = get_object_or_404(Tournament, pk=tournament_id)
    rds = t.round_set.order_by('number')
    for r in rds:
        if not r.is_finished():
            # This must be the "current round"
            return render(request, 'rounds/detail.html', {'round': r})
    return HttpResponse("No rounds currently being played")

def round_index(request, tournament_id):
    t = get_object_or_404(Tournament, pk=tournament_id)
    the_list = t.round_set.order_by('number')
    context = {'tournament': t, 'round_list': the_list}
    return render(request, 'rounds/index.html', context)

def round_detail(request, tournament_id, round_num):
    t = get_object_or_404(Tournament, pk=tournament_id)
    r = t.round_set.get(number=round_num)
    return render(request, 'rounds/detail.html', {'round': r})

def round_scores(request, tournament_id, round_num):
    return HttpResponse("This is the tournament %s round %s scores" % (tournament_id, round_num))

def game_index(request, tournament_id, round_num):
    return HttpResponse("This is the tournament %s round %s game index" % (tournament_id, round_num))

def game_detail(request, tournament_id, game_name):
    return HttpResponse("This is the tournament %s game %s detail" % (tournament_id, game_name))

def game_sc_chart(request, tournament_id, game_name):
    return HttpResponse("This is the tournament %s game %s sc_chart" % (tournament_id, game_name))

def game_news(request, tournament_id, game_name):
    return HttpResponse("This is the tournament %s game %s news" % (tournament_id, game_name))

def game_background(request, tournament_id, game_name):
    return HttpResponse("This is the tournament %s game %s background" % (tournament_id, game_name))

