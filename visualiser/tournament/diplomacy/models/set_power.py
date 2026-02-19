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
from django.utils.translation import gettext as _

from .game_set import GameSet
from .great_power import GreatPower


class SetPower(models.Model):
    """
    A single GreatPower in a given GameSet.
    """
    the_set = models.ForeignKey(GameSet,
                                verbose_name=_(u'set'),
                                on_delete=models.CASCADE)
    power = models.ForeignKey(GreatPower, on_delete=models.CASCADE)
    colour = models.CharField(max_length=20)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['the_set', 'power'], name='unique_set_power')
        ]

    def __str__(self):
        return _(u'%(power)s in %(the_set)s') % {'power': self.power.name,
                                                 'the_set': self.the_set.name}
