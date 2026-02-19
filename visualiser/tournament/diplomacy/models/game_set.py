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

from ..utils.game_image_location import game_image_location


class GameSet(models.Model):
    """
    A Diplomacy board game set.
    Over the years, different sets have been produced with different pieces,
    maps, etc.
    The main purpose of separating this out is so that we can display SC
    counts with power colours matching those of any photos of the board.
    """
    name = models.CharField(max_length=20, unique=True)
    initial_image = models.ImageField(upload_to=game_image_location)

    def __str__(self):
        return self.name