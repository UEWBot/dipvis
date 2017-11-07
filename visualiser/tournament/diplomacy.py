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

# This file contains the basics of the standard game of Diplomacy.
# Which powers exist, how many Supply Centres there are, which colour
# represents each power, etc.

from django.db import models
from django.utils.translation import ugettext as _
from django.utils.encoding import python_2_unicode_compatible

from django.core.exceptions import ValidationError

import os

TOTAL_SCS = 34
WINNING_SCS = ((TOTAL_SCS/2)+1)

FIRST_YEAR = 1901

def validate_year(value):
    """
    Checks for a valid game year
    """
    if value < FIRST_YEAR:
        raise ValidationError(_(u'%(value)d is not a valid game year'), params = {'value': value})

def validate_year_including_start(value):
    """
    Checks for a valid game year, allowing 1900, too
    """
    if value < FIRST_YEAR-1:
        raise ValidationError(_(u'%(value)d is not a valid game year'), params = {'value': value})

def game_image_location(instance, filename):
    """
    Function that determines where to store the file.
    """
    if type(instance) == GameImage:
        game = instance.game
        tournament = game.the_round.tournament
        directory = os.path.join(tournament.name, game.name)
    else:
        directory = 'starting_positions'
    return os.path.join('games', directory, filename)

@python_2_unicode_compatible
class GreatPower(models.Model):
    """
    One of the seven great powers that can be played
    """
    name = models.CharField(max_length=20, unique=True)
    abbreviation = models.CharField(max_length=1, unique=True)
    starting_centres = models.PositiveIntegerField()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class GameSet(models.Model):
    """
    A Diplomacy board game set.
    Over the years, different sets have been produced with different pieces, maps, etc.
    The main purpose of separating this out is so that we can display SC counts with power
    colours matching those of any photos of the board.
    """
    name = models.CharField(max_length=20, unique=True)
    initial_image = models.ImageField(upload_to=game_image_location)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class SetPower(models.Model):
    """
    A single GreatPower in a given GameSet.
    """
    the_set = models.ForeignKey(GameSet, verbose_name=_(u'set'), on_delete=models.CASCADE)
    power = models.ForeignKey(GreatPower, on_delete=models.CASCADE)
    colour = models.CharField(max_length=20)

    class Meta:
        unique_together = ('the_set', 'power')

    def __str__(self):
        return _(u'%(power)s in %(the_set)s' % {'power': self.power.name, 'the_set': self.the_set.name})

