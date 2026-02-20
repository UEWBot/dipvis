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

from .great_power import GreatPower


class SupplyCentre(models.Model):
    """
    A supply centre on the Diplomacy board.
    """
    name = models.CharField(max_length=20, unique=True)
    abbreviation = models.CharField(max_length=4, unique=True)
    initial_owner = models.ForeignKey(GreatPower,
                                      on_delete=models.CASCADE,
                                      null=True,
                                      blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
