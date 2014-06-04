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

from django.conf.urls import patterns, url

from tournament import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^(?P<tournament_id>\d+)/$', views.tournament_detail, name='tournament_detail'),
    url(r'^(?P<tournament_id>\d+)/scores/$', views.tournament_scores, name='tournament_scores'),
    url(r'^(?P<tournament_id>\d+)/current_round/$', views.tournament_round, name='tournament_round'),
    url(r'^(?P<tournament_id>\d+)/round/$', views.round_index, name='round_index'),
    url(r'^(?P<tournament_id>\d+)/round/(?P<round_num>\d+)/$', views.round_detail, name='round_detail'),
    url(r'^(?P<tournament_id>\d+)/round/(?P<round_num>\d+)/scores/$', views.round_scores, name='round_scores'),
    url(r'^(?P<tournament_id>\d+)/round/(?P<round_num>\d+)/games/$', views.game_index, name='game_index'),
    url(r'^(?P<tournament_id>\d+)/game/(?P<game_name>\d+)/$', views.game_detail, name='game_detail'),
    url(r'^(?P<tournament_id>\d+)/game/(?P<game_name>\d+)/sc_chart/$', views.game_sc_chart, name='game_sc_chart'),
    url(r'^(?P<tournament_id>\d+)/game/(?P<game_name>\d+)/news/$', views.game_news, name='game_news'),
    url(r'^(?P<tournament_id>\d+)/game/(?P<game_name>\d+)/background/$', views.game_background, name='game_background'),
)
