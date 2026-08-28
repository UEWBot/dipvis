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

from pathlib import Path

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Max, Min, Q
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from django_countries.fields import CountryField

from tournament.diplomacy import WINNING_SCS, GreatPower
from tournament.wdr import WDR_BASE_URL, validate_wdr_player_id

from .event_kinds import EventKinds
from .game_results import GameResults
from .position_str import position_str
from .wdr_background import InvalidWDRId, WDRBackground, WDRNotAccessible


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
MASK_BOARDS_TOPPED = 1 << 9
MASK_ROUND_ENDPOINTS = 1 << 10
MASK_BEST_COUNTRY = 1 << 11
MASK_OTHER_AWARDS = 1 << 12
MASK_RANKINGS = 1 << 13
MASK_SERIES_WINS = 1 << 14
MASK_TOP_BOARDS_PLAYED = 1 << 15
MASK_ALL_BG = (1 << 16) - 1


def player_picture_location(instance, filename):
    """
    Function that determines where to store the file.
    """
    # Stuff them all into one directory
    return Path('player_pictures', filename)


class Player(models.Model):
    """
    A person who played Diplomacy
    """
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
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
    user = models.OneToOneField(User,
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE,
                                help_text=_('If the Player has an account on the site, record it here'))

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('player_detail', args=[str(self.id)])

    def sortable_str(self):
        return f'{self.last_name}, {self.first_name}'

    def _clear_background(self):
        """
        Remove all background info on the Player from the database.

        This undoes add_player_bg()
        """
        self.playertitle_set.all().delete()
        self.playerranking_set.all().delete()
        self.playeraward_set.all().delete()
        self.playereventranking_set.all().delete()
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

        latest = self.playereventranking_set.aggregate(Max('updated'))['updated__max']
        if result is None:
            result = latest
        elif latest is not None:
            result = max(result, latest)

        latest = self.playergameresult_set.aggregate(Max('updated'))['updated__max']
        if result is None:
            result = latest
        elif latest is not None:
            result = max(result, latest)

        latest = self.playertitle_set.aggregate(Max('updated'))['updated__max']
        if result is None:
            result = latest
        elif latest is not None:
            result = max(result, latest)

        return result

    def wdr_url(self):
        """URL for this player in the World Diplomacy Reference."""
        if self.wdr_player_id:
            return f'{WDR_BASE_URL}players/{self.wdr_player_id}'
        return ''

    def wdr_name(self):
        """
        Returns the name of the player in the WDR as a string

        If the WDR is inaccessible, returns "".
        If the Player's WDR id is invalid, returns "(Invalid WDR Id)".
        """
        try:
            bg = WDRBackground(self.wdr_player_id)
        except WDRNotAccessible:
            return ''
        except InvalidWDRId:
            return '(Invalid WDR Id)'
        names = bg.firstname_lastname()
        return f'{names[0]} {names[1]}'

    def tournamentplayers(self, including_unpublished=False):
        """Returns the set of TournamentPlayers for this Player."""
        tps = self.tournamentplayer_set.select_related('tournament').order_by('-tournament__end_date')
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

    def _ranking_queryset(self, event_kind):
        """Return the base filtered tournament-ranking queryset for the current background view."""
        qs = self.playereventranking_set.filter(position__isnull=False)
        if event_kind is not None:
            qs = qs.filter(event_kind=event_kind)
        return qs

    def _awards(self, ranking_set, power=None, mask=MASK_ALL_BG):
        """List of all awards won, optionally as a specified power."""
        results = []
        award_set = self.playeraward_set.filter(event_ranking__in=ranking_set).order_by('event_ranking__date')
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
                else:
                    msg = ngettext('%(name)s has won Best %(power)s once.',
                                   '%(name)s has won Best %(power)s %(count)d times.',
                                   award_count)
                    results.append(msg % {'name': self,
                                          'power': p,
                                          'count': award_count})
                a = power_award_set.first()
                s = _('%(name)s first won %(award)s in %(year)d at %(event)s') % {'name': self,
                                                                                  'award': a.name,
                                                                                  'year': a.event_ranking.date.year,
                                                                                  'event': a.event_ranking.event_name}
                if a.final_sc_count:
                    s += _(' with %(dots)d Supply Centres') % {'dots': a.final_sc_count}
                s += '.'
                results.append(s)
                a = power_award_set.last()
                s = _('%(name)s most recently won %(award)s in %(year)d at %(event)s') % {'name': self,
                                                                                          'award': a.name,
                                                                                          'year': a.event_ranking.date.year,
                                                                                          'event': a.event_ranking.event_name}
                if a.final_sc_count:
                    s += _(' with %(dots)d Supply Centres') % {'dots': a.final_sc_count}
                s += '.'
                results.append(s)
        if (mask & MASK_OTHER_AWARDS) != 0:
            for a in award_set.filter(power=None):
                results.append(_('%(name)s won %(award)s at %(event)s.')
                               % {'name': self,
                                  'award': a.name,
                                  'event': a.event_ranking.event_name})
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

    def _tourney_rankings(self, ranking_set, an_event, event, events, mask=MASK_ALL_BG):
        """List of tournament rankings."""
        results = []
        ranking_set = ranking_set.order_by('date')
        plays = ranking_set.count()
        if plays == 0:
            if (mask & MASK_TOURNEY_COUNT) != 0:
                results.append(_(u'This is the first %(event)s %(name)s has competed in.')
                               % {'name': self, 'event': event})
            return results
        if (mask & MASK_TOURNEY_COUNT) != 0:
            results.append(ngettext('%(name)s has competed in one %(event)s.',
                                    '%(name)s has competed in %(number)d %(events)s.',
                                    plays)
                           % {'name': self,
                              'number': plays,
                              'event': event,
                              'events': events})
        if (mask & MASK_FIRST_TOURNEY) != 0:
            first = ranking_set.first()
            results.append(_(u'%(name)s first competed in %(an_event)s (%(event_name)s) in %(year)d.')
                           % {'name': self,
                              'event_name': first.event_name,
                              'year': first.date.year,
                              'an_event': an_event})
        if (mask & MASK_LAST_TOURNEY) != 0:
            last = ranking_set.last()
            results.append(_(u'%(name)s most recently competed in %(an_event)s (%(event_name)s) in %(year)d.')
                           % {'name': self,
                              'event_name': last.event_name,
                              'year': last.date.year,
                              'an_event': an_event})
        if (mask & MASK_BEST_TOURNEY_RESULT) != 0:
            wins_set = ranking_set.filter(position=1)
            wins = wins_set.count()
            if wins > 0:
                results.append(_(u'%(name)s has won %(wins)d of %(plays)d %(events)s (%(percentage).2f%%).')
                               % {'name': self,
                                  'plays': plays,
                                  'percentage': 100.0 * float(wins) / float(plays),
                                  'wins': wins,
                                  'events': events})
                w = wins_set.first()
                results.append(_('%(name)s won their first %(event)s (%(event_name)s) in %(year)d.')
                               % {'name': self,
                                  'event_name': w.event_name,
                                  'year': w.date.year,
                                  'event': event})
                w = wins_set.last()
                results.append(_('%(name)s most recently won %(an_event)s (%(event_name)s) in %(year)d.')
                               % {'name': self,
                                  'event_name': w.event_name,
                                  'year': w.date.year,
                                  'an_event': an_event})
            else:
                best = ranking_set.aggregate(Min('position'))['position__min']
                pos = position_str(best)
                results.append(_(u'The best %(event)s result for %(name)s is %(position)s.')
                               % {'name': self, 'position': pos, 'event': event})
        return results

    def _results(self, ranking_set, an_event, event, events, power=None, mask=MASK_ALL_BG):
        """
        List of tournament game achievements, optionally with one Great Power.
        """
        results = []
        results_set = self.playergameresult_set.filter(event_ranking__in=ranking_set)
        if power is not None:
            c_str = _(u' as %(power)s') % {'power': power}
            results_set = results_set.filter(power=power)
        else:
            c_str = u''
        games = results_set.count()
        if games == 0:
            if (mask & MASK_GAMES_PLAYED) != 0:
                results.append(_(u'%(name)s has never played%(power)s in %(an_event)s before.')
                               % {'name': self,
                                  'power': c_str,
                                  'an_event': an_event})
            return results
        if (mask & MASK_GAMES_PLAYED) != 0:
            msg = ngettext('%(name)s has played %(games)d %(event)s game%(power)s.',
                           '%(name)s has played %(games)d %(event)s games%(power)s.',
                           games)
            results.append(msg % {'name': self,
                                  'games': games,
                                  'power': c_str,
                                  'event': event})
        if (mask & MASK_BEST_SC_COUNT) != 0:
            best = results_set.aggregate(Max('final_sc_count'))['final_sc_count__max']
            # SC count is optional
            if best:
                results.append(_(u'%(name)s has finished with as many as %(dots)d centres%(power)s in %(event)s games.')
                               % {'name': self,
                                  'dots': best,
                                  'power': c_str,
                                  'event': event})
        if (mask & MASK_SOLO_COUNT) != 0:
            solos = results_set.filter(final_sc_count__gte=WINNING_SCS).count()
            if solos > 0:
                msg = ngettext('%(name)s has soloed %(solos)d of %(games)d %(event)s game played%(power)s (%(percentage).2f%%).',
                               '%(name)s has soloed %(solos)d of %(games)d %(event)s games played%(power)s (%(percentage).2f%%).',
                               games)
                results.append(msg % {'name': self,
                                      'solos': solos,
                                      'games': games,
                                      'power': c_str,
                                      'event': event,
                                      'percentage': 100.0 * float(solos) / float(games)})
            else:
                results.append(_(u'%(name)s has yet to solo%(power)s at %(an_event)s.')
                               % {'name': self,
                                  'power': c_str,
                                  'an_event': an_event})
        if (mask & MASK_ELIM_COUNT) != 0:
            query = Q(year_eliminated__isnull=False) | Q(final_sc_count=0)
            eliminations_set = results_set.filter(query)
            eliminations = eliminations_set.count()
            if eliminations > 0:
                msg = ngettext('%(name)s was eliminated in %(deaths)d of %(games)d %(event)s game played%(power)s (%(percentage).2f%%).',
                               '%(name)s was eliminated in %(deaths)d of %(games)d %(event)s games played%(power)s (%(percentage).2f%%).',
                               games)
                results.append(msg % {'name': self,
                                      'deaths': eliminations,
                                      'games': games,
                                      'power': c_str,
                                      'event': event,
                                      'percentage': 100.0 * float(eliminations) / float(games)})
            else:
                results.append(_(u'%(name)s has yet to be eliminated%(power)s in %(an_event)s.')
                               % {'name': self,
                                  'power': c_str,
                                  'an_event': an_event})
        if (mask & MASK_BOARDS_TOPPED) != 0:
            query = Q(result=GameResults.WIN) | Q(position=1)
            board_tops = results_set.filter(query).count()
            if board_tops > 0:
                msg = ngettext('%(name)s topped the board in %(tops)d of %(games)d %(event)s game played%(power)s (%(percentage).2f%%).',
                               '%(name)s topped the board in %(tops)d of %(games)d %(event)s games played%(power)s (%(percentage).2f%%).',
                               games)
                results.append(msg % {'name': self,
                                      'tops': board_tops,
                                      'games': games,
                                      'power': c_str,
                                      'event': event,
                                      'percentage': 100.0 * float(board_tops) / float(games)})
            else:
                results.append(_(u'%(name)s has yet to top the board%(power)s at %(an_event)s.')
                               % {'name': self,
                                  'power': c_str,
                                  'an_event': an_event})
        if (mask & MASK_TOP_BOARDS_PLAYED) != 0:
            top_board_games = results_set.filter(is_top_board=True).count()
            if top_board_games > 0:
                msg = ngettext('%(name)s has played %(count)d top board game%(power)s.',
                               '%(name)s has played %(count)d top board games%(power)s.',
                               top_board_games)
                results.append(msg % {'name': self,
                                      'count': top_board_games,
                                      'power': c_str,
                                      'event': event})
        return results

    def background(self, power=None, mask=MASK_ALL_BG, event_kind=None):
        """
        List of background strings about the player, optionally as a specific Great Power

        If event_kind is not supplied, all event kinds are included.
        """
        an_event, event, events = EventKinds.event_words(event_kind)
        ranking_set = self._ranking_queryset(event_kind)
        if power is None:
            return (self._titles(mask=mask) +
                    self._tourney_rankings(ranking_set=ranking_set, an_event=an_event, event=event, events=events, mask=mask) +
                    self._results(ranking_set=ranking_set, an_event=an_event, event=event, events=events, mask=mask) +
                    self._awards(ranking_set=ranking_set, mask=mask) +
                    self._rankings(mask=mask))
        return (self._results(ranking_set=ranking_set, an_event=an_event, event=event, events=events, power=power, mask=mask) +
                self._awards(ranking_set=ranking_set, power=power, mask=mask))
