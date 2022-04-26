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