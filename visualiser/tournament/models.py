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

SPRING = 'S'
FALL = 'F'
SEASONS = (
    (SPRING, 'spring'),
    (FALL, 'fall'),
)

def validate_year(value):
    """
    Checks for a valid game year
    """
    if value < 1901:
        raise ValidationError(u'%s is not a valid game year' % value)

def validate_sc_count(value):
    """
    Checks for a valid SC count
    """
    if value < 0 or value > 34:
        raise ValidationError(u'%s is not a valid SC count' % value)

def validate_wdd_id(value):
    """
    Checks a WDD id
    """
    url = u'http://world-diplomacy-database.com/php/results/player_fiche.php?id_player=%d' % value
    # TODO Check that the URL doesn't redirect

class GreatPower(models.Model):
    """
    One of the seven great powers that can be played
    """
    name = models.CharField(max_length=20, unique=True)
    abbreviation = models.CharField(max_length=1, unique=True)
    def __unicode__(self):
        return self.name

class Player(models.Model):
    """
    A person who played Diplomacy
    """
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    wdd_player_id = models.PositiveIntegerField(unique=True, verbose_name='WDD player id', blank=True, null=True)
    def __unicode__(self):
        return u'%s %s' % (self.first_name, self.last_name)

class ScoringSystem(models.Model):
    """
    A system for assigning scores to players of a single game
    """
    name = models.CharField(max_length=30)
    def __unicode__(self):
        return self.name

class Tournament(models.Model):
    """
    A Diplomacy tournament
    """
    name = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
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
    first_year = models.PositiveSmallIntegerField(default=1901, validators=[validate_year])
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
    def __unicode__(self):
        return u'%s %d %s %d' % (self.game, self.year, self.power.abbreviation, self.count)

