# Diplomacy Tournament Visualiser
# Copyright (C) 2020 Chris Brand
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
from django.utils.translation import gettext_lazy


class GreatPower(models.Model):
    """
    One of the seven great powers that can be played
    """
    name = models.CharField(max_length=20, unique=True, verbose_name=gettext_lazy('name'))
    abbreviation = models.CharField(max_length=1,
                                    unique=True,
                                    verbose_name=gettext_lazy('abbreviation'))

    class Meta:
        ordering = ['name']
        verbose_name = gettext_lazy('great power')
        verbose_name_plural = gettext_lazy('great powers')

    def __str__(self):
        return self.name

    @property
    def starting_centres(self):
        """
        How many centres does the power start with?
        """
        return self.supplycentre_set.count()
