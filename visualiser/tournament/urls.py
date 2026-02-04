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

from django.urls import path, include, register_converter

from tournament import game_views
from tournament import round_views
from tournament import series_views
from tournament import tournament_views
from tournament import tournament_player_views
from tournament import wdd_views
from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR

class YearConverter:
    """URL converter for a game year (int)"""
    regex = r'[0-9]{4,}'

    def to_python(self, value):
        val = int(value)
        if val < FIRST_YEAR:
            raise ValueError
        return val

    def to_url(self, value):
        return f'{value}'

register_converter(YearConverter, 'year')


class TurnConverter:
    """URL converter for a game phase (e.g. S1901M) (str)"""
    regex = r'[SF][0-9]+[MRA]'

    def to_python(self, value):
        val = int(value[1:-1])
        if val < FIRST_YEAR:
            raise ValueError
        # Adjustments only happen in Fall
        if (value[0] == 'S') and (value[-1] == 'A'):
            raise ValueError
        return value

    def to_url(self, value):
        return f'{value}'

register_converter(TurnConverter, 'turn')


round_patterns = [
    path('', round_views.round_simple,
         {'template': 'detail'}, name='round_detail'),
    path('roll_call/', round_views.roll_call, name='round_roll_call'),
    path('populate_pools/', round_views.populate_pools, name='populate_pools'),
    path('get_seven/', round_views.get_seven, name='get_seven'),
    path('seed_games/', round_views.seed_games, name='seed_games'),
    path('create_games/', round_views.create_games, name='create_games'),
    path('create_games/<slug:pool_slug>/', round_views.create_games,
         name='create_games_in_pool'),
    path('game_scores/', round_views.game_scores, name='game_scores'),
    path('games/', round_views.game_index, name='game_index'),
    path('board_call_csv/', round_views.board_call_csv, name='board_call_csv'),
    path('board_call/', round_views.round_simple,
         {'template': 'board_call'}, name='board_call'),
    path('sc_graphs/', round_views.game_cycle,
         {'template': 'games/sc_graph.html'}, name='round_sc_graphs'),
    path('sc_graphs/<str:game_name>/', round_views.game_cycle,
         {'template': 'games/sc_graph.html'}, name='round_sc_graphs_from_game'),
]

game_patterns = [
    path('', game_views.game_simple,
         {'template': 'detail'}, name='game_detail'),
    path('change_game/', game_views.change_game, name='change_game'),
    path('sc_chart/', game_views.game_sc_chart, name='game_sc_chart'),
    path('sc_chart_refresh/', game_views.game_sc_chart,
         {'refresh': True}, name='game_sc_chart_refresh'),
    # This is just the graph image
    path('graph/', game_views.graph, name='graph_img_scs'),
    # This is the page showing the graph
    path('sc_graph/', game_views.game_sc_graph, name='game_sc_graph'),
    path('sc_graph_refresh/', game_views.game_sc_graph,
         {'refresh': True}, name='game_sc_graph_refresh'),
    path('enter_scs/', game_views.sc_counts, name='enter_scs'),
    path('sc_owners/', game_views.game_sc_owners, name='game_sc_owners'),
    path('sc_owners_refresh/', game_views.game_sc_owners,
         {'refresh': True}, name='game_sc_owners_refresh'),
    path('enter_sc_owners/', game_views.sc_owners, name='enter_sc_owners'),
    # Always the latest position
    path('positions/latest/', game_views.game_image,
         {'turn': '', 'timelapse': True, 'redirect_url_name': 'current_game_image'},
         name='current_game_image'),
    # Fixed at the specified turn
    path('positions/<turn:turn>/', game_views.game_image, name='game_image'),
    # Cycle through all images, from S1901M
    path('timelapse/', game_views.game_image,
         {'turn': 'S1901M', 'timelapse': True}, name='game_timelapse'),
    # Same as either current_game_image or game_timelapse, depending on turn
    # This is the URL they both redirect to. Don't expect users to go there
    # TODO Begs the question of why not just use this one...
    path('timelapse/<turn:turn>/', game_views.game_image,
         {'timelapse': True}, name='game_image_seq'),
    path('add_position/', game_views.add_game_image, name='add_game_image'),
    path('news/', game_views.game_news, name='game_news'),
    path('news/<year:for_year>/', game_views.game_news,
         name='game_news_for_year'),
    path('news_ticker/', game_views.game_news,
         {'as_ticker': True}, name='game_news_ticker'),
    path('background/', game_views.game_background, name='game_background'),
    path('background_ticker/', game_views.game_background,
         {'as_ticker': True}, name='game_background_ticker'),
    path('ticker/', game_views.game_simple,
         {'template': 'ticker'}, name='game_ticker'),
    path('draw_vote/', game_views.draw_vote,
         {'concession': False}, name='draw_vote'),
    path('concession/', game_views.draw_vote,
         {'concession': True}, name='concession'),
    path('views/', game_views.game_simple,
         {'template': 'view'}, name='game_views'),
    # These three go together as a cycle
    path('overview/', game_views.game_sc_chart,
         {'refresh': True, 'redirect_url_name': 'game_overview_2'},
         name='game_overview'),
    path('overview2/', game_views.game_sc_owners,
         {'refresh': True, 'redirect_url_name': 'game_overview_3'},
         name='game_overview_2'),
    path('overview3/', game_views.game_sc_graph,
         {'refresh': True, 'redirect_url_name': 'game_overview_4'},
         name='game_overview_3'),
    path('overview4/', game_views.game_image,
         {'timelapse': True, 'redirect_url_name': 'game_overview'},
         name='game_overview_4'),
    path('scrape_backstabbr/', game_views.scrape_external_site,
         name='scrape_external_site'),
    path('aar/<int:player_id>/', game_views.aar,
         name='aar'),
]

tp_patterns = [
    path('', tournament_player_views.index,
         name='tournament_players'),
    path('payments/', tournament_player_views.payments,
         name='tournament_player_payments'),
    path('<int:tp_id>/', tournament_player_views.detail,
         name='tournament_player_detail'),
]

series_patterns = [
    path('', series_views.SeriesIndexView.as_view(), name='series_index'),
    path('<slug:slug>/', series_views.SeriesDetailView.as_view(),
         name='series_detail'),
    path('<slug:slug>/players/', series_views.series_players,
         name='series_players'),
    path('<slug:slug>/players_vftf/', series_views.series_players,
         {'include_ftf': False}, name='series_players_vftf'),
    path('<slug:slug>/players_ftf/', series_views.series_players,
         {'include_vftf': False}, name='series_players_ftf'),
]

tournament_patterns = [
    path('', tournament_views.tournament_simple,
         {'template': 'detail'}, name='tournament_detail'),
    path('framesets/', tournament_views.tournament_simple,
         {'template': 'frameset_picker'}, name='framesets'),
    path('frameset_3x3/', tournament_views.tournament_simple,
         {'template': 'frameset_3x3'}, name='frameset_3x3'),
    path('frameset_top_board/', tournament_views.tournament_simple,
         {'template': 'frameset_top_board'}, name='frameset_top_board'),
    path('frameset_3_games/', tournament_views.tournament_simple,
         {'template': 'frameset_3_games'}, name='frameset_3_games'),
    path('frameset_2_games/', tournament_views.tournament_simple,
         {'template': 'frameset_2_games'}, name='frameset_2_games'),
    path('frameset_2x2/', tournament_views.tournament_simple,
         {'template': 'frameset_2x2'}, name='frameset_2x2'),
    path('frameset_1x1/', tournament_views.tournament_simple,
         {'template': 'frameset_1x1'}, name='frameset_1x1'),
    path('views/', tournament_views.tournament_simple,
         {'template': 'view'}, name='tournament_views'),
    # These three go together as a cycle
    path('overview/', tournament_views.tournament_scores,
         {'refresh': True, 'redirect_url_name': 'tournament_overview_2'},
         name='tournament_overview'),
    path('overview2/', tournament_views.tournament_game_results,
         {'refresh': True, 'redirect_url_name': 'tournament_overview_3'},
         name='tournament_overview_2'),
    path('overview3/', tournament_views.tournament_best_countries,
         {'refresh': True, 'redirect_url_name': 'tournament_overview_4'},
         name='tournament_overview_3'),
    path('overview4/', tournament_views.team_scores,
         {'refresh': True, 'redirect_url_name': 'tournament_overview'},
         name='tournament_overview_4'),
    path('scores/', tournament_views.tournament_scores, name='tournament_scores'),
    path('scores_refresh/', tournament_views.tournament_scores,
         {'refresh': True}, name='tournament_scores_refresh'),
    path('team_scores/', tournament_views.team_scores, name='team_scores'),
    path('team_scores_refresh/', tournament_views.team_scores,
         {'refresh': True}, name='team_scores_refresh'),
    # This is just the graph image
    path('graph/', tournament_views.graph, name='graph_img_score'),
    # This is the page showing the graph
    path('score_graph/', tournament_views.tournament_score_graph,
         name='tournament_score_graph'),
    path('score_graph_refresh/', tournament_views.tournament_score_graph,
         {'refresh': True}, name='tournament_score_graph_refresh'),
    path('game_results/', tournament_views.tournament_game_results,
         name='tournament_game_results'),
    path('game_results_refresh/', tournament_views.tournament_game_results,
         {'refresh': True}, name='tournament_game_results_refresh'),
    path('best_countries/', tournament_views.tournament_best_countries,
         name='tournament_best_countries'),
    path('best_countries_refresh/', tournament_views.tournament_best_countries,
         {'refresh': True}, name='tournament_best_countries_refresh'),
    path('game_links/', tournament_views.tournament_simple,
         {'template': 'game_links'}, name='tournament_game_links'),
    path('enter_scores/', tournament_views.enter_scores, name='enter_scores'),
    path('self_check_in/', tournament_views.self_check_in_control,
         name='self_check_in_control'),
    path('current_round/', tournament_views.tournament_round, name='tournament_round'),
    # This uses the default empty game name
    path('game_image/', game_views.add_game_image, name='add_any_game_image'),
    path('news/', tournament_views.tournament_news, name='tournament_news'),
    path('news_ticker/', tournament_views.tournament_news,
         {'as_ticker': True}, name='tournament_news_ticker'),
    path('background/', tournament_views.tournament_background,
         name='tournament_background'),
    path('ticker/', tournament_views.tournament_simple,
         {'template': 'ticker'}, name='tournament_ticker'),
    path('background_ticker/', tournament_views.tournament_background,
         {'as_ticker': True}, name='tournament_background_ticker'),
    path('rounds/', tournament_views.round_index, name='round_index'),
    path('csv_classification/', wdd_views.view_classification_csv,
         name='csv_classification'),
    path('csv_boards/', wdd_views.view_boards_csv, name='csv_boards'),
    path('prefs/', tournament_views.enter_prefs, name='enter_prefs'),
    path('upload_prefs/', tournament_views.upload_prefs, name='upload_prefs'),
    path('prefs_csv/', tournament_views.prefs_csv, name='prefs_csv'),
    path('seeder_bias/', tournament_views.seeder_bias, name='seeder_bias'),
    path('player_prefs/<uuid:uuid>/', tournament_player_views.player_prefs,
         name='player_prefs'),
    path('awards/', tournament_views.tournament_simple,
         {'template': 'awards', 'context': {'numbered_list': False}},
         name='tournament_awards'),
    path('wdd_awards/', tournament_views.tournament_simple,
         {'template': 'awards', 'context': {'numbered_list': True}},
         name='tournament_wdd_awards'),
    path('enter_awards/', tournament_views.enter_awards, name='enter_awards'),
    path('handicaps/', tournament_views.enter_handicaps, name='enter_handicaps'),
    path('teams/', tournament_views.teams, name='teams'),
    path('enter_teams/', tournament_views.enter_teams, name='enter_teams'),
    path('players/', include(tp_patterns)),
    path('rounds/<int:round_num>/', include(round_patterns)),
    path('games/<str:game_name>/', include(game_patterns)),
]

api_patterns = [
    path('tournament/<int:tournament_id>/', tournament_views.api,
         name='api_tournament'),
    path('tournament/<int:tournament_id>/game/<str:game_name>/', game_views.api,
         name='api_game'),
]

urlpatterns = [
    path('', tournament_views.tournament_index, name='index'),
    path('series/', include(series_patterns)),
    path('api/v<int:version>/', include(api_patterns)),
    path('<int:tournament_id>/', include(tournament_patterns)),
]
