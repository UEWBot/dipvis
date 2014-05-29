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

SPRING = 'S'
FALL = 'F'
SEASONS = (
    (SPRING, 'spring'),
    (FALL, 'fall'),
)

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
    wdd_player_id = models.PositiveIntegerField(unique=True)
    def __unicode__(self):
        return self.first_name + self.last_name

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
    def __unicode__(self):
        return self.name

class TournamentScore(models.Model):
    """
    One player's score in a tournament
    """
    player = models.ForeignKey(Player)
    tournament = models.ForeignKey(Tournament)
    score = models.PositiveIntegerField()
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
    final_year = models.PositiveSmallIntegerField(blank=True)
    earliest_end_time = models.DateTimeField(blank=True)
    latest_end_time = models.DateTimeField(blank=True)
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
    def __unicode__(self):
        return self.name

class DrawProposal(models.Model):
    """
    A single draw or concession proposal in a game
    """
    game = models.ForeignKey(Game)
    year = models.PositiveSmallIntegerField()
    season = models.CharField(max_length=1, choices=SEASONS)
    passed = models.BooleanField(blank=True)
    power_1 = models.ForeignKey(GreatPower, related_name='+')
    power_2 = models.ForeignKey(GreatPower, blank=True, related_name='+')
    power_3 = models.ForeignKey(GreatPower, blank=True, related_name='+')
    power_4 = models.ForeignKey(GreatPower, blank=True, related_name='+')
    power_5 = models.ForeignKey(GreatPower, blank=True, related_name='+')
    power_6 = models.ForeignKey(GreatPower, blank=True, related_name='+')
    power_7 = models.ForeignKey(GreatPower, blank=True, related_name='+')
    def __unicode__(self):
        return u'%s %d%s' % (self.game, self.year, self.season)

class GamePlayer(models.Model):
    """
    A person who played a Great Power in a Game
    """
    player = models.ForeignKey(Player)
    game = models.ForeignKey(Game)
    power = models.ForeignKey(GreatPower, related_name='+')
    first_year = models.PositiveSmallIntegerField(default=1)
    first_season = models.CharField(max_length=1, choices=SEASONS, default=SPRING)
    last_year = models.PositiveSmallIntegerField(blank=True)
    last_season = models.CharField(max_length=1, choices=SEASONS, blank=True)
    score = models.FloatField(blank=True)
    def __unicode__(self):
        return u'%s %s %s' % (self.game, self.player, self.power)

class CentreCount(models.Model):
    """
    The number of centres owned by one power at the end of a given game year
    """
    power = models.ForeignKey(GreatPower, related_name='+')
    game = models.ForeignKey(Game)
    year = models.PositiveSmallIntegerField()
    count = models.PositiveSmallIntegerField()
    def __unicode__(self):
        return u'%s %d %s %d' % (self.game, self.year, self.power.abbreviation, self.count)

