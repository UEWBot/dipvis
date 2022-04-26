from django.db import models


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