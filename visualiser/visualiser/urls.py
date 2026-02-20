# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2017, 2019-2020 Chris Brand
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

from django.contrib import admin
from django.urls import include, path, register_converter

from tournament import (backstabbr_views, game_scoring_system_views,
                        player_views)

admin.autodiscover()


class BackstabbrTypeConverter:
    """Converter for the backstabbr game type (sandbox/game) part of a URL"""
    regex = r'game|sandbox'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(BackstabbrTypeConverter, 'bs_type')


backstabbr_patterns = [
    # This is just the graph image
    path('graph/<bs_type:game_type>/<int:game_number>/', backstabbr_views.graph,
         name='graph_img_bs'),
    # This is the page showing the graph
    path('sc_graph/game/<int:game_number>/', backstabbr_views.game_sc_graph,
         {'sandbox': False}, name='game_sc_graph'),
    path('sc_graph/sandbox/<int:game_number>/', backstabbr_views.game_sc_graph,
         {'sandbox': True}, name='sandbox_sc_graph'),
    path('sc_graph/enter_url/', backstabbr_views.url_form, name='enter_url'),
]

game_scoring_patterns = [
    path('', game_scoring_system_views.game_scoring_index,
         name='game_scoring_index'),
    path('<slug:slug>/', game_scoring_system_views.game_scoring_detail,
         name='game_scoring_detail'),
]

player_patterns = [
    path('', player_views.PlayerIndexView.as_view(),
         name='player_index'),
    path('<int:pk>/', player_views.player_detail,
         name='player_detail'),
    path('<int:pk1>/<int:pk2>/', player_views.player_versus,
         name='player_versus'),
    path('upload_players/', player_views.upload_players,
         name='upload_players'),
    path('<int:pk>/wep7/', player_views.wpe,
         {'years': 7, 'count': 7}, name='wep7'),
]

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('backstabbr/', include(backstabbr_patterns)),
    path('game_scoring/', include(game_scoring_patterns)),
    path('players/', include(player_patterns)),
    path('tournaments/', include('tournament.urls')),
]
