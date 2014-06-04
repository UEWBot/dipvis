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

from tournament.models import Tournament, Round, Game

def index(request):
    the_list = Tournament.objects.order_by('-start_date')
    context = {'tournament_list': the_list}
    return render(request, 'tournaments/index.html', context)

def tournament_detail(request, tournament_id):
    t = get_object_or_404(Tournament, pk=tournament_id)
    return render(request, 'tournaments/detail.html', {'tournament': t})

def tournament_scores(request, tournament_id):
    t = get_object_or_404(Tournament, pk=tournament_id)
    tps = t.tournamentplayer_set.order_by('-score')
    return render(request, 'tournaments/scores.html', {'tournament': t, 'player_set': tps})

def tournament_round(request, tournament_id):
    return HttpResponse("This is the tournament %s current round" % tournament_id)

def round_index(request, tournament_id):
    the_list = Tournament.objects.order_by('-start_date')
    context = {'round_list': the_list}
    return render(request, 'rounds/index.html', context)

def round_detail(request, tournament_id, round_num):
    return HttpResponse("This is the tournament %s round %s detail" % (tournament_id, round_num))

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

