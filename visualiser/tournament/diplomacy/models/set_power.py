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
        unique_together = ('the_set', 'power')

    def __str__(self):
        return _(u'%(power)s in %(the_set)s') % {'power': self.power.name,
                                                 'the_set': self.the_set.name}
