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

import re
import traceback
import urllib.request

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max, Min, Q
from django.urls import reverse
from django.utils.translation import ugettext as _

from tournament.background import WikipediaBackground, WDDBackground, WDD_BASE_URL
from tournament.background import InvalidWDDId, WDDNotAccessible
from tournament.diplomacy import WINNING_SCS, GreatPower, validate_year

# These happen to co-incide with the coding used by the WDD
WIN = 'W'
DRAW_2 = 'D2'
DRAW_3 = 'D3'
DRAW_4 = 'D4'
DRAW_5 = 'D5'
DRAW_6 = 'D6'
DRAW_7 = 'D7'
LOSS = 'L'
GAME_RESULT = (
    (WIN, _('Win')),
    (DRAW_2, _('2-way draw')),
    (DRAW_3, _('3-way draw')),
    (DRAW_4, _('4-way draw')),
    (DRAW_5, _('5-way draw')),
    (DRAW_6, _('6-way draw')),
    (DRAW_7, _('7-way draw')),
    (LOSS, _('Loss')),
)
# Mapping from an integer to the corresponding WIN or DRAW_n constant
TO_GAME_RESULT = {
    1: WIN,
    2: DRAW_2,
    3: DRAW_3,
    4: DRAW_4,
    5: DRAW_5,
    6: DRAW_6,
    7: DRAW_7,
}

# Mask values to choose which background strings to include
MASK_TITLES = 1<<0
MASK_TOURNEY_COUNT = 1<<1
MASK_FIRST_TOURNEY = 1<<2
MASK_LAST_TOURNEY = 1<<3
MASK_BEST_TOURNEY_RESULT = 1<<4
MASK_GAMES_PLAYED = 1<<5
MASK_BEST_SC_COUNT = 1<<6
MASK_SOLO_COUNT = 1<<7
MASK_ELIM_COUNT = 1<<8
MASK_BOARD_TOP_COUNT = 1<<9
MASK_ROUND_ENDPOINTS = 1<<10
MASK_BEST_COUNTRY = 1<<11
MASK_OTHER_AWARDS = 1<<12
MASK_RANKINGS = 1<<13
MASK_ALL_BG = (1<<14)-1

TITLE_MAP = {
    'World Champion' : 1,
    'North American Champion' : 1,
    'Winner' : 1,
    'European Champion' : 1,
    'Second' : 2,
    'Third' : 3,
}

def validate_wdd_player_id(value):
    """
    Checks a WDD player id
    """
    url = WDD_BASE_URL + 'player_fiche.php?id_player=%d' % value
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
    url = WDD_BASE_URL + 'tournament_class.php?id_tournament=%d' % value
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

def add_player_bg(player):
    """
    Cache background data for the player
    """
    # First check wikipedia
    bg = WikipediaBackground('%s %s' % (player.first_name, player.last_name))
    # Titles won
    titles = bg.titles()
    for title in titles:
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
                i = PlayerTournamentRanking.objects.get_or_create(player=player,
                                                                  tournament=title['Tournament'],
                                                                  position=pos,
                                                                  year=title['Year'])[0]
                if the_title:
                    i.title = the_title
                i.save()
            except:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print("Failed to save PlayerTournamentRanking")
                print("player=%s, tournament=%s, position=%s, year=%s" % (str(player),
                                                                          title['Tournament'],
                                                                          pos,
                                                                          title['Year']))
                traceback.print_exc()
    # Do we have a WDD id for this player?
    wdd = player.wdd_player_id
    if not wdd:
        return
    bg = WDDBackground(wdd)
    # Podium finishes
    finishes = bg.finishes()
    for finish in finishes:
        d = finish['Date']
        try:
            i = PlayerTournamentRanking.objects.get_or_create(player=player,
                                                              tournament=finish['Tournament'],
                                                              position=finish['Position'],
                                                              year=d[:4])[0]
            i.date = d
            # Ignore if not present
            try:
                i.wdd_tournament_id = wdd_url_to_id(finish['WDD URL'])
            except KeyError:
                pass
            i.save()
        except:
            # Handle all exceptions
            # This way, we fail to add/update the single ranking rather than all the background
            print("Failed to save PlayerTournamentRanking")
            print("player=%s, tournament=%s, position=%s, year=%s" % (str(player),
                                                                      finish['Tournament'],
                                                                      finish['Position'],
                                                                      d[:4]))
            traceback.print_exc()
    # Tournaments
    tournaments = bg.tournaments()
    for t in tournaments:
        d = t['Date']
        try:
            i = PlayerTournamentRanking.objects.get_or_create(player=player,
                                                              tournament=t['Name of the tournament'],
                                                              position=t['Rank'],
                                                              year=d[:4])[0]
            i.date = d
            # Ignore if not present
            try:
                i.wdd_tournament_id = wdd_url_to_id(t['WDD URL'])
            except KeyError:
                pass
            i.save()
        except KeyError:
            # No rank implies they were the TD or similar - just ignore that tournament
            print("Ignoring unranked %s for %s" % (t['Name of the tournament'], player))
        except:
            # Handle all other exceptions
            # This way, we fail to add/update the single ranking rather than all the background
            print("Failed to save PlayerTournamentRanking")
            print("player=%s, tournament=%s, position=%s, year=%s" % (str(player),
                                                                      t['Name of the tournament'],
                                                                      t['Rank'],
                                                                      d[:4]))
            traceback.print_exc()
    # Boards
    boards = bg.boards()
    for b in boards:
        try:
            power = b['Country']
            p = GreatPower.objects.get(name__contains=power)
        except GreatPower.DoesNotExist:
            # Apparently not a Standard game
            continue
        try:
            i = PlayerGameResult.objects.get_or_create(tournament_name=b['Name of the tournament'],
                                                       game_name=b['Round / Board'],
                                                       player=player,
                                                       power=p,
                                                       date=b['Date'],
                                                       position=b['Position'])[0]
            # If there's no 'Position sharing', they were alone at that position
            try:
                i.position_equals = b['Position sharing']
            except KeyError:
                i.position_equals = 1
            # Ignore any of these that aren't present
            try:
                i.score = b['Score']
            except KeyError:
                pass
            try:
                i.final_sc_count = b['Final SCs']
            except KeyError:
                pass
            try:
                i.result = b['Game end']
            except KeyError:
                pass
            try:
                i.year_eliminated = b['Elimination year']
            except KeyError:
                pass
            try:
                i.wdd_tournament_id = wdd_url_to_id(b['WDD Tournament URL'])
            except KeyError:
                pass
            i.save()
        except:
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
    # Awards
    awards = bg.awards()
    for k, v in awards.items():
        # Go through the list of awards
        for a in v:
            if k == 'Awards':
                award_name = a['Name']
            else:
                try:
                    p = GreatPower.objects.get(name__contains=k)
                except GreatPower.DoesNotExist:
                    # Apparently not a Standard game
                    continue
                award_name = 'Best %s' % p
            # Some of the WDD pages are badly-structured with nested tables
            # Ignore any messed-up results
            try:
                date_str = a['Date']
                if len(date_str) != 10:
                    print('Ignoring award with bad date %s' % str(a))
                    continue
            except KeyError:
                print('Ignoring award with no date %s' % str(a))
                continue
            try:
                i = PlayerAward.objects.get_or_create(player=player,
                                                      tournament=a['Tournament'],
                                                      date=date_str,
                                                      name=award_name)[0]
                if k != 'Awards':
                    i.power = p
                # Ignore any of these that aren't present
                try:
                    i.score = a['Score']
                except KeyError:
                    pass
                try:
                    i.final_sc_count = a['SCs']
                except KeyError:
                    pass
                try:
                    i.wdd_tournament_id = wdd_url_to_id(a['WDD URL'])
                except KeyError:
                    pass
                i.save()
            except:
                # Handle all exceptions
                # This way, we fail to add/update the single ranking rather than all the background
                print("Failed to save PlayerAward")
                print("player=%s, tournament=%s, date=%s, name=%s" % (str(player),
                                                                      a['Tournament'],
                                                                      date_str,
                                                                      award_name))
                traceback.print_exc()
    # Rankings
    rankings = bg.rankings()
    for r in rankings:
        try:
            i = PlayerRanking.objects.get_or_create(player=player,
                                                    system=r['Name'])[0]
            i.score = float(r['Score'])
            i.international_rank = r['International rank']
            i.national_rank = r['National rank']
            i.save()
        except:
            # Handle all exceptions
            # This way, we fail to add/update the single ranking rather than all the background
            print("Failed to save PlayerRanking")
            print("player=%s, system=%s" % (str(player), r['Name']))
            traceback.print_exc()

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
    picture = models.ImageField(upload_to=player_picture_location, blank=True, null=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return u'%s %s' % (self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        super(Player, self).save(*args, **kwargs)
        add_player_bg(self)

    def wdd_name(self):
        """Name for this player in the World Diplomacy Database."""
        if not self.wdd_player_id:
            return u''
        bg = WDDBackground(self.wdd_player_id)
        try:
            return bg.wdd_name()
        except WDDNotAccessible:
            # Not much we can do in this case
            return u''
        except InvalidWDDId:
            # This can only happen if we couldn't get to the WDD when the Player was created
            raise ValidationError(_(u'WDD Id %(wdd_id)d is invalid'),
                                  params={'wdd_id': self.wdd_player_id})

    def wdd_url(self):
        """URL for this player in the World Diplomacy Database."""
        if self.wdd_player_id:
            return WDD_BASE_URL + 'player_fiche.php?id_player=%d' % self.wdd_player_id
        return u''

    def wdd_firstname_lastname(self):
        """Name for this player as a 2-tuple, as in the WDD in preference."""
        if not self.wdd_player_id:
            return (self.first_name, self.last_name)
        bg = WDDBackground(self.wdd_player_id)
        try:
            return bg.wdd_firstname_lastname()
        except InvalidWDDId:
            # This can only happen if we couldn't get to the WDD when the Player was created
            raise ValidationError(_(u'WDD Id %(wdd_id)d is invalid'),
                                  params={'wdd_id': self.wdd_player_id})
        except:
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
        if power:
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
            results.append(_(u'%(name)s has competed in %(number)d tournament(s).')
                           % {'name': self, 'number': plays})
        if (mask & MASK_TITLES) != 0:
            # Add summaries of actual titles
            titles = {}
            for ranking in ranking_set:
                if ranking.title:
                    if ranking.title not in titles:
                        titles[ranking.title] = []
                    titles[ranking.title].append(ranking.year)
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
        """ List of tournament game achievements, optionally with one Great Power """
        results = []
        results_set = self.playergameresult_set.all()
        if power:
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
            query = Q(result=WIN) | Q(position=1)
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
        if not power:
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

    def __str__(self):
        pos = position_str(self.position)
        s = _(u'%(player)s came %(position)s at %(tournament)s') % {'player': self.player,
                                                                    'position': pos,
                                                                    'tournament': self.tournament}
        if self.tournament[-4:] != str(self.year):
            s += _(u' in %(year)d') % {'year': self.year}
        return s

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
    final_sc_count = models.PositiveSmallIntegerField(blank=True, null=True)
    result = models.CharField(max_length=2, choices=GAME_RESULT, blank=True)
    year_eliminated = models.PositiveSmallIntegerField(blank=True,
                                                       null=True,
                                                       validators=[validate_year])
    wdd_tournament_id = models.PositiveIntegerField(validators=[validate_wdd_tournament_id],
                                                    verbose_name=_(u'WDD tournament id'),
                                                    blank=True,
                                                    null=True)

    class Meta:
        unique_together = ('tournament_name', 'game_name', 'player', 'power')

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
        unique_together = ('player', 'tournament', 'date', 'name')

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
        unique_together = ('player', 'system')

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
