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
import re
import traceback
import urllib.request

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max, Min, Q
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from tournament.background import WikipediaBackground, WDDBackground, WDD_BASE_RESULTS_URL
from tournament.background import InvalidWDDId, WDDNotAccessible
from tournament.diplomacy.values.diplomacy_values import WINNING_SCS
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.tasks.validate_sc_count import validate_sc_count
from tournament.diplomacy.tasks.validate_year import validate_year

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
    'North American Champion': 1,
    'Winner': 1,
    'European Champion': 1,
    'Second': 2,
    'Third': 3,
}


def validate_wdd_player_id(value):
    """
    Checks a WDD player id
    """
    url = WDD_BASE_RESULTS_URL + 'player_fiche.php?id_player=%d' % value
    try:
        p = urllib.request.urlopen(url)
    except urllib.request.URLError:
        # Most likely WDD is not available - assume the value is ok
        return
    if p.geturl() != url:
        raise ValidationError(_(u'%(value)d is not a valid WDD player Id'),
                              params={'value': value})


def validate_wdd_tournament_id(value):
    """
    Checks a WDD tournament id
    """
    url = WDD_BASE_RESULTS_URL + 'tournament_class.php?id_tournament=%d' % value
    try:
        p = urllib.request.urlopen(url)
    except urllib.request.URLError:
        # Most likely WDD is not available - assume the value is ok
        return
    if p.geturl() != url:
        raise ValidationError(_(u'%(value)d is not a valid WDD tournament Id'),
                              params={'value': value})


def player_picture_location(instance, filename):
    """
    Function that determines where to store the file.
    """
    # Stuff them all into one directory
    return 'player_pictures/%s' % filename


def wdd_url_to_id(url):
    """
    Extracts the tournament id from a WDD tournament URL
    """
    # The numbers at the end of the string
    m = re.search(r'(\d+)$', url)
    if m:
        return int(m.group(1))
    return 0


def _update_or_create_playertournamentranking_wiki(player, title):
    """
    Given a Player and a dict with 'Tournament' and 'Year' keys,
    and optional 'Champion' key, representing the Wikipedia page,
    create or update a PlayerTournamentRanking
    """
    pos = None
    the_title = None
    for key, val in TITLE_MAP.items():
        try:
            if title[key] == str(player):
                pos = val
                if 'Champion' in key:
                    the_title = key
        except KeyError:
            pass
    if pos:
        try:
            defaults = {}
            if the_title:
                defaults['title'] = the_title
            PlayerTournamentRanking.objects.update_or_create(player=player,
                                                             tournament=title['Tournament'],
                                                             position=pos,
                                                             year=title['Year'],
                                                             defaults=defaults)
        except Exception:
            # Handle all exceptions
            # This way, we fail to add/update the single ranking rather than all the background
            print("Failed to save PlayerTournamentRanking")
            print("player=%s, tournament=%s, position=%s, year=%s" % (str(player),
                                                                      title['Tournament'],
                                                                      pos,
                                                                      title['Year']))
            traceback.print_exc()


def _update_or_create_playertournamentranking_wdd1(player, finish, wpe_scores):
    """
    Given a Player and a dict with 'Tournament' 'Date' and 'Position' keys,
    and optional 'WDD URL' key, representing the World Diplomacy Database data,
    plus a dict keyed by WDD tournament id of WPE scores for the player,
    create or update a PlayerTournamentRanking
    """
    d = finish['Date']
    try:
        defaults = {}
        try:
            # WDD contains some invalid dates (e.g. '2017-09-0')
            datetime.datetime.strptime(d, '%Y-%m-%d')
        except ValueError:
            pass
        else:
            defaults['date'] = d
        # Ignore if not present
        try:
            defaults['wdd_tournament_id'] = wdd_url_to_id(finish['WDD URL'])
        except KeyError:
            pass
        else:
            try:
                defaults['wpe_score'] = wpe_scores[defaults['wdd_tournament_id']]
            except KeyError:
                pass
        PlayerTournamentRanking.objects.update_or_create(player=player,
                                                         tournament=finish['Tournament'],
                                                         position=finish['Position'],
                                                         year=d[:4],
                                                         defaults=defaults)
    except Exception:
        # Handle all exceptions
        # This way, we fail to add/update the single ranking rather than all the background
        print("Failed to save PlayerTournamentRanking")
        print("player=%s, tournament=%s, position=%s, year=%s" % (str(player),
                                                                  finish['Tournament'],
                                                                  finish['Position'],
                                                                  d[:4]))
        traceback.print_exc()


def _update_or_create_playertournamentranking_wdd2(player, t):
    """
    Given a Player and a dict with 'Name of the Tournament' 'Date' and 'Rank' keys,
    and optional 'WDD URL' key, representing the World Diplomacy Database data,
    create or update a PlayerTournamentRanking
    """
    d = t['Date']
    try:
        defaults = {}
        try:
            # WDD contains some invalid dates (e.g. '2017-09-0')
            datetime.datetime.strptime(d, '%Y-%m-%d')
        except ValueError:
            pass
        else:
            defaults['date'] = d
        # Ignore if not present
        try:
            defaults['wdd_tournament_id'] = wdd_url_to_id(t['WDD URL'])
        except KeyError:
            pass
        PlayerTournamentRanking.objects.update_or_create(player=player,
                                                         tournament=t['Name of the tournament'],
                                                         position=t['Rank'],
                                                         year=d[:4],
                                                         defaults=defaults)
    except KeyError:
        # No rank implies they were the TD or similar - just ignore that tournament
        print("Ignoring unranked %s for %s" % (t['Name of the tournament'], player))
    except Exception:
        # Handle all other exceptions
        # This way, we fail to add/update the single ranking rather than all the background
        print("Failed to save PlayerTournamentRanking")
        print("player=%s, tournament=%s, position=%s, year=%s" % (str(player),
                                                                  t['Name of the tournament'],
                                                                  t['Rank'],
                                                                  d[:4]))
        traceback.print_exc()


def _update_or_create_playergameresult(player, b):
    """
    Given a Player and a dict with 'Country', 'Name of the Tournament' 'Date' 'Round / Board' and 'Position' keys,
    and optional 'Position sharing' 'Score' 'Final SCs' 'Game end' 'Elimination year' and 'WDD Tournament URL' keys,
    representing the World Diplomacy Database data, create or update a PlayerGameResult
    """
    try:
        power = b['Country']
        p = GreatPower.objects.get(name__contains=power)
    except GreatPower.DoesNotExist:
        # Apparently not a Standard game
        return
    if 'Position' not in b:
        print('Ignoring game %s in %s for %s with no position' % (b['Round / Board'],
                                                                  b['Name of the tournament'],
                                                                  str(player)))
        return
    try:
        defaults = {}
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
        try:
            defaults['wdd_tournament_id'] = wdd_url_to_id(b['WDD Tournament URL'])
        except KeyError:
            pass
        # WDD has been known to change the date
        # The result should still be unique without it, though
        defaults['date'] = b['Date']
        PlayerGameResult.objects.update_or_create(tournament_name=b['Name of the tournament'],
                                                  game_name=b['Round / Board'],
                                                  player=player,
                                                  power=p,
                                                  position=b['Position'],
                                                  defaults=defaults)
    except Exception:
        # Handle all exceptions
        # This way, we fail to add/update the single ranking rather than all the background
        print("Failed to save PlayerGameResult")
        print("player=%s, tournament_name=%s, game_name=%s, power=%s, position=%s, date=%s"
              % (str(player),
                 b['Name of the tournament'],
                 b['Round / Board'],
                 str(p),
                 b['Position'],
                 b['Date']))
        traceback.print_exc()


def _update_or_create_playeraward(player, k, a):
    """
    Given a Player and key ('Awards' or a GreatPower name) and a dict with 'Tournament' and 'Date' keys,
    and optional 'Score' 'SCs' and 'WDD URL' keys,
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
        award_name = 'Best %s' % p
    # Some of the WDD pages are badly-structured with nested tables
    # Ignore any messed-up results
    try:
        date_str = a['Date']
        if len(date_str) != 10:
            print('Ignoring award with bad date %s' % str(a))
            return
    except KeyError:
        print('Ignoring award with no date %s' % str(a))
        return
    try:
        defaults = {}
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
        try:
            defaults['wdd_tournament_id'] = wdd_url_to_id(a['WDD URL'])
        except KeyError:
            pass
        PlayerAward.objects.update_or_create(player=player,
                                             tournament=a['Tournament'],
                                             date=date_str,
                                             name=award_name,
                                             defaults=defaults)
    except Exception:
        # Handle all exceptions
        # This way, we fail to add/update the single ranking rather than all the background
        print("Failed to save PlayerAward")
        print("player=%s, tournament=%s, date=%s, name=%s" % (str(player),
                                                              a['Tournament'],
                                                              date_str,
                                                              award_name))
        traceback.print_exc()


def _update_or_create_playerranking(player, r):
    """
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
        print("Failed to save PlayerRanking")
        print("player=%s, system=%s" % (str(player), r['Name']))
        traceback.print_exc()


def add_player_bg(player, include_wpe=False):
    """
    Cache background data for the player
    include_wpe=True will set PlayerTournamentRanking.wpe_score,
    which involves parsing an additional WDD page
    """
    # First check wikipedia
    bg = WikipediaBackground('%s %s' % (player.first_name, player.last_name))
    # Titles won
    titles = bg.titles()
    for title in titles:
        _update_or_create_playertournamentranking_wiki(player, title)
    # Do we have a WDD id for this player?
    wdd = player.wdd_player_id
    if not wdd:
        return
    bg = WDDBackground(wdd)
    wpe_scores = {}
    if include_wpe:
        # Construct a dict, keyed by WDD Id, of WPE scores
        for score in bg.wpe_scores():
            key = wdd_url_to_id(score['WDD WPE URL'])
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


class Player(models.Model):
    """
    A person who played Diplomacy
    """
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    wdd_player_id = models.PositiveIntegerField(unique=True,
                                                validators=[validate_wdd_player_id],
                                                verbose_name=_(u'WDD player id'),
                                                blank=True,
                                                null=True)
    backstabbr_username = models.CharField(max_length=40,
                                           blank=True,
                                           help_text=_('Username on the backstabbr website'))
    backstabbr_profile_url = models.URLField(blank=True)
    picture = models.ImageField(upload_to=player_picture_location, blank=True, null=True)
    location = models.CharField(max_length=60, blank=True)
    # Cache of the player's name in the WDD
    _wdd_name = models.CharField(max_length=60, blank=True)
    user = models.OneToOneField(User,
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE,
                                help_text=_('If the Player has an account on the site, record it here'))
    class Meta:
        ordering = ['last_name', 'first_name']

    def __init__(self, *args, **kwargs):
        super(Player, self).__init__(*args, **kwargs)
        self._old_wdd_id = self.wdd_player_id

    def __str__(self):
        return u'%s %s' % (self.first_name, self.last_name)

    def sortable_str(self):
        return u'%s, %s' % (self.last_name, self.first_name)

    def _clear_background(self):
        """
        Remove all background info on the Player from the database.
        This undoes add_player_bg()
        """
        self.playerranking_set.all().delete()
        self.playeraward_set.all().delete()
        self.playertournamentranking_set.all().delete()
        self.playergameresult_set.all().delete()

    def save(self, *args, **kwargs):
        # Clear cached WDD Name if WDD id has changed
        if (not self.wdd_player_id) or (self._old_wdd_id != self.wdd_player_id):
            self._wdd_name = ''
            self._clear_background()
        self._old_wdd_id = self.wdd_player_id
        super(Player, self).save(*args, **kwargs)

    def wdd_name(self):
        """Name for this player in the World Diplomacy Database."""
        if not self.wdd_player_id:
            return u''
        # Read from the WDD if we haven't cached it
        if not self._wdd_name:
            bg = WDDBackground(self.wdd_player_id)
            try:
                self._wdd_name = bg.wdd_name()
                super(Player, self).save(update_fields=['_wdd_name'])
            except WDDNotAccessible:
                # Not much we can do in this case
                return u''
            except InvalidWDDId as e:
                # This can only happen if we couldn't get to the WDD when wdd_player_id was validated
                raise ValidationError(_(u'WDD Id %(wdd_id)d is invalid'),
                                      params={'wdd_id': self.wdd_player_id}) from e
        return self._wdd_name

    def wdd_url(self):
        """URL for this player in the World Diplomacy Database."""
        if self.wdd_player_id:
            return WDD_BASE_RESULTS_URL + 'player_fiche.php?id_player=%d' % self.wdd_player_id
        return u''

    def wdd_firstname_lastname(self):
        """Name for this player as a 2-tuple, as in the WDD in preference."""
        if not self.wdd_player_id:
            return (self.first_name, self.last_name)
        bg = WDDBackground(self.wdd_player_id)
        try:
            return bg.wdd_firstname_lastname()
        except InvalidWDDId as e:
            # This can only happen if we couldn't get to the WDD when the Player was created
            raise ValidationError(_(u'WDD Id %(wdd_id)d is invalid'),
                                  params={'wdd_id': self.wdd_player_id}) from e
        except Exception:
            return (self.first_name, self.last_name)

    def tournamentplayers(self, including_unpublished=False):
        """Returns the set of TournamentPlayers for this Player."""
        if including_unpublished:
            return self.tournamentplayer_set.all()
        return self.tournamentplayer_set.filter(tournament__is_published=True)

    def _rankings(self, mask=MASK_ALL_BG):
        """List of all rankings"""
        results = []
        if (mask & MASK_RANKINGS) == 0:
            return results
        rankings_set = self.playerranking_set.all()
        for r in rankings_set:
            results.append('%s.' % str(r))
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

    def _tourney_rankings(self, mask=MASK_ALL_BG):
        """ List of titles won and tournament rankings"""
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
        if (mask & MASK_TITLES) != 0:
            # Add summaries of actual titles
            titles = {}
            for ranking in ranking_set:
                if ranking.title:
                    titles.setdefault(ranking.title, []).append(ranking.year)
            for key, lst in titles.items():
                results.append(str(self) + ' was ' + key + ' in ' + ', '.join(map(str, lst)) + '.')
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
        List of background strings about the player,
        optionally as a specific Great Power
        """
        if power is None:
            return self._tourney_rankings(mask=mask) + self._results(mask=mask) + self._awards(mask=mask) + self._rankings(mask=mask)
        return self._results(power, mask=mask) + self._awards(power, mask=mask)

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('player_detail', args=[str(self.id)])


class PlayerTournamentRanking(models.Model):
    """
    A tournament ranking for a player.
    Used to import background information from the WDD.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    tournament = models.CharField(max_length=60)
    position = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    date = models.DateField(blank=True, null=True)
    title = models.CharField(max_length=30, blank=True)
    wdd_tournament_id = models.PositiveIntegerField(validators=[validate_wdd_tournament_id],
                                                    verbose_name=_(u'WDD tournament id'),
                                                    blank=True,
                                                    null=True)
    wpe_score = models.FloatField(blank=True,
                                  null=True,
                                  help_text=_('World Performance Evaluation score'))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'tournament', 'year'],
                                    name='unique_player_tournament_year'),
        ]

    def __str__(self):
        pos = position_str(self.position)
        s = _(u'%(player)s came %(position)s at %(tournament)s') % {'player': self.player,
                                                                    'position': pos,
                                                                    'tournament': self.tournament}
        if self.tournament[-4:] != str(self.year):
            s += _(u' in %(year)d') % {'year': self.year}
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
    Used to import background information from the WDD.
    """

    tournament_name = models.CharField(max_length=60)
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

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(result__in=GameResults.values) | Q(result=''),
                                   name='%(class)s_result_valid'),
            models.UniqueConstraint(fields=['tournament_name', 'game_name', 'player', 'power'],
                                    name='unique_names_player_power'),
        ]

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
    tournament = models.CharField(max_length=60)
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

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'tournament', 'date', 'name'],
                                    name='unique_player_tournament_date_name'),
        ]

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

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'system'],
                                    name='unique_player_system'),
        ]

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
