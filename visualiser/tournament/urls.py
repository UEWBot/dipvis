# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016 Chris Brand
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

from django.conf.urls import url, include

from tournament import views

round_patterns = [
    url(r'^$', views.round_detail, name='round_detail'),
    url(r'^create_games/$', views.create_games, name='create_games'),
    url(r'^game_scores/$', views.game_scores, name='game_scores'),
    url(r'^games/$', views.game_index, name='game_index'),
    url(r'^views/$', views.round_simple, {'template': 'view'}, name='round_views'),
]

game_patterns = [
    url(r'^$', views.game_detail, name='game_detail'),
    url(r'^sc_chart/$', views.game_sc_chart, name='game_sc_chart'),
    url(r'^sc_chart_refresh/$', views.game_sc_chart, {'refresh': True}, name='game_sc_chart_refresh'),
    url(r'^enter_scs/$', views.sc_counts, name='enter_scs'),
    # Always the latest position
    url(r'^positions/latest/$', views.game_image,
        {'turn': '', 'timelapse': True}, name='current_game_image'),
    # Fixed at the specified turn
    url(r'^positions/(?P<turn>\w+)/$', views.game_image, name='game_image'),
    # Cycle through all images, from S1901M
    url(r'^timelapse/$', views.game_image,
        {'turn': 'S1901M', 'timelapse': True}, name='game_timelapse'),
    # Same as either current_game_image or game_timelapse, depending on turn
    # This is the URL they both redirect to. Don't expect users to go there
    # TODO Begs the question of why not just use this one...
    url(r'^timelapse/(?P<turn>\w*)/$', views.game_image,
        {'timelapse': True}, name='game_image_seq'),
    url(r'^add_position/$', views.add_game_image, name='add_game_image'),
    url(r'^news/$', views.game_news, name='game_news'),
    url(r'^news_ticker/$', views.game_news, {'as_ticker': True}, name='game_news_ticker'),
    url(r'^background/$', views.game_background, name='game_background'),
    url(r'^background_ticker/$', views.game_background,
        {'as_ticker': True}, name='game_background_ticker'),
    url(r'^ticker/$', views.game_simple, {'template': 'ticker'}, name='game_ticker'),
    url(r'^draw_vote/$', views.draw_vote, name='draw_vote'),
    url(r'^views/$', views.game_simple, {'template': 'view'}, name='game_views'),
]

tournament_patterns = [
    url(r'^framesets/$', views.tournament_simple, {'template': 'frameset_picker'}, name='framesets'),
    url(r'^frameset_3x3/$', views.tournament_simple, {'template': 'frameset_3x3'}, name='frameset_3x3'),
    url(r'^frameset_top_board/$', views.tournament_simple, {'template': 'frameset_top_board'}, name='frameset_top_board'),
    url(r'^frameset_2x2/$', views.tournament_simple, {'template': 'frameset_2x2'}, name='frameset_2x2'),
    url(r'^frameset_1x1/$', views.tournament_simple, {'template': 'frameset_1x1'}, name='frameset_1x1'),
    url(r'^views/$', views.tournament_simple, {'template': 'view'}, name='tournament_views'),
    url(r'^scores/$', views.tournament_scores, name='tournament_scores'),
    url(r'^scores_refresh/$', views.tournament_scores, {'refresh': True}, name='tournament_scores_refresh'),
    url(r'^enter_scores/$', views.round_scores, name='enter_scores'),
    url(r'^roll_call/$', views.roll_call, name='roll_call'),
    url(r'^current_round/$', views.tournament_round, name='tournament_round'),
    url(r'^game_image/$', views.add_game_image, name='add_game_image'),
    url(r'^news/$', views.tournament_news, name='tournament_news'),
    url(r'^news_ticker/$', views.tournament_news, {'as_ticker': True}, name='tournament_news_ticker'),
    url(r'^background/$', views.tournament_background, name='tournament_background'),
    url(r'^ticker/$', views.tournament_simple, {'template': 'ticker'}, name='tournament_ticker'),
    url(r'^background_ticker/$', views.tournament_background,
        {'as_ticker': True}, name='tournament_background_ticker'),
    url(r'^rounds/$', views.round_index, name='round_index'),
    url(r'^rounds/(?P<round_num>\d+)/', include(round_patterns)),
    url(r'^games/(?P<game_name>\w+)/', include(game_patterns)),
]

urlpatterns = [
    url(r'^$', views.tournament_index, name='index'),
    url(r'^(?P<tournament_id>\d+)/$', views.tournament_simple, {'template': 'detail'}, name='tournament_detail'),
    url(r'^(?P<tournament_id>\d+)/', include(tournament_patterns)),
]
