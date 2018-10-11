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

"""
This module provides classes describing the core Diplomacy board game.

If we ever want to support variants, then these are the definitions
that will need to differ for different variants.
"""

import os

from django.db import models
from django.utils.translation import ugettext as _

from django.core.exceptions import ValidationError

TOTAL_SCS = 34
WINNING_SCS = ((TOTAL_SCS/2)+1)

FIRST_YEAR = 1901

def validate_year(value):
    """
    Checks for a valid game year
    """
    if value < FIRST_YEAR:
        raise ValidationError(_(u'%(value)d is not a valid game year'),
                              params = {'value': value})

def validate_year_including_start(value):
    """
    Checks for a valid game year, allowing 1900, too
    """
    if value < FIRST_YEAR-1:
        raise ValidationError(_(u'%(value)d is not a valid game year'),
                              params = {'value': value})

def validate_ranking(value):
    """
    Checks for a valid power rank - 1..7
    """
    if value < 1:
        raise ValidationError(_('%(value)d is not a valid ranking'),
                              params = {'value': value})
    if value > GreatPower.objects.count():
        raise ValidationError(_('%(value)d is not a valid ranking'),
                              params = {'value': value})

def validate_preference_string(the_string):
    """
    Checks that the string represents a valid power preference list.
    It must only consist of the single-letter abbreviations for the great powers
    (upper or lower case), with each present at most once.
    """
    # Convert the preference string to all uppercase
    the_string = the_string.upper()
    # Check for duplicated powers in the string
    if len(the_string) != len(set(the_string)):
        raise ValidationError(_('%(prefs)s contains duplicate characters'),
                              params = {'prefs': the_string})
    # Check for invalid powers in the string
    all_powers = set()
    for p in GreatPower.objects.all():
        all_powers.add(p.abbreviation)
    invalid = set(the_string) - all_powers
    if len(invalid):
        raise ValidationError(_('%(prefs)s contains invalid character(s)'),
                              params = {'prefs': the_string})

def game_image_location(instance, filename):
    """
    Function that determines where to store the file.
    """
    return os.path.join('games', 'starting_positions', filename)

class GreatPower(models.Model):
    """
    One of the seven great powers that can be played
    """
    name = models.CharField(max_length=20, unique=True)
    abbreviation = models.CharField(max_length=1, unique=True)

    @property
    def starting_centres(self):
        """
        How many centres does the power start with?
        """
        return self.supplycentre_set.count()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

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
        return _(u'%(power)s in %(the_set)s' % {'power': self.power.name,
                                                'the_set': self.the_set.name})

class SupplyCentre(models.Model):
    """
    A supply centre on the Diplomacy board.
    """
    name = models.CharField(max_length=20, unique=True)
    abbreviation = models.CharField(max_length=4, unique=True)
    initial_owner = models.ForeignKey(GreatPower, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
