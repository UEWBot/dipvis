from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from ..models.great_power import GreatPower

def validate_ranking(value):
    """
    Checks for a valid power rank - 1..7
    """
    if value < 1:
        raise ValidationError(_('%(value)d is not a valid ranking'),
                              params={'value': value})
    if value > GreatPower.objects.count():
        raise ValidationError(_('%(value)d is not a valid ranking'),
                              params={'value': value})