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

from .player_award import PlayerAward
from .player_game_result import PlayerGameResult
from .player_ranking import PlayerRanking
from .player_title import PlayerTitle
from .player_tournament_ranking import PlayerTournamentRanking
from .wdd_background import WDDBackground
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


def _update_or_create_playertournamentranking_wdd1(player, finish, wpe_scores):
    """
    Creates or updates a PlayerTournamentRanking for the player

    Given a Player and a dict with 'Tournament' 'Date', 'Position',
    and 'WDD URL' keys, representing the World Diplomacy Database data,
    plus a dict keyed by WDD tournament id of WPE scores for the player,
    create or update a PlayerTournamentRanking
    """
    d = finish['Date']
    try:
        wdd_tournament_id = wdd_url_to_tournament_id(finish['WDD URL'])
        defaults = {'position': finish['Position'],
                    'tournament': finish['Tournament']}
        try:
            defaults['wpe_score'] = wpe_scores[wdd_tournament_id]
        except KeyError:
            pass
        try:
            # WDD contains some invalid dates (e.g. '2017-09-0')
            datetime.datetime.strptime(d, '%Y-%m-%d')
        except ValueError:
            pass
        else:
            defaults['date'] = d
        PlayerTournamentRanking.objects.update_or_create(player=player,
                                                         wdd_tournament_id=wdd_tournament_id,
                                                         year=d[:4],
                                                         defaults=defaults)
    except Exception:
        # Handle all exceptions
        # This way, we fail to add/update the single ranking rather than all the background
        print('Failed to save PlayerTournamentRanking')
        print(f'player={str(player)}, tournament={finish["Tournament"]}, position={finish["Position"]}, year={d[:4]}')
        traceback.print_exc()


def _update_or_create_playertournamentranking_wdd2(player, t):
    """
    Creates or updates a PlayerTournamentRanking for the player

    Given a Player and a dict with 'Name of the Tournament' 'Date', 'Rank',
    and 'WDD URL' keys, representing the World Diplomacy Database data,
    create or update a PlayerTournamentRanking
    """
    d = t['Date']
    try:
        wdd_tournament_id = wdd_url_to_tournament_id(t['WDD URL'])
        defaults = {'position': t['Rank'],
                    'tournament': t['Name of the tournament']}
        try:
            # WDD contains some invalid dates (e.g. '2017-09-0')
            datetime.datetime.strptime(d, '%Y-%m-%d')
        except ValueError:
            pass
        else:
            defaults['date'] = d
        PlayerTournamentRanking.objects.update_or_create(player=player,
                                                         wdd_tournament_id=wdd_tournament_id,
                                                         year=d[:4],
                                                         defaults=defaults)
    except KeyError:
        # No rank implies they were the TD or similar - just ignore that tournament
        print(f'Ignoring unranked {t["Name of the tournament"]} for {player}')
    except Exception:
        # Handle all other exceptions
        # This way, we fail to add/update the single ranking rather than all the background
        print('Failed to save PlayerTournamentRanking')
        print(f'player={str(player)}, tournament={t["Name of the tournament"]}, position={t["Rank"]}, year={d[:4]}')
        traceback.print_exc()


def _split_wdd_game_name(name):
    """
    Extracts the round number and game number from a WDD game name.

    Returns a (round_number, game_number) 2-tuple.
    """
    # Format is "R n B m" or "R / B"
    parts = name.split()
    if (len(parts) == 4) and (parts[0] == 'R') and (parts[2] == 'B'):
        return parts[1], parts[-1]
    elif (len(parts) == 3) and (parts[1] == '/'):
        return parts[0], parts[-1]
    raise ValueError(name)


def _update_or_create_playergameresult(player, b):
    """
    Creates or updates a PlayerGameResult for the player

    Given a Player and a dict with 'Country', 'Name of the Tournament' 'Date' 'Round / Board', 'Position',
    and 'WDD Tournament URL' keys, and optional 'Position sharing' 'Score' 'Final SCs' 'Game end' and
    'Elimination year' keys, representing the World Diplomacy Database data, create or update a PlayerGameResult
    """
    try:
        power = b['Country']
        p = GreatPower.objects.get(name__contains=power)
    except GreatPower.DoesNotExist:
        # Apparently not a Standard game
        return
    if 'Position' not in b:
        # We can't make assumptions about how players are ranked within a game
        # without knowing the scoring system, DIAS, etc.
        print(f'Ignoring game {b["Round / Board"]} in {b["Name of the tournament"]} for {str(player)} with no position')
        return
    try:
        wdd_tournament_id = wdd_url_to_tournament_id(b['WDD Tournament URL'])
        defaults = {'position': b['Position'],
                    'tournament_name': b['Name of the tournament']}
        # If there's no 'Position sharing', they were alone at that position
        defaults['position_equals'] = b.get('Position sharing', 1)
        # Ignore any of these that aren't present
        try:
            defaults['score'] = b['Score']
        except KeyError:
            pass
        try:
            defaults['final_sc_count'] = b['Final SCs']
        except KeyError:
            pass
        try:
            defaults['result'] = b['Game end']
        except KeyError:
            pass
        try:
            defaults['year_eliminated'] = b['Elimination year']
        except KeyError:
            pass
        # WDD has been known to change the date
        # The result should still be unique without it, though
        defaults['date'] = b['Date']
        round_num, game_num = _split_wdd_game_name(b['Round / Board'])
        PlayerGameResult.objects.update_or_create(wdd_tournament_id=wdd_tournament_id,
                                                  round_number=round_num,
                                                  game_number=game_num,
                                                  player=player,
                                                  power=p,
                                                  defaults=defaults)
    except Exception:
        # Handle all exceptions
        # This way, we fail to add/update the single ranking rather than all the background
        print('Failed to save PlayerGameResult')
        print(f'player={str(player)}, tournament_name={b["Name of the tournament"]}, round_number={round_num}, game_number={game_num}, power={str(p)}, position={b["Position"]}, date={b["Date"]}')
        traceback.print_exc()


def _update_or_create_playeraward(player, k, a):
    """
    Creates or updates a PlayerAward for the player

    Given a Player and key ('Awards' or a GreatPower name) and a dict with 'Tournament', 'Date',
    and 'WDD URL' keys, and optional 'Score' and 'SCs' keys,
    representing the World Diplomacy Database data, create or update a PlayerAward
    """
    if k == 'Awards':
        award_name = a['Name']
    else:
        try:
            p = GreatPower.objects.get(name__contains=k)
        except GreatPower.DoesNotExist:
            # Apparently not a Standard game
            return
        award_name = f'Best {p}'
    # Some of the WDD pages are badly-structured with nested tables
    # Ignore any messed-up results
    # TODO "bad date" is often just a year - could pick 31 Dec for those
    #      "no date" often have a year, which could also be used as above
    try:
        date_str = a['Date']
        if len(date_str) != 10:
            print(f'Ignoring award with bad date {str(a)}')
            return
    except KeyError:
        print(f'Ignoring award with no date {str(a)}')
        return
    try:
        wdd_tournament_id = wdd_url_to_tournament_id(a['WDD URL'])
        defaults = {'tournament': a['Tournament']}
        if k != 'Awards':
            defaults['power'] = p
        # Ignore any of these that aren't present
        try:
            defaults['score'] = a['Score']
        except KeyError:
            pass
        try:
            defaults['final_sc_count'] = a['SCs']
        except KeyError:
            pass
        PlayerAward.objects.update_or_create(player=player,
                                             wdd_tournament_id=wdd_tournament_id,
                                             date=date_str,
                                             name=award_name,
                                             defaults=defaults)
    except Exception:
        # Handle all exceptions
        # This way, we fail to add/update the single ranking rather than all the background
        print('Failed to save PlayerAward')
        print(f'player={str(player)}, tournament={a["Tournament"]}, date={date_str}, name={award_name}')
        traceback.print_exc()


def _update_or_create_playerranking(player, r):
    """
    Creates or updates a PlayerRanking for the player

    Given a Player and a dict with 'Name' 'Score' 'International rank' and 'National rank' keys,
    representing the World Diplomacy Database data, create or update a PlayerRanking
    """
    try:
        PlayerRanking.objects.update_or_create(player=player,
                                               system=r['Name'],
                                               defaults={'score': float(r['Score']),
                                                         'international_rank': r['International rank'],
                                                         'national_rank': r['National rank']})
    except Exception:
        # Handle all exceptions
        # This way, we fail to add/update the single ranking rather than all the background
        print('Failed to save PlayerRanking')
        print(f'player={str(player)}, system={r["Name"]}')
        traceback.print_exc()


def _add_player_bg_from_wdd(player, wdd_id, include_wpe):
    """
    Add or update player background information from the WDD

    Returns a list of Player fields that were updated and need saving.
    """
    fields = []
    bg = WDDBackground(wdd_id)
    # WPE scores
    wpe_scores = {}
    if include_wpe:
        # Construct a dict, keyed by WDD Id, of WPE scores
        for score in bg.wpe_scores():
            key = wdd_url_to_tournament_id(score['WDD WPE URL'])
            if key:
                wpe_scores[key] = score['Score']
    # Podium finishes
    finishes = bg.finishes()
    for finish in finishes:
        _update_or_create_playertournamentranking_wdd1(player, finish, wpe_scores)
    # Tournaments
    tournaments = bg.tournaments()
    for t in tournaments:
        _update_or_create_playertournamentranking_wdd2(player, t)
    # Boards
    boards = bg.boards()
    for b in boards:
        _update_or_create_playergameresult(player, b)
    # Awards
    awards = bg.awards()
    for k, v in awards.items():
        # Go through the list of awards
        for a in v:
            _update_or_create_playeraward(player, k, a)
    # Rankings
    rankings = bg.rankings()
    for r in rankings:
        _update_or_create_playerranking(player, r)
    # Nationalities
    # Assume that if we know nationalities they either came from the WDD or are more accurate
    if not player.nationalities:
        nats = bg.nationalities()
        try:
            player.nationalities = wdd_nation_to_country(nats[0])
        except IndexError:
            # WDD doesn't have nationality info
            pass
        except UnrecognisedCountry:
            # WDD does have a country, but it doesn't map to a real-world country
            pass
        else:
            fields.append('nationalities')
    # Location
    # Assume that if we know a location it either came from the WDD or is more accurate
    if not player.location:
        loc = bg.location()
        if loc:
            try:
                player.location = wdd_nation_to_country(loc).name
            except UnrecognisedCountry:
                # WDD does have a country, but it doesn't map to a real-world country
                pass
            else:
                fields.append('location')
    return fields


def _find_wdr_tournament(wdr_id, tournaments_list):
    """
    Return the dict for the specified tournament from a list of dicts
    """
    for t in tournaments_list:
        if wdr_id == t['tournament_id']:
            return t


def _wdr_tournament_should_be_included(t):
    """
    Is the WDR tournament actually a tournament?

    WDR tournaments include several events that are not tournaments per se.

    t should be the dict representing the tournament in the WDR.
    Return True if t is an actual tournament that we want to include.
    """
    kind = t['tournament_kind']
    if kind in ['EDC',      # European Championship
                'DIPCON',   # North American Championship
                'APAC',     # Asia-Pacific Championship
                'NDC',      # National Championship
                'MASTERS',  # Invitational
                'DBNI',     # DBN Invitational
                'VDC',      # Virtual Championship
                'CUP',
                'NCUP',     # National Cup
                'OPEN',
                'WDC']:     # World Championship
        return True
    elif kind in ['LEAGUE',
                  'EGP',   # European Grand Prix
                  'NAGP',  # North American Grand Prix
                  'BIC',   # Bismark Cup
                  'nCIR',  # National Circuit
                  'NCIR',  # National Circuit
                  'CIR']:  # Circuit
        return False
    else:
        print(f'Unrecognised tournament_kind {kind} in {t}')
        return False


def _add_player_bg_from_wdr(player, wdr_id):
    """
    Add or update player background information from the WDR

    Returns a list of Player fields that were updated and need saving.
    """
    fields = []
    bg = WDRBackground(wdr_id)
    # Podium finishes and Tournaments
    tournaments = bg.tournaments()
    for t in tournaments:
        # We only care about tournaments where the player was ranked
        # (others are most likely ones where they were TD but played)
        if not t['tournament_player_rank']:
            print(f"Skipping {t['tournament_name']} for {player} with no ranking")
            continue
        elif t['tournament_player_rank'] == -1:
            print(f"Skipping {t['tournament_name']} for {player} with -1 ranking")
            continue
        if not _wdr_tournament_should_be_included(t):
            continue
        defaults = {'position': t['tournament_player_rank'],
                    'tournament': t['tournament_name']}
        if t['tournament_end_date']:
            defaults['date'] = t['tournament_end_date']
        else:
            defaults['date'] = t['tournament_start_date']
        if t['tournament_wdd_id'] == -1:
            try:
                PlayerTournamentRanking.objects.update_or_create(player=player,
                                                                 wdr_tournament_id=t['tournament_id'],
                                                                 year=defaults['date'][:4],
                                                                 defaults=defaults)
            except Exception:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print('Failed to save PlayerTournamentRanking')
                print(f'player={str(player)}, tournament={t["tournament_name"]}, position={t["tournament_player_rank"]}, year={defaults["date"][:4]}')
                traceback.print_exc()
        else:
            defaults['wdr_tournament_id'] = t['tournament_id']
            try:
                PlayerTournamentRanking.objects.update_or_create(player=player,
                                                                 wdd_tournament_id=t['tournament_wdd_id'],
                                                                 year=defaults['date'][:4],
                                                                 defaults=defaults)
            except Exception:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print('Failed to save PlayerTournamentRanking')
                print(f'player={str(player)}, tournament={t["tournament_name"]}, position={t["tournament_player_rank"]}, year={defaults["date"][:4]}')
                traceback.print_exc()
    # Boards
    for b in bg.boards():
        # Skip variant boards because they don't factor well into the statistics
        if b['board_variant'] not in ['Classic', 'Standard (7)', 'Standard']:
            print('Skipping variant board')
            print(b)
            continue
        # What was the tournament?
        t_id = b['board_tournament']
        t = _find_wdr_tournament(t_id, tournaments)
        if not t:
            # This seems like a bug in WDR - sometimes tournaments are missing from the list
            print("Failed to find tournament")
            print(b)
            print(t_id)
            continue
        defaults = {'tournament_name': t['tournament_name'],
                    'position': b['board_rank']}
        if not b['board_rank']:
            # This seems like a bug in WDR, but sometimes we don't get a rank
            print("No board_rank")
            print(b)
            continue
        if t['tournament_end_date']:
            defaults['date'] = t['tournament_end_date']
        else:
            defaults['date'] = t['tournament_start_date']
        # Ignore any of these that aren't present
        if b['board_score']:
            defaults['score'] = b['board_score']
        if b['board_centers']:
            defaults['final_sc_count'] = b['board_centers']
        if b['board_year_of_elimination']:
            defaults['year_eliminated'] = b['board_year_of_elimination']
        if t['tournament_wdd_id'] == -1:
            try:
                PlayerGameResult.objects.update_or_create(wdr_tournament_id=t_id,
                                                          round_number=b['board_round'],
                                                          game_number=b['board_number'],
                                                          player=player,
                                                          power=wdr_power_name_to_greatpower(b['board_power']),
                                                          defaults=defaults)
            except Exception:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print('Failed to save PlayerGameResult')
                print(f'player={str(player)}, tournament_name={t["tournament_name"]}, round_number={b["board_round"]}, game_number={b["board_number"]}, power={b["board_power"]}, position={b["board_rank"]}')
                traceback.print_exc()
        else:
            defaults['wdr_tournament_id'] = t_id
            try:
                PlayerGameResult.objects.update_or_create(wdd_tournament_id=t['tournament_wdd_id'],
                                                          round_number=b['board_round'],
                                                          game_number=b['board_number'],
                                                          player=player,
                                                          power=wdr_power_name_to_greatpower(b['board_power']),
                                                          defaults=defaults)
            except Exception:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print('Failed to save PlayerGameResult')
                print(f'player={str(player)}, tournament_name={t["tournament_name"]}, round_number={b["board_round"]}, game_number={b["board_number"]}, power={b["board_power"]}, position={b["board_rank"]}')
                traceback.print_exc()
    # Awards
    for a in bg.awards():
        # WDR only stores best country awards at present
        award_name = f'Best {a["award_country"]}'
        # What was the tournament?
        t_id = a['award_tournament']
        t = _find_wdr_tournament(t_id, tournaments)
        defaults = {'tournament': t['tournament_name']}
        if t['tournament_end_date']:
            defaults['date'] = t['tournament_end_date']
        else:
            defaults['date'] = t['tournament_start_date']
        if t['tournament_wdd_id'] == -1:
            try:
                PlayerAward.objects.update_or_create(player=player,
                                                     wdr_tournament_id=t_id,
                                                     name=award_name,
                                                     power=wdr_power_name_to_greatpower(a['award_country']),
                                                     defaults=defaults)
            except Exception:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print('Failed to save PlayerAward')
                print(f'player={str(player)}, tournament={t["tournament_name"]}, date={t["tournament_end_date"]}, name={award_name}')
                traceback.print_exc()
        else:
            defaults['wdr_tournament_id'] = t_id
            try:
                PlayerAward.objects.update_or_create(player=player,
                                                     wdd_tournament_id=t['tournament_wdd_id'],
                                                     name=award_name,
                                                     power=wdr_power_name_to_greatpower(a['award_country']),
                                                     defaults=defaults)
            except Exception:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print('Failed to save PlayerAward')
                print(f'player={str(player)}, tournament={t["tournament_name"]}, date={t["tournament_end_date"]}, name={award_name}')
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


def add_player_bg(player, include_wpe=False):
    """
    Cache background data for the player

    include_wpe=True will set PlayerTournamentRanking.wpe_score,
    which involves parsing an additional WDD page
    """
    fields = []
    # First check wikipedia
    bg = WikipediaBackground(f'{player.first_name} {player.last_name}')
    # Titles won
    titles = bg.titles()
    for title in titles:
        _update_or_create_playertitle_wiki(player, title)
    # TODO If we have both ids, check that the WDR agrees about the WDD id
    #      player.wdd_player_id == WDRBackground(player.wdr_player_id).wdd_id()
    # WDR is easier to parse and often more up-to-date, so use it in preference to WDD
    # Do we have a WDR id for this player?
    wdr = player.wdr_player_id
    if wdr:
        try:
            fields += _add_player_bg_from_wdr(player, wdr)
        except WDRNotAccessible:
            print(f'Unable to read from WDR for id {wdr}')
            wdr = None
    if not wdr:
        # Do we have any WDD ids for this player?
        for wdd in player.wddplayer_set.all():
            fields += _add_player_bg_from_wdd(player, wdd.wdd_player_id, include_wpe)
    if fields:
        player.save(update_fields=fields)
    # TODO Set PlayerTitle.ranking to cross-reference
