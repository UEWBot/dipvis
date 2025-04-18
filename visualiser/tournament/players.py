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
from pathlib import Path
import traceback
from urllib.parse import urlunparse, urlencode

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max, Min, Q
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from django_countries.fields import Country, CountryField

from tournament.background import WikipediaBackground, WDDBackground, WDRBackground
from tournament.background import InvalidWDDId, WDDNotAccessible, WDRNotAccessible
from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR, TOTAL_SCS, WINNING_SCS
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.tasks.validate_sc_count import validate_sc_count
from tournament.diplomacy.tasks.validate_year import validate_year
from tournament.wdd import wdd_nation_to_country, wdd_url_to_tournament_id, UnrecognisedCountry
from tournament.wdd import validate_wdd_player_id, validate_wdd_tournament_id
from tournament.wdd import WDD_NETLOC, WDD_BASE_RESULTS_PATH, WDD_BASE_RANKING_PATH
from tournament.wdd import WDD_BASE_RESULTS_URL
from tournament.wdr import validate_wdr_player_id, validate_wdr_tournament_id
from tournament.wdr import WDR_BASE_URL
from tournament.wdr import wdr_power_name_to_greatpower


# Mask values to choose which background strings to include
MASK_TITLES = 1 << 0
MASK_TOURNEY_COUNT = 1 << 1
MASK_FIRST_TOURNEY = 1 << 2
MASK_LAST_TOURNEY = 1 << 3
MASK_BEST_TOURNEY_RESULT = 1 << 4
MASK_GAMES_PLAYED = 1 << 5
MASK_BEST_SC_COUNT = 1 << 6
MASK_SOLO_COUNT = 1 << 7
MASK_ELIM_COUNT = 1 << 8
MASK_BOARD_TOP_COUNT = 1 << 9
MASK_ROUND_ENDPOINTS = 1 << 10
MASK_BEST_COUNTRY = 1 << 11
MASK_OTHER_AWARDS = 1 << 12
MASK_RANKINGS = 1 << 13
MASK_SERIES_WINS = 1 << 14
MASK_ALL_BG = (1 << 15) - 1

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


def player_picture_location(instance, filename):
    """
    Function that determines where to store the file.
    """
    # Stuff them all into one directory
    return Path('player_pictures', filename)


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
            defaults['wpe_score']=wpe_scores[wdd_tournament_id]
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
        try:
            defaults['position_equals'] = b['Position sharing']
        except KeyError:
            defaults['position_equals'] = 1
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
        PlayerGameResult.objects.update_or_create(wdd_tournament_id=wdd_tournament_id,
                                                  game_name=b['Round / Board'],
                                                  player=player,
                                                  power=p,
                                                  defaults=defaults)
    except Exception:
        # Handle all exceptions
        # This way, we fail to add/update the single ranking rather than all the background
        print('Failed to save PlayerGameResult')
        print(f'player={str(player)}, tournament_name={b["Name of the tournament"]}, game_name={b["Round / Board"]}, power={str(p)}, position={b["Position"]}, date={b["Date"]}')
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
        game_name = f'{b["board_round"]} / {b["board_number"]}'
        if t['tournament_wdd_id'] == -1:
            try:
                PlayerGameResult.objects.update_or_create(wdr_tournament_id=t_id,
                                                          game_name=game_name,
                                                          player=player,
                                                          power=wdr_power_name_to_greatpower(b['board_power']),
                                                          defaults=defaults)
            except Exception:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print('Failed to save PlayerGameResult')
                print(f'player={str(player)}, tournament_name={t["tournament_name"]}, game_name={game_name}, power={b["board_power"]}, position={b["board_rank"]}')
                traceback.print_exc()
        else:
            defaults['wdr_tournament_id'] = t_id
            try:
                PlayerGameResult.objects.update_or_create(wdd_tournament_id=t['tournament_wdd_id'],
                                                          game_name=game_name,
                                                          player=player,
                                                          power=wdr_power_name_to_greatpower(b['board_power']),
                                                          defaults=defaults)
            except Exception:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print('Failed to save PlayerGameResult')
                print(f'player={str(player)}, tournament_name={t["tournament_name"]}, game_name={game_name}, power={b["board_power"]}, position={b["board_rank"]}')
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
            defaults['date']=t['tournament_end_date']
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
            defaults['wdr_tournament_id']=t_id
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
            wdr = None
    if not wdr:
        # Do we have a WDD id for this player?
        wdd = player.wdd_player_id
        if wdd:
            fields += _add_player_bg_from_wdd(player, wdd, include_wpe)
    if fields:
        player.save(update_fields=fields)
    # TODO Set PlayerTitle.ranking to cross-reference


def position_str(position):
    """
    Returns the string version of the position e.g. '1st', '12th'.
    """
    # TODO translation support ?
    result = str(position)
    pos = position % 100
    if pos > 3 and pos < 21:
        result += u'th'
    elif pos % 10 == 1:
        result += u'st'
    elif pos % 10 == 2:
        result += u'nd'
    elif pos % 10 == 3:
        result += u'rd'
    else:
        result += u'th'
    return _(result)


class WDDPlayerIdField(models.PositiveIntegerField):
    """A field that represents the unique id for a player in the WDD"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_val = None

    def pre_save(self, model_instance, add):
        # Clear cached WDD Name if WDD id has changed
        model_instance._wdd_firstname = ''
        model_instance._wdd_lastname = ''
        val = super().pre_save(model_instance, add)
        if (val != self._old_val) and not add:
            # Background data is presumably wrong
            model_instance._clear_background()
            self._old_val = val
        return val


class Player(models.Model):
    """
    A person who played Diplomacy
    """
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    wdd_player_id = WDDPlayerIdField(unique=True,
                                     validators=[validate_wdd_player_id],
                                     verbose_name=_(u'WDD player id'),
                                     blank=True,
                                     null=True)
    wdr_player_id = models.PositiveIntegerField(unique=True,
                                                validators=[validate_wdr_player_id],
                                                verbose_name=_(u'WDR player id'),
                                                blank=True,
                                                null=True)
    backstabbr_username = models.CharField(max_length=40,
                                           blank=True,
                                           help_text=_('Username on the backstabbr website'))
    backstabbr_profile_url = models.URLField(blank=True)
    picture = models.ImageField(upload_to=player_picture_location, blank=True, null=True)
    location = models.CharField(max_length=60, blank=True)
    nationalities = CountryField(multiple=True, blank=True)
    # Cache of the player's name in the WDD
    _wdd_firstname = models.CharField(max_length=40, blank=True)
    _wdd_lastname = models.CharField(max_length=40, blank=True)
    user = models.OneToOneField(User,
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE,
                                help_text=_('If the Player has an account on the site, record it here'))
    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def sortable_str(self):
        return f'{self.last_name}, {self.first_name}'

    def _clear_background(self):
        """
        Remove all background info on the Player from the database.

        This undoes add_player_bg()
        """
        self.playerranking_set.all().delete()
        self.playeraward_set.all().delete()
        self.playertournamentranking_set.all().delete()
        self.playergameresult_set.all().delete()

    def background_updated(self):
        """
        Returns the datetime at which the background info was most recently updated.

        If no date is available (or there's no background), None will be returned.
        """
        result = self.playerranking_set.aggregate(Max('updated'))['updated__max']

        latest = self.playeraward_set.aggregate(Max('updated'))['updated__max']
        if result is None:
            result = latest
        elif latest is not None:
            result = max(result, latest)

        latest = self.playertournamentranking_set.aggregate(Max('updated'))['updated__max']
        if result is None:
            result = latest
        elif latest is not None:
            result = max(result, latest)

        latest = self.playergameresult_set.aggregate(Max('updated'))['updated__max']
        if result is None:
            result = latest
        elif latest is not None:
            result = max(result, latest)

        return result

    def wdd_url(self):
        """URL for this player in the World Diplomacy Database."""
        if self.wdd_player_id:
            return f'{WDD_BASE_RESULTS_URL}player_fiche.php?id_player={self.wdd_player_id}'
        return ''

    def wdr_url(self):
        """URL for this player in the World Diplomacy Reference."""
        if self.wdr_player_id:
            return f'{WDR_BASE_URL}players/{self.wdr_player_id}'
        return ''

    def wdd_firstname_lastname(self):
        """
        Name for this player as a 2-tuple, as in the WDD.

        If the player has no WDD id, returns the name used locally.
        If the name in the WDD cannot be determined, returns ('', '').
        """
        if not self.wdd_player_id:
            return (self.first_name, self.last_name)
        # Read from the WDD if we haven't cached it
        if not self._wdd_firstname and not self._wdd_lastname:
            bg = WDDBackground(self.wdd_player_id)
            try:
                self._wdd_firstname, self._wdd_lastname = bg.wdd_firstname_lastname()
                self.save(update_fields=['_wdd_firstname', '_wdd_lastname'])
            except WDDNotAccessible:
                # Nothing we can do
                pass
            except InvalidWDDId as e:
                # This can only happen if we couldn't get to the WDD when wdd_player_id was validated
                raise ValidationError(_(u'WDD Id %(wdd_id)d is invalid'),
                                      params={'wdd_id': self.wdd_player_id}) from e
        return (self._wdd_firstname, self._wdd_lastname)

    def wdr_name(self):
        """Returns the name of the player in the WDR as a string"""
        try:
            bg = WDRBackground(self.wdr_player_id)
        except WDRNotAccessible:
            return ''
        names = bg.firstname_lastname()
        return f'{names[0]} {names[1]}'

    def tournamentplayers(self, including_unpublished=False):
        """Returns the set of TournamentPlayers for this Player."""
        tps = self.tournamentplayer_set.prefetch_related('tournament')
        if including_unpublished:
            return tps
        return tps.filter(tournament__is_published=True)

    def _rankings(self, mask=MASK_ALL_BG):
        """List of all rankings"""
        results = []
        if (mask & MASK_RANKINGS) == 0:
            return results
        rankings_set = self.playerranking_set.all()
        for r in rankings_set:
            results.append(f'{str(r)}.')
        return results

    def _awards(self, power=None, mask=MASK_ALL_BG):
        """List of all awards won, optionally as a specified power"""
        results = []
        award_set = self.playeraward_set.order_by('date')
        powers = GreatPower.objects.all()
        if power is not None:
            award_set = award_set.filter(power=power)
            powers = [power]
        if (mask & MASK_BEST_COUNTRY) != 0:
            # Look at each of the interesting powers
            for p in powers:
                # Find all the awards related to the power of interest
                power_award_set = award_set.filter(power=p)
                award_count = power_award_set.count()
                if award_count == 0:
                    results.append(_('%(name)s has never won Best %(power)s.')
                                   % {'name': self, 'power': p})
                    continue
                elif award_count == 1:
                    count_str = _('once')
                else:
                    count_str = _('%(count)d times') % {'count': award_count}
                results.append(_('%(name)s has won Best %(power)s %(count_str)s.')
                               % {'name': self,
                                  'power': p,
                                  'count_str': count_str})
                a = power_award_set.first()
                s = _('%(name)s first won %(award)s in %(year)d at %(tourney)s') % {'name': self,
                                                                                    'award': a.name,
                                                                                    'year': a.date.year,
                                                                                    'tourney': a.tournament}
                if a.final_sc_count:
                    s += _(' with %(dots)d Supply Centres') % {'dots': a.final_sc_count}
                s += '.'
                results.append(s)
                a = power_award_set.last()
                s = _('%(name)s most recently won %(award)s in %(year)d at %(tourney)s') % {'name': self,
                                                                                            'award': a.name,
                                                                                            'year': a.date.year,
                                                                                            'tourney': a.tournament}
                if a.final_sc_count:
                    s += _(' with %(dots)d Supply Centres') % {'dots': a.final_sc_count}
                s += '.'
                results.append(s)
        if (mask & MASK_OTHER_AWARDS) != 0:
            for a in award_set.filter(power=None):
                results.append(_('%(name)s won %(award)s at %(tourney)s.')
                               % {'name': self,
                                  'award': a.name,
                                  'tourney': a.tournament})
        return results

    def _titles(self, mask=MASK_ALL_BG):
        """List of titles won"""
        results = []
        title_set = self.playertitle_set.order_by('year')
        if (mask & MASK_TITLES) != 0:
            # Add summaries of actual titles
            titles = {}
            for title in title_set:
                titles.setdefault(title.title, []).append(title.year)
            for key, lst in titles.items():
                results.append(str(self) + ' was ' + key + ' in ' + ', '.join(map(str, lst)) + '.')
        return results

    def _tourney_rankings(self, mask=MASK_ALL_BG):
        """List of tournament rankings"""
        results = []
        ranking_set = self.playertournamentranking_set.order_by('year')
        plays = ranking_set.count()
        if plays == 0:
            if (mask & MASK_TOURNEY_COUNT) != 0:
                results.append(_(u'This is the first tournament for %(name)s.')
                               % {'name': self})
            return results
        if (mask & MASK_TOURNEY_COUNT) != 0:
            results.append(ngettext('%(name)s has competed in one tournament.',
                                    '%(name)s has competed in %(number)d tournaments.',
                                    plays)
                           % {'name': self, 'number': plays})
        if (mask & MASK_FIRST_TOURNEY) != 0:
            first = ranking_set.first()
            results.append(_(u'%(name)s first competed in a tournament (%(tournament)s) in %(year)d.')
                           % {'name': self,
                              'tournament': first.tournament,
                              'year': first.year})
        if (mask & MASK_LAST_TOURNEY) != 0:
            last = ranking_set.last()
            results.append(_(u'%(name)s most recently competed in a tournament (%(tournament)s) in %(year)d.')
                           % {'name': self,
                              'tournament': last.tournament,
                              'year': last.year})
        if (mask & MASK_BEST_TOURNEY_RESULT) != 0:
            wins_set = ranking_set.filter(position=1)
            wins = wins_set.count()
            if wins > 0:
                results.append(_(u'%(name)s has won %(wins)d of %(plays)d tournaments (%(percentage).2f%%).')
                               % {'name': self,
                                  'plays': plays,
                                  'percentage': 100.0 * float(wins) / float(plays),
                                  'wins': wins})
                w = wins_set.first()
                results.append(_('%(name)s won their first tournament (%(tourney)s) in %(year)d.')
                               % {'name': self,
                                  'tourney': w.tournament,
                                  'year': w.year})
                w = wins_set.last()
                results.append(_('%(name)s most recently won a tournament (%(tourney)s) in %(year)d.')
                               % {'name': self,
                                  'tourney': w.tournament,
                                  'year': w.year})
            else:
                best = ranking_set.aggregate(Min('position'))['position__min']
                pos = position_str(best)
                results.append(_(u'The best tournament result for %(name)s is %(position)s.')
                               % {'name': self, 'position': pos})
        return results

    def _results(self, power=None, mask=MASK_ALL_BG):
        """
        List of tournament game achievements, optionally with one Great Power.
        """
        results = []
        results_set = self.playergameresult_set.all()
        # We can't report anything useful if we have no info on games played
        if not results_set.exists():
            return results
        if power is not None:
            results_set = results_set.filter(power=power)
            c_str = _(u' as %(power)s') % {'power': power}
        else:
            c_str = u''
        games = results_set.count()
        if games == 0:
            if (mask & MASK_GAMES_PLAYED) != 0:
                results.append(_(u'%(name)s has never played%(power)s in a tournament before.')
                               % {'name': self,
                                  'power': c_str})
            return results
        games_word = _('games')
        if games == 1:
            games_word = _('game')
        if (mask & MASK_GAMES_PLAYED) != 0:
            results.append(_(u'%(name)s has played %(games)d tournament %(games_word)s%(power)s.')
                           % {'name': self,
                              'games': games,
                              'games_word': games_word,
                              'power': c_str})
        if (mask & MASK_BEST_SC_COUNT) != 0:
            best = results_set.aggregate(Max('final_sc_count'))['final_sc_count__max']
            # SC count is optional
            if best:
                results.append(_(u'%(name)s has finished with as many as %(dots)d centres%(power)s in tournament games.')
                               % {'name': self,
                                  'dots': best,
                                  'power': c_str})
        if (mask & MASK_SOLO_COUNT) != 0:
            solos = results_set.filter(final_sc_count__gte=WINNING_SCS).count()
            if solos > 0:
                results.append(_(u'%(name)s has soloed %(solos)d of %(games)d tournament %(games_word)s played%(power)s (%(percentage).2f%%).')
                               % {'name': self,
                                  'solos': solos,
                                  'games': games,
                                  'games_word': games_word,
                                  'power': c_str,
                                  'percentage': 100.0 * float(solos) / float(games)})
            else:
                results.append(_(u'%(name)s has yet to solo%(power)s at a tournament.')
                               % {'name': self,
                                  'power': c_str})
        if (mask & MASK_ELIM_COUNT) != 0:
            query = Q(year_eliminated__isnull=False) | Q(final_sc_count=0)
            eliminations_set = results_set.filter(query)
            eliminations = eliminations_set.count()
            if eliminations > 0:
                results.append(_(u'%(name)s was eliminated in %(deaths)d of %(games)d tournament %(games_word)s played%(power)s (%(percentage).2f%%).')
                               % {'name': self,
                                  'deaths': eliminations,
                                  'games': games,
                                  'games_word': games_word,
                                  'power': c_str,
                                  'percentage': 100.0 * float(eliminations) / float(games)})
            else:
                results.append(_(u'%(name)s has yet to be eliminated%(power)s in a tournament.')
                               % {'name': self,
                                  'power': c_str})
        if (mask & MASK_BOARD_TOP_COUNT) != 0:
            query = Q(result=GameResults.WIN) | Q(position=1)
            board_tops = results_set.filter(query).count()
            if board_tops > 0:
                results.append(_(u'%(name)s topped the board in %(tops)d of %(games)d tournament %(games_word)s played%(power)s (%(percentage).2f%%).')
                               % {'name': self,
                                  'tops': board_tops,
                                  'games': games,
                                  'games_word': games_word,
                                  'power': c_str,
                                  'percentage': 100.0 * float(board_tops) / float(games)})
            else:
                results.append(_(u'%(name)s has yet to top the board%(power)s at a tournament.')
                               % {'name': self,
                                  'power': c_str})
        return results

    def background(self, power=None, mask=MASK_ALL_BG):
        """
        List of background strings about the player, optionally as a specific Great Power
        """
        if power is None:
            return self._titles(mask=mask) + self._tourney_rankings(mask=mask) + self._results(mask=mask) + self._awards(mask=mask) + self._rankings(mask=mask)
        return self._results(power, mask=mask) + self._awards(power, mask=mask)

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('player_detail', args=[str(self.id)])


class PlayerTournamentRanking(models.Model):
    """
    A tournament ranking for a player.

    Used to import background information from external sites.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    tournament = models.CharField(max_length=100)
    position = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    date = models.DateField(blank=True, null=True)
    wdd_tournament_id = models.PositiveIntegerField(validators=[validate_wdd_tournament_id],
                                                    verbose_name=_(u'WDD tournament id'),
                                                    blank=True,
                                                    null=True)
    wdr_tournament_id = models.PositiveIntegerField(validators=[validate_wdr_tournament_id],
                                                    verbose_name=_(u'WDR tournament id'),
                                                    blank=True,
                                                    null=True)
    wpe_score = models.FloatField(blank=True,
                                  null=True,
                                  help_text=_('World Performance Evaluation score'))
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'tournament', 'year'],
                                    name='unique_player_tournament_year'),
        ]

    def wdd_url(self):
        """WDD URL where this ranking can be seen"""
        if (not self.wdd_tournament_id) or (not self.player.wdd_player_id):
            return ''
        query = {'id_tournament': self.wdd_tournament_id,
                 'id_player': self.player.wdd_player_id}
        url = urlunparse(('https',
                          WDD_NETLOC,
                          f'{WDD_BASE_RESULTS_PATH}tournament_player.php',
                          '',
                          urlencode(query),
                          ''))
        return url

    def wdr_url(self):
        """WDR URL where this ranking can be seen"""
        if not self.wdr_tournament_id:
            return ''
        return f'{WDR_BASE_URL}tournaments/{self.wdr_tournament_id}'

    def __str__(self):
        pos = position_str(self.position)
        s = _(u'%(player)s came %(position)s at %(tournament)s') % {'player': self.player,
                                                                    'position': pos,
                                                                    'tournament': self.tournament}
        if self.tournament[-4:] != str(self.year):
            s += _(u' in %(year)d') % {'year': self.year}
        return s


class PlayerTitle(models.Model):
    """
    A title won by a player.

    Used to import background information from external sites.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    year = models.PositiveSmallIntegerField()
    updated = models.DateTimeField(auto_now=True)
    # Cross-reference to more information about the tournament where the title was won
    ranking = models.ForeignKey(PlayerTournamentRanking,
                                on_delete=models.SET_NULL,
                                blank=True,
                                null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'title', 'year'],
                                    name='unique_player_title_year'),
        ]

    def __str__(self):
        s = _(u'%(player)s won %(title)s in %(year)s') % {'player': self.player,
                                                          'title': self.title,
                                                          'year': self.year}
        return s


class GameResults(models.TextChoices):
    """How a game ended, from one player's perspective"""
    # These encodings happen to co-incide with the coding used by the WDD
    WIN = 'W', _('Win')
    DRAW_2 = 'D2', _('2-way draw')
    DRAW_3 = 'D3', _('3-way draw')
    DRAW_4 = 'D4', _('4-way draw')
    DRAW_5 = 'D5', _('5-way draw')
    DRAW_6 = 'D6', _('6-way draw')
    DRAW_7 = 'D7', _('7-way draw')
    LOSS = 'L', _('Loss')


class PlayerGameResult(models.Model):
    """
    One player's result for a tournament game.

    Used to import background information from external sites.
    """

    tournament_name = models.CharField(max_length=100)
    game_name = models.CharField(max_length=20)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    power = models.ForeignKey(GreatPower, related_name='+', on_delete=models.CASCADE)
    date = models.DateField()
    position = models.PositiveSmallIntegerField()
    position_equals = models.PositiveSmallIntegerField(blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    final_sc_count = models.PositiveSmallIntegerField(blank=True,
                                                      null=True,
                                                      validators=[validate_sc_count])
    result = models.CharField(max_length=2, choices=GameResults.choices, blank=True)
    year_eliminated = models.PositiveSmallIntegerField(blank=True,
                                                       null=True,
                                                       validators=[validate_year])
    wdd_tournament_id = models.PositiveIntegerField(validators=[validate_wdd_tournament_id],
                                                    verbose_name=_(u'WDD tournament id'),
                                                    blank=True,
                                                    null=True)
    wdr_tournament_id = models.PositiveIntegerField(validators=[validate_wdr_tournament_id],
                                                    verbose_name=_(u'WDR tournament id'),
                                                    blank=True,
                                                    null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(final_sc_count__lte=TOTAL_SCS) | Q(final_sc_count__isnull=True),
                                   name='%(class)s_final_sc_count_valid'),
            models.CheckConstraint(check=Q(result__in=GameResults.values) | Q(result=''),
                                   name='%(class)s_result_valid'),
            models.CheckConstraint(check=Q(year_eliminated__gte=FIRST_YEAR) | Q(year_eliminated__isnull=True),
                                   name='%(class)s_year_eliminated_valid'),
            models.UniqueConstraint(fields=['tournament_name', 'game_name', 'player', 'power'],
                                    name='unique_names_player_power'),
        ]

    def for_same_game(self, pgr):
        """Returns True if the two PlayerGameResults are for the same game"""
        return ((self.tournament_name == pgr.tournament_name) and
                (self.game_name == pgr.game_name) and
                (self.date == pgr.date))

    def round(self):
        """Which round of the tournament was the game played?"""
        # Parse the game name
        # Format is either "R n B m" or "n / m"
        parts = self.game_name.split()
        if (len(parts) == 4) and (parts[0] == 'R') and (parts[2] == 'B'):
            return parts[1]
        elif (len(parts) == 3) and (parts[1] == '/'):
            return parts[0]
        return '?'

    def board(self):
        """Which board of the round was the game?"""
        # Parse the game name
        # Format is either "R n B m" or "n / m"
        parts = self.game_name.split()
        return parts[-1]

    def wdd_url(self):
        """WDD URL where this result can be seen"""
        if not self.wdd_tournament_id:
            return ''
        query = {'id_tournament': self.wdd_tournament_id,
                 'id_round': self.round(),
                 'id_board': self.board()}
        url = urlunparse(('https',
                          WDD_NETLOC,
                          f'{WDD_BASE_RESULTS_PATH}tournament_board.php',
                          '',
                          urlencode(query),
                          ''))
        return url

    def wdr_url(self):
        """WDR URL where this ranking can be seen"""
        if not self.wdr_tournament_id:
            return ''
        return f'{WDR_BASE_URL}tournaments/{self.wdr_tournament_id}/boards'

    def __str__(self):
        return _(u'%(player)s played %(power)s in %(game)s at %(tourney)s') % {'player': self.player,
                                                                               'power': self.power,
                                                                               'game': self.game_name,
                                                                               'tourney': self.tournament_name}


class PlayerAward(models.Model):
    """
    An award won by a player.

    Used to import background information.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    tournament = models.CharField(max_length=100)
    date = models.DateField()
    name = models.CharField(max_length=50)
    power = models.ForeignKey(GreatPower,
                              related_name='+',
                              on_delete=models.CASCADE,
                              blank=True,
                              null=True)
    score = models.FloatField(blank=True, null=True)
    final_sc_count = models.PositiveSmallIntegerField(blank=True, null=True)
    wdd_tournament_id = models.PositiveIntegerField(validators=[validate_wdd_tournament_id],
                                                    verbose_name=_(u'WDD tournament id'),
                                                    blank=True,
                                                    null=True)
    wdr_tournament_id = models.PositiveIntegerField(validators=[validate_wdr_tournament_id],
                                                    verbose_name=_(u'WDR tournament id'),
                                                    blank=True,
                                                    null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(final_sc_count__lte=TOTAL_SCS) | Q(final_sc_count__isnull=True),
                                   name='%(class)s_final_sc_count_valid'),
            models.UniqueConstraint(fields=['player', 'tournament', 'date', 'name'],
                                    name='unique_player_tournament_date_name'),
        ]

    def wdd_url(self):
        """WDD URL where this award can be seen"""
        if not self.wdd_tournament_id:
            return ''
        if self.power is None:
            path = 'tournament_award.php'
        else:
            path = 'tournament_best_countries.php'
        query = {'id_tournament': self.wdd_tournament_id}
        url = urlunparse(('https',
                          WDD_NETLOC,
                          f'{WDD_BASE_RESULTS_PATH}{path}',
                          '',
                          urlencode(query),
                          ''))
        return url

    def wdr_url(self):
        """WDR URL where this ranking can be seen"""
        if not self.wdr_tournament_id:
            return ''
        return f'{WDR_BASE_URL}tournaments/{self.wdr_tournament_id}'

    def __str__(self):
        return _('%(player)s won %(award)s at %(tourney)s') % {'player': self.player,
                                                               'award': self.name,
                                                               'tourney': self.tournament}


class PlayerRanking(models.Model):
    """
    WDD Ranking of a player.

    Used to import background information.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    system = models.CharField(max_length=50)
    score = models.FloatField(blank=True, null=True)
    international_rank = models.CharField(max_length=20)
    national_rank = models.CharField(max_length=20)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'system'],
                                    name='unique_player_system'),
        ]

    def wdd_url(self):
        """WDD URL where this ranking can be seen"""
        if not self.player.wdd_player_id:
            return ''
        if self.system == 'World Performance Evaluation':
            wdd_system_id = 2
        elif self.system == 'Dip Pouch Tournament Rating':
            wdd_system_id = 3
        elif self.system == 'SDR Marathon':
            wdd_system_id = 16
        else:
            return ''
        query = {'id_ranking': wdd_system_id,
                 'id_player': self.player.wdd_player_id}
        url = urlunparse(('https',
                          WDD_NETLOC,
                          f'{WDD_BASE_RANKING_PATH}ranking_player.php',
                          '',
                          urlencode(query),
                          ''))
        return url

    def wdr_url(self):
        """WDR URL where this ranking can be seen"""
        if self.system == 'WPE7':
            return f'{WDR_BASE_URL}rankings/wpe7'
        return ''

    def national_str(self):
        """Returns a string describing the national_rank"""
        s = _('%(player)s is ranked %(ranking)s in their country in the %(system)s') % {'player': self.player,
                                                                                        'ranking': self.national_rank,
                                                                                        'system': self.system}
        return s

    def __str__(self):
        s = _('%(player)s is ranked %(ranking)s internationally in the %(system)s') % {'player': self.player,
                                                                                       'ranking': self.international_rank,
                                                                                       'system': self.system}
        return s
