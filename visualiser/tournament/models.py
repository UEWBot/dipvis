# Diplomacy Tournament Visualiser
# Copyright (C) 2014 Chris Brand
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

from django.db import models
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Min, Sum, Q

from tournament.background import Background

import urllib2, random

SPRING = 'S'
FALL = 'F'
SEASONS = (
    (SPRING, 'spring'),
    (FALL, 'fall'),
)

FIRST_YEAR = 1901

TOTAL_SCS = 34
WINNING_SCS = ((TOTAL_SCS/2)+1)

# These happen to co-incide with the coding used by the WDD
GAME_RESULT = (
    ('W', 'Win'),
    ('D2', '2-way draw'),
    ('D3', '3-way draw'),
    ('D4', '4-way draw'),
    ('D5', '5-way draw'),
    ('D6', '6-way draw'),
    ('D7', '7-way draw'),
    ('L', 'Loss'),
)

def validate_year(value):
    """
    Checks for a valid game year
    """
    if value < FIRST_YEAR:
        raise ValidationError(u'%s is not a valid game year' % value)

def validate_sc_count(value):
    """
    Checks for a valid SC count
    """
    if value < 0 or value > TOTAL_SCS:
        raise ValidationError(u'%s is not a valid SC count' % value)

def validate_wdd_id(value):
    """
    Checks a WDD id
    """
    url = u'http://world-diplomacy-database.com/php/results/player_fiche.php?id_player=%d' % value
    p = urllib2.urlopen(url)
    if p.geturl() != url:
        raise ValidationError(u'%d is not a valid WDD Id' % value)

class GreatPower(models.Model):
    """
    One of the seven great powers that can be played
    """
    name = models.CharField(max_length=20, unique=True)
    abbreviation = models.CharField(max_length=1, unique=True)
    colour = models.CharField(max_length=20)
    class Meta:
        ordering = ['name']
    def __unicode__(self):
        return self.name

TITLE_MAP = {
    'World Champion' : 1,
    'North American Champion' : 1,
    'Winner' : 1,
    'European Champion' : 1,
    'Second' : 2,
    'Third' : 3,
}

def add_player_bg(player):
    """
    Cache background data for the player
    """
    wdd = player.wdd_player_id
    if wdd:
        bg = Background(wdd)
        # Titles won
        titles = bg.titles()
        for title in titles:
            pos = None
            the_title = None
            for key,val in TITLE_MAP.iteritems():
                try:
                    if title[key] == unicode(player):
                        pos = val
                        if key.find('Champion') != -1:
                            the_title = key
                except KeyError:
                    pass
            if pos:
                i, created = PlayerRanking.objects.get_or_create(player=player,
                                                                 tournament=title['Tournament'],
                                                                 position=pos,
                                                                 year=title['Year'])
                if the_title:
                    i.title = the_title
                i.save()
        # Podium finishes
        finishes = bg.finishes()
        for finish in finishes:
            d = finish['Date']
            i,created = PlayerRanking.objects.get_or_create(player=player,
                                                            tournament=finish['Tournament'],
                                                            position=finish['Position'],
                                                            year=d[:4])
            i.date = d
            i.save()
        # Tournaments
        tournaments = bg.tournaments()
        for t in tournaments:
            d = t['Date']
            try:
                i,created = PlayerRanking.objects.get_or_create(player=player,
                                                                tournament=t['Name of the tournament'],
                                                                position=t['Rank'],
                                                                year=d[:4])
                i.date = d
                i.save()
            except KeyError:
                # No rank implies they were the TD or similar - just ignore that tournament
                print("Ignoring %s for %s" % (t['Name of the tournament'], player))
                pass
        # Boards
        boards = bg.boards()
        for b in boards:
            try:
                power = b['Country']
                p=GreatPower.objects.get(name__contains=power)
            except GreatPower.DoesNotExist:
                # Apparently not a Standard game
                continue
            i,created = PlayerGameResult.objects.get_or_create(tournament_name=b['Name of the tournament'],
                                                               game_name=b['Round / Board'],
                                                               player=player,
                                                               power=p,
                                                               date = b['Date'],
                                                               position = b['Position'])
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
            i.save()

def position_str(position):
    """
    Returns the string version of the position e.g. '1st', '12th'.
    """
    result = unicode(position)
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
    return result

class Player(models.Model):
    """
    A person who played Diplomacy
    """
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    wdd_player_id = models.PositiveIntegerField(unique=True, verbose_name='WDD player id', blank=True, null=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __unicode__(self):
        return u'%s %s' % (self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        super(Player, self).save(*args, **kwargs)
        add_player_bg(self)

    def clean(self):
        # Check that the WDD id seems to match the name
        bg = Background(self.wdd_player_id)
        wdd_name = bg.name()
        raise ValidationError, u'WDD Id %d is for %s, not %s %s' % (self.wdd_player_id, wdd_name, self.first_name, self.last_name)

    def _rankings(self):
        """ List of titles won and tournament rankings"""
        results = []
        ranking_set = self.playerranking_set.order_by('year')
        plays = ranking_set.count()
        wins = ranking_set.filter(position=1).count()
        best = ranking_set.aggregate(Min('position'))['position__min']
        # Add summaries of actual titles
        titles = {}
        for ranking in ranking_set:
            if ranking.title:
                if ranking.title not in titles:
                    titles[ranking.title] = []
                titles[ranking.title].append(ranking.year)
        for key, lst in titles.iteritems():
            results.append(str(self) + ' was ' + key + ' in ' + ', '.join(map(str, lst)))
        # Add summaries of tournament rankings
        if plays > 0:
            results.append(u'%s has competed in %d tournament(s)' % (self, plays))
            first = ranking_set.first()
            results.append(u'%s first competed in a tournament (%s) in %d' % (self, first.tournament, first.year))
            last = ranking_set.last()
            results.append(u'%s most recently competed in a tournament (%s) in %d' % (self, last.tournament, last.year))
            if wins > 1:
                results.append(u'%s has won %d tournaments' % (self, wins))
            elif wins > 0:
                results.append(u'%s has won %d tournament' % (self, wins))
            else:
                pos = position_str(best)
                results.append(u'The best tournament result for %s is %s' % (self, pos))
        return results

    def _results(self, power=None):
        """ List of tournament game achievements, optionally with one Great Power """
        results = []
        results_set = self.playergameresult_set.order_by('year')
        if power:
            results_set = results_set.filter(power=power)
            c_str = u' as %s' % power
        else:
            c_str = ''
        games = results_set.count()
        if games == 0:
            results.append(u'%s has never played%s in a tournament before' % (self, c_str))
            return results
        results.append(u'%s has played %d tournament games%s' % (self, games, c_str))
        solo_set = results_set.filter(final_sc_count__gte=WINNING_SCS)
        solos = solo_set.count()
        if solos > 0:
            results.append(u'%s has soloed %d of %d tournament games played%s (%.2f%%)' % (self, solos, games, c_str, 100.0*float(solos)/float(games)))
        else:
            results.append(u'%s has yet to solo%s at a tournament' % (self, c_str))
        query = Q(year_eliminated__isnull=False) | Q(final_sc_count=0)
        eliminations_set = results_set.filter(query)
        eliminations = eliminations_set.count()
        if eliminations > 0:
            results.append(u'%s was eliminated in %d of %d tournament games played%s (%.2f%%)' % (self, eliminations, games, c_str, 100.0*float(eliminations)/float(games)))
        else:
            results.append(u'%s has yet to be eliminated%s in a tournament' % (self, c_str))
        query = Q(result='W') | Q(position=1)
        victories_set = results_set.filter(query)
        board_tops = victories_set.count()
        if board_tops > 0:
            results.append(u'%s topped the board in %d of %d tournament games played%s (%.2f%%)' % (self, board_tops, games, c_str, 100.0*float(board_tops)/float(games)))
        else:
            results.append(u'%s has yet to top the board%s at a tournament' % (self, c_str))
        return results

    def background(self, power=None):
        """
        List of background strings about the player, optionally as a specific Great Power
        """
        if not power:
            return self._rankings() + self._results()
        return self._results(power)

class ScoringSystem(models.Model):
    """
    A system for assigning scores to players of a single game
    """
    name = models.CharField(max_length=30)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

class Tournament(models.Model):
    """
    A Diplomacy tournament
    """
    name = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()

    def background(self):
        players = Player.objects.filter(tournamentplayer__tournament = self)
        results = []
        for p in players:
            results += p.background()
        # Shuffle the resulting list
        random.shuffle(results)
        return results

    def is_finished(self):
        for r in self.round_set.all():
            if not r.is_finished():
                return False
        return True

    def get_absolute_url(self):
        return reverse('tournament_detail', args=[str(self.id)])

    def __unicode__(self):
        return self.name

class TournamentPlayer(models.Model):
    """
    One player in a tournament
    """
    player = models.ForeignKey(Player)
    tournament = models.ForeignKey(Tournament)
    score = models.FloatField(default=0.0)

    def __unicode__(self):
        return u'%s %s %f' % (self.tournament, self.player, self.score)

    def save(self, *args, **kwargs):
        super(TournamentPlayer, self).save(*args, **kwargs)
        add_player_bg(self.player)

class Round(models.Model):
    """
    A single round of a tournament
    """
    tournament = models.ForeignKey(Tournament)
    number = models.PositiveSmallIntegerField()
    scoring_system = models.ForeignKey(ScoringSystem)
    dias = models.BooleanField(verbose_name='Draws Include All Survivors')
    final_year = models.PositiveSmallIntegerField(blank=True, null=True, validators=[validate_year])
    earliest_end_time = models.DateTimeField(blank=True, null=True)
    latest_end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['number']

    def is_finished(self):
        gs = self.game_set.all()
        if len(gs) == 0:
            # Rounds with no games can't have started
            return False
        for g in gs:
            if not g.is_finished:
                return False
        return True

    def get_absolute_url(self):
        return reverse('round_detail', args=[str(self.tournament.id), str(self.number)])

    def __unicode__(self):
        return u'%s round %d' % (self.tournament, self.number)

class Game(models.Model):
    """
    A single game of Diplomacy
    """
    name = models.CharField(max_length=20)
    started_at = models.DateTimeField()
    is_finished = models.BooleanField(default=False)
    is_top_board = models.BooleanField(default=False)
    the_round = models.ForeignKey(Round, verbose_name='round')

    class Meta:
        ordering = ['name']

    def is_dias(self):
        """
        Returns whether the game is Draws Include All Survivors
        """
        return self.the_round.dias

    def years_played(self):
        """
        Returns a list of years for which there are SC counts for this game
        """
        scs = self.centrecount_set.all()
        return sorted(list(set([sc.year for sc in scs])))

    def players(self, latest=True):
        """
        Returns a dict, keyed by power, of lists of players of that power
        If latest is True, only inlcude the latest player of each power
        """
        powers = GreatPower.objects.all()
        gps = self.gameplayer_set.all().order_by('-first_year')
        retval = {}
        for power in powers:
            ps = gps.filter(power=power)
            if latest:
                ps = ps[0:1]
            retval[power] = [gp.player for gp in ps]
        return retval

    def background(self):
        players_by_power = self.players(latest=True)
        results = []
        for c,players in players_by_power.iteritems():
            for p in players:
                results += p.background(c)
        # Shuffle the resulting list
        random.shuffle(results)
        return results

    def result_str(self):
        """
        Returns a string representing the game result, if any, or None
        """
        # Did a draw proposal pass ?
        try:
            dp = self.drawproposal_set.filter(passed=True).get()
            sz = dp.draw_size()
            if sz == 1:
                retval = u'Game conceded to '
            else:
                retval = u'Game ended as a draw between '
            winners = []
            for n in range(1,sz+1):
                value = dp.__dict__['power_%d_id' % n]
                power = GreatPower.objects.get(pk=value)
                winners.append(power.name)
            return retval + ', '.join(winners)
        except DrawProposal.DoesNotExist:
            pass
        # Did a power reach 18 centres ?
        final_year = self.years_played()[-1]
        scs = self.centrecount_set.filter(year=final_year).order_by('-count')
        if scs[0].count >= WINNING_SCS:
            return u'Game won by %s' % scs[0].power.name
        # TODO Did the game get to the fixed endpoint ?
        if self.is_finished:
            return u'Game ended'
        # Then it seems to be ongoing
        return None

    def get_absolute_url(self):
        return reverse('game_detail', args=[str(self.the_round.tournament.id), self.name])

    def __unicode__(self):
        return self.name

class DrawProposal(models.Model):
    """
    A single draw or concession proposal in a game
    """
    game = models.ForeignKey(Game)
    year = models.PositiveSmallIntegerField(validators=[validate_year])
    season = models.CharField(max_length=1, choices=SEASONS)
    passed = models.BooleanField()
    proposer = models.ForeignKey(GreatPower, related_name='+')
    power_1 = models.ForeignKey(GreatPower, related_name='+')
    power_2 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+')
    power_3 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+')
    power_4 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+')
    power_5 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+')
    power_6 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+')
    power_7 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+')

    def draw_size(self):
        count = 0
        for name, value in self.__dict__.iteritems():
            if name.startswith('power_'):
                if value:
                    count += 1
        return count

    def clean(self):
        # No skipping powers
        found_null = False
        for n in range(1,8):
            if not self.__dict__['power_%d_id' % n]:
                found_null = True
            elif found_null:
                raise ValidationError('Draw powers should go as early as possible')
        # Each power must be unique
        powers = set()
        for name, value in self.__dict__.iteritems():
            if value and name.startswith('power_'):
                if value in powers:
                    power = GreatPower.objects.get(pk=value)
                    raise ValidationError('%s present more than once' % power)
                powers.add(value)
        # Only one successful draw proposal
        if self.passed:
            try:
                p = DrawProposal.objects.filter(game=self.game, passed=True).get()
                if p != self:
                    raise ValidationError('Game already has a successful draw proposal')
            except DrawProposal.DoesNotExist:
                pass
        # No dead powers included
        # If DIAS, all alive powers must be included
        dias = self.game.is_dias()
        year = self.game.years_played()[-1]
        scs = self.game.centrecount_set.filter(year=final_year)
        for sc in scs:
            if sc.power in powers:
                if sc.count == 0:
                    raise ValidationError('Dead power %s included in proposal' % sc.power)
            else:
                if dias and sc.count > 0:
                    raise ValidationError('Missing alive power %s in DIAS game' % sc.power)

    def __unicode__(self):
        return u'%s %d%s' % (self.game, self.year, self.season)

class RoundPlayer(models.Model):
    """
    A person who played a round in a tournament
    """
    player = models.ForeignKey(Player)
    the_round = models.ForeignKey(Round, verbose_name='round')
    score = models.FloatField(default=0.0)

    def clean(self):
        # Player should already be in the tournament
        t = self.the_round.tournament
        tp = self.player.tournamentplayer_set.filter(tournament=t)
        if not tp:
            raise ValidationError('Player is not yet in the tournament')

    def __unicode__(self):
        return u'%s in %s' % (self.player, self.the_round)

class GamePlayer(models.Model):
    """
    A person who played a Great Power in a Game
    """
    player = models.ForeignKey(Player)
    game = models.ForeignKey(Game)
    power = models.ForeignKey(GreatPower, related_name='+')
    # TODO Ensure no overlapping players, or gaps
    first_year = models.PositiveSmallIntegerField(default=FIRST_YEAR, validators=[validate_year])
    first_season = models.CharField(max_length=1, choices=SEASONS, default=SPRING)
    last_year = models.PositiveSmallIntegerField(blank=True, null=True, validators=[validate_year])
    last_season = models.CharField(max_length=1, choices=SEASONS, blank=True)
    score = models.FloatField(default=0.0)

    def clean(self):
        # Player should already be in the tournament
        t = self.game.the_round.tournament
        tp = self.player.tournamentplayer_set.filter(tournament=t)
        if not tp:
            raise ValidationError('Player is not yet in the tournament')

    def __unicode__(self):
        return u'%s %s %s' % (self.game, self.player, self.power)

class CentreCount(models.Model):
    """
    The number of centres owned by one power at the end of a given game year
    """
    power = models.ForeignKey(GreatPower, related_name='+')
    game = models.ForeignKey(Game)
    year = models.PositiveSmallIntegerField(validators=[validate_year])
    count = models.PositiveSmallIntegerField(validators=[validate_sc_count])

    class Meta:
        unique_together = ('power', 'game', 'year')

    def clean(self):
        # Not possible to more than double your count in one year
        # or to recover from an elimination
        if self.year > FIRST_YEAR:
            try:
                prev = CentreCount.objects.filter(power=self.power, game=self.game, year=self.year-1).get()
                if self.count > 2 * prev.count:
                    raise ValidationError('SC count for a power should not more than double in a year')
                elif (prev.count == 0) and (self.count > 0):
                    raise ValidationError('SC count cannot increase from zero')
            except DrawProposal.DoesNotExist:
                # We're obviously missing a year - let that go
                pass

    def __unicode__(self):
        return u'%s %d %s %d' % (self.game, self.year, self.power.abbreviation, self.count)

class PlayerRanking(models.Model):
    """
    A tournament ranking for a player
    """
    player = models.ForeignKey(Player)
    tournament = models.CharField(max_length=30)
    position = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    date = models.DateField(blank=True, null=True)
    title = models.CharField(max_length=30, blank=True, null=True)

    def __unicode__(self):
        pos = position_str(self.position)
        s = u'%s came %s at %s' % (self.player, pos, self.tournament)
        if self.tournament[-4:] != unicode(self.year):
            s += u' in %d' % self.year
        return s

class PlayerGameResult(models.Model):
    """
    One player's result for a tournament game
    """
    tournament_name = models.CharField(max_length=20)
    game_name = models.CharField(max_length=20)
    player = models.ForeignKey(Player)
    power = models.ForeignKey(GreatPower, related_name='+')
    date = models.DateField()
    position = models.PositiveSmallIntegerField()
    position_equals = models.PositiveSmallIntegerField(blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    final_sc_count = models.PositiveSmallIntegerField(blank=True, null=True)
    result = models.CharField(max_length=2, choices=GAME_RESULT, blank=True, null=True)
    year_eliminated = models.PositiveSmallIntegerField(blank=True, null=True, validators=[validate_year])

    class Meta:
        unique_together = ('tournament_name', 'game_name', 'player', 'power')

    def __unicode__(self):
        return u'%s played %s in %s' % (self.player, self.power, self.game_name)

