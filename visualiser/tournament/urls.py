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

from tournament import tournament_views
from tournament import round_views
from tournament import game_views
from tournament import wdd_views

round_patterns = [
    url(r'^$', round_views.round_simple,
        {'template': 'detail'}, name='round_detail'),
    url(r'^create_games/$', round_views.create_games, name='create_games'),
    url(r'^get_seven/$', round_views.get_seven, name='get_seven'),
    url(r'^seed_games/$', round_views.seed_games, name='seed_games'),
    url(r'^game_scores/$', round_views.game_scores, name='game_scores'),
    url(r'^games/$', round_views.game_index, name='game_index'),
    url(r'^roll_call/$', round_views.roll_call, name='round_roll_call'),
]

game_patterns = [
    url(r'^$', game_views.game_simple,
        {'template': 'detail'}, name='game_detail'),
    url(r'^sc_chart/$', game_views.game_sc_chart, name='game_sc_chart'),
    url(r'^sc_chart_refresh/$', game_views.game_sc_chart,
        {'refresh': True}, name='game_sc_chart_refresh'),
    url(r'^enter_scs/$', game_views.sc_counts, name='enter_scs'),
    url(r'^sc_owners/$', game_views.game_sc_owners, name='game_sc_owners'),
    url(r'^sc_owners_refresh/$', game_views.game_sc_owners,
        {'refresh': True}, name='game_sc_owners_refresh'),
    url(r'^enter_sc_owners/$', game_views.sc_owners, name='enter_sc_owners'),
    # Always the latest position
    url(r'^positions/latest/$', game_views.game_image,
        {'turn': '', 'timelapse': True}, name='current_game_image'),
    # Fixed at the specified turn
    url(r'^positions/(?P<turn>\w+)/$', game_views.game_image, name='game_image'),
    # Cycle through all images, from S1901M
    url(r'^timelapse/$', game_views.game_image,
        {'turn': 'S1901M', 'timelapse': True}, name='game_timelapse'),
    # Same as either current_game_image or game_timelapse, depending on turn
    # This is the URL they both redirect to. Don't expect users to go there
    # TODO Begs the question of why not just use this one...
    url(r'^timelapse/(?P<turn>\w*)/$', game_views.game_image,
        {'timelapse': True}, name='game_image_seq'),
    url(r'^add_position/$', game_views.add_game_image, name='add_game_image'),
    url(r'^news/$', game_views.game_news, name='game_news'),
    url(r'^news_ticker/$', game_views.game_news,
        {'as_ticker': True}, name='game_news_ticker'),
    url(r'^background/$', game_views.game_background, name='game_background'),
    url(r'^background_ticker/$', game_views.game_background,
        {'as_ticker': True}, name='game_background_ticker'),
    url(r'^ticker/$', game_views.game_simple,
        {'template': 'ticker'}, name='game_ticker'),
    url(r'^draw_vote/$', game_views.draw_vote, name='draw_vote'),
    url(r'^views/$', game_views.game_simple,
        {'template': 'view'}, name='game_views'),
    # These three go together as a cycle
    url(r'^overview/$', game_views.game_sc_chart,
        {'refresh': True, 'redirect_url_name': 'game_overview_2'},
        name='game_overview'),
    url(r'^overview2/$', game_views.game_sc_owners,
        {'refresh': True, 'redirect_url_name': 'game_overview_3'},
        name='game_overview_2'),
    url(r'^overview3/$', game_views.game_image,
        {'timelapse': True, 'redirect_url_name': 'game_overview'},
        name='game_overview_3'),
]

tournament_patterns = [
    url(r'^$', tournament_views.tournament_simple,
        {'template': 'detail'}, name='tournament_detail'),
    url(r'^framesets/$', tournament_views.tournament_simple,
        {'template': 'frameset_picker'}, name='framesets'),
    url(r'^frameset_3x3/$', tournament_views.tournament_simple,
        {'template': 'frameset_3x3'}, name='frameset_3x3'),
    url(r'^frameset_top_board/$', tournament_views.tournament_simple,
        {'template': 'frameset_top_board'}, name='frameset_top_board'),
    url(r'^frameset_2x2/$', tournament_views.tournament_simple,
        {'template': 'frameset_2x2'}, name='frameset_2x2'),
    url(r'^frameset_1x1/$', tournament_views.tournament_simple,
        {'template': 'frameset_1x1'}, name='frameset_1x1'),
    url(r'^views/$', tournament_views.tournament_simple,
        {'template': 'view'}, name='tournament_views'),
    # These three go together as a cycle
    url(r'^overview/$', tournament_views.tournament_scores,
        {'refresh': True, 'redirect_url_name': 'tournament_overview_2'},
        name='tournament_overview'),
    url(r'^overview2/$', tournament_views.tournament_game_results,
        {'refresh': True, 'redirect_url_name': 'tournament_overview_3'},
        name='tournament_overview_2'),
    url(r'^overview3/$', tournament_views.tournament_best_countries,
        {'refresh': True, 'redirect_url_name': 'tournament_overview'},
        name='tournament_overview_3'),
    url(r'^scores/$', tournament_views.tournament_scores, name='tournament_scores'),
    url(r'^scores_refresh/$', tournament_views.tournament_scores,
        {'refresh': True}, name='tournament_scores_refresh'),
    url(r'^game_results/$', tournament_views.tournament_game_results,
        name='tournament_game_results'),
    url(r'^game_results_refresh/$', tournament_views.tournament_game_results,
        {'refresh': True}, name='tournament_game_results_refresh'),
    url(r'^best_countries/$', tournament_views.tournament_best_countries,
        name='tournament_best_countries'),
    url(r'^best_countries_refresh/$', tournament_views.tournament_best_countries,
        {'refresh': True}, name='tournament_best_countries_refresh'),
    url(r'^enter_scores/$', tournament_views.round_scores, name='enter_scores'),
    url(r'^roll_call/$', round_views.roll_call, name='roll_call'),
    url(r'^current_round/$', tournament_views.tournament_round, name='tournament_round'),
    # TODO Why does this one calls into game_views ?
    url(r'^game_image/$', game_views.add_game_image, name='add_game_image'),
    url(r'^news/$', tournament_views.tournament_news, name='tournament_news'),
    url(r'^news_ticker/$', tournament_views.tournament_news,
        {'as_ticker': True}, name='tournament_news_ticker'),
    url(r'^background/$', tournament_views.tournament_background,
        name='tournament_background'),
    url(r'^ticker/$', tournament_views.tournament_simple,
        {'template': 'ticker'}, name='tournament_ticker'),
    url(r'^background_ticker/$', tournament_views.tournament_background,
        {'as_ticker': True}, name='tournament_background_ticker'),
    url(r'^rounds/$', tournament_views.round_index, name='round_index'),
    url(r'^csv_classification/$', wdd_views.view_classification_csv,
        name='csv_classification'),
    url(r'^csv_boards/$', wdd_views.view_boards_csv, name='csv_boards'),
    url(r'^prefs/$', tournament_views.enter_prefs, name='enter_prefs'),
    url(r'^upload_prefs/$', tournament_views.upload_prefs, name='upload_prefs'),
    url(r'^prefs_csv/$', tournament_views.prefs_csv, name='prefs_csv'),
    url(r'^player_prefs/(?P<uuid>[^/]+)/$', tournament_views.player_prefs,
        name='player_prefs'),
    url(r'^rounds/(?P<round_num>\d+)/', include(round_patterns)),
    url(r'^games/(?P<game_name>\w+)/', include(game_patterns)),
]

urlpatterns = [
    url(r'^$', tournament_views.tournament_index, name='index'),
    url(r'^(?P<tournament_id>\d+)/', include(tournament_patterns)),
]
