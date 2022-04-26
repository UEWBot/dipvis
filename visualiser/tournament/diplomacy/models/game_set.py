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