# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2026 Chris Brand
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

# This file contains code related to Diplomacy players themselves.
# This is predominantly the Player class, but also the various classes
# used to cache background information about players' Diplomacy
# tournament history.

"""
This module provides classes to describe Diplomacy players.

Most of the code is dedicated to storing background information
about a player and retrieving it as needed.
"""

import datetime
import traceback

from django_countries.fields import Country

from tournament.diplomacy import GreatPower
from tournament.wdd import (UnrecognisedCountry, wdd_nation_to_country,
                            wdd_url_to_tournament_id)
from tournament.wdr import wdr_power_name_to_greatpower

from .event_kinds import EventKinds
from .player_award import PlayerAward
from .player_game_result import PlayerGameResult
from .player_ranking import PlayerRanking
from .player_title import PlayerTitle
from .player_event_ranking import PlayerEventRanking
from .wdr_background import WDRBackground, WDRNotAccessible
from .wikipedia_background import WikipediaBackground


TITLE_MAP = {
    'World Champion': 1,
    'Champion': 1,
    'North American Champion': 1,
    'Diplomat of the Year': 1,
    'Winner': 1,
    'European Champion': 1,
    'Online Champion': 1,
    'APAC Champion': 1,
    'Second': 2,
    'Third': 3,
    'Runners-up': 2,
}


def _update_or_create_playertitle_wiki(player, title):
    """
    Creates or updates a PlayerTitle for the player

    Given a Player and a dict with 'Tournament' and 'Year' keys,
    and optional 'Champion' key, representing the Wikipedia page,
    create or update a PlayerTitle
    """
    the_title = None
    for key, val in TITLE_MAP.items():
        try:
            if title[key] == str(player):
                if key == 'Champion':
                    the_title = f'{title["Tournament"]} Champion'
                elif key == 'Diplomat of the Year':
                    the_title = 'DBNI Diplomat of the Year'
                elif key == 'Winner':
                    the_title = f'{title["Tournament"]} Winner'
                elif 'Champion' in key:
                    the_title = key
                break
        except KeyError:
            pass
    if the_title:
        try:
            # ranking is left unset
            PlayerTitle.objects.update_or_create(player=player,
                                                 title=the_title,
                                                 year=title['Year'])
        except Exception:
            # Handle all exceptions
            # This way, we fail to add/update the single title rather than all the background
            print('Failed to save PlayerTitle')
            print(f'player={str(player)}, title={the_title}, year={title["Year"]}')
            traceback.print_exc()


def _split_wdd_game_name(name):
    """
    Extracts the round number and game number from a WDD game name.

    Returns a (round_number, game_number) 2-tuple.

    Obsolete - only retained for old migrations.
    """
    # Format is "R n B m" or "R / B"
    parts = name.split()
    if (len(parts) == 4) and (parts[0] == 'R') and (parts[2] == 'B'):
        return parts[1], parts[-1]
    elif (len(parts) == 3) and (parts[1] == '/'):
        return parts[0], parts[-1]
    raise ValueError(name)


WDR_EVENT_TYPE_MAP = {
    "Circuit": EventKinds.CIRCUIT,
    "League": EventKinds.LEAGUE,
    "Tournament": EventKinds.TOURNAMENT,
}


def _classify_wdr_tournament_kind(kind):
    """
    Classify a raw WDR tournament_event_type string into an EventKinds choice.
    """
    if not kind:
        return EventKinds.OTHER
    return WDR_EVENT_TYPE_MAP[kind]


def _update_or_create_event_ranking(player, lookup, defaults):
    """Update by source id, but reconcile rows that already match the DB unique key."""
    try:
        ptr = PlayerEventRanking.objects.get(player=player,
                                             event_name=defaults['event_name'],
                                             date=defaults['date'])
    except PlayerEventRanking.DoesNotExist:
        return PlayerEventRanking.objects.update_or_create(player=player,
                                                           **lookup,
                                                           defaults=defaults)
    for key, value in {**lookup, **defaults}.items():
        setattr(ptr, key, value)
    ptr.save()
    return ptr, False


def _add_player_bg_from_wdr(player, wdr_id):
    """
    Add or update player background information from the WDR

    Returns a list of Player fields that were updated and need saving.
    """
    fields = []
    bg = WDRBackground(wdr_id)
    rankings_by_wdr_tournament_id = {}
    # Podium finishes and Tournaments
    tournaments = bg.tournaments()
    for t in tournaments:
        event_date = t['tournament_end_date'] or t['tournament_start_date']
        if not event_date:
            print(f"Skipping {t['tournament_name']} for {player} with no date")
            continue
        event_kind = _classify_wdr_tournament_kind(t.get('tournament_event_type'))
        defaults = {'event_kind': event_kind,
                    'position': t['tournament_player_rank'] if t['tournament_player_rank'] and t['tournament_player_rank'] > 0 else None,
                    'event_name': t['tournament_name'],
                    'tournament_kind': t.get('tournament_kind')}
        defaults['date'] = event_date
        if t['tournament_wdd_id'] == -1:
            try:
                ptr, _ = _update_or_create_event_ranking(player,
                                                         {'wdr_tournament_id': t['tournament_id']},
                                                         defaults)
                rankings_by_wdr_tournament_id[t['tournament_id']] = ptr
            except Exception:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print('Failed to save PlayerEventRanking')
                print(f'player={str(player)}, event_kind={event_kind}, wdr_tournament_id={t["tournament_id"]}, defaults={defaults}')
                traceback.print_exc()
        else:
            defaults['wdr_tournament_id'] = t['tournament_id']
            try:
                # Note that WDD distinguishes tournaments and circuits, so the same id may identify one of each
                ptr, _ = _update_or_create_event_ranking(player,
                                                         {'event_kind': event_kind,
                                                          'wdd_tournament_id': t['tournament_wdd_id']},
                                                         defaults)
                rankings_by_wdr_tournament_id[t['tournament_id']] = ptr
            except Exception:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print('Failed to save PlayerEventRanking')
                print(f'player={str(player)}, event_kind={event_kind}, wdd_tournament_id={t["tournament_wdd_id"]}, defaults={defaults}')
                traceback.print_exc()
    # Boards
    for b in bg.boards():
        # Skip variant boards because they don't factor well into the statistics
        if b['board_variant'] not in ['Classic', 'Standard (7)', 'Standard']:
            print(f'Skipping board with variant {b["board_variant"]}')
            continue
        # What was the tournament?
        t_id = b['board_tournament']
        event_ranking = rankings_by_wdr_tournament_id.get(t_id)
        if event_ranking is None:
            continue
        defaults = {'position': b['board_rank'],
                    'is_top_board': bool(b.get('board_is_top'))}
        if not b['board_rank']:
            # This seems like a bug in WDR, but sometimes we don't get a rank
            print(f"No board_rank in board {b}")
            continue
        # Ignore any of these that aren't present
        if b['board_score']:
            defaults['score'] = b['board_score']
        if b['board_centers'] and (b['board_centers'] != -1):
            defaults['final_sc_count'] = b['board_centers']
        if b['board_year_of_elimination']:
            defaults['year_eliminated'] = b['board_year_of_elimination']
        try:
            PlayerGameResult.objects.update_or_create(event_ranking=event_ranking,
                                                      round_number=b['board_round'],
                                                      game_number=b['board_number'],
                                                      player=player,
                                                      power=wdr_power_name_to_greatpower(b['board_power']),
                                                      defaults=defaults)
        except Exception:
            # Handle all exceptions
            # This way, we fail to add/update the single ranking rather than all the background
            print('Failed to save PlayerGameResult')
            print(f'player={str(player)}, event_name={event_ranking.event_name}, round_number={b["board_round"]}, game_number={b["board_number"]}, power={b["board_power"]}, defaults={defaults}')
            traceback.print_exc()
    # Awards
    for a in bg.awards():
        # WDR only stores best country awards at present
        award_name = f'Best {a["award_country"]}'
        # What was the tournament?
        t_id = a['award_tournament']
        event_ranking = rankings_by_wdr_tournament_id.get(t_id)
        if event_ranking is None:
            continue
        try:
            PlayerAward.objects.update_or_create(event_ranking=event_ranking,
                                                 player=player,
                                                 name=award_name,
                                                 power=wdr_power_name_to_greatpower(a['award_country']))
        except Exception:
            # Handle all exceptions
            # This way, we fail to add/update the single ranking rather than all the background
            print('Failed to save PlayerAward')
            print(f'player={str(player)}, event_name={event_ranking.event_name}, date={event_ranking.date}, name={award_name}')
            traceback.print_exc()
    # WPE scores (and other Rankings)
    ranks = bg.rankings()
    for k, v in ranks.items():
        if not v['score']:
            continue
        try:
            PlayerRanking.objects.update_or_create(player=player,
                                                   system=k,
                                                   # TODO can we just use v directly?
                                                   defaults={'score': float(v['score']),
                                                             'international_rank': v['international_rank'],
                                                             'national_rank': v['national_rank']})
        except Exception:
            # Handle all exceptions
            # This way, we fail to add/update the single ranking rather than all the background
            print('Failed to save PlayerRanking')
            print(f'player={str(player)}, system={k}')
            traceback.print_exc()
    # Nationalities
    # Assume that if we know nationalities they either came from the WDR or are more accurate
    if not player.nationalities:
        nat = bg.nationality()
        if nat:
            player.nationalities = Country(nat)
            fields.append('nationalities')
    # Location
    # Assume that if we know a location it either came from the WDR or is more accurate
    if not player.location:
        loc = bg.location()
        if loc:
            player.location = Country(loc).name
            fields.append('location')
    return fields


def add_player_bg(player):
    """
    Cache background data for the player in the database
    """
    fields = []
    # First check wikipedia
    bg = WikipediaBackground(f'{player.first_name} {player.last_name}')
    # Titles won
    titles = bg.titles()
    for title in titles:
        _update_or_create_playertitle_wiki(player, title)
    # Do we have a WDR id for this player?
    wdr = player.wdr_player_id
    if wdr:
        try:
            fields += _add_player_bg_from_wdr(player, wdr)
        except WDRNotAccessible:
            print(f'Unable to read from WDR for id {wdr}')
            wdr = None
    if fields:
        player.save(update_fields=fields)
    # TODO Set PlayerTitle.ranking to cross-reference
