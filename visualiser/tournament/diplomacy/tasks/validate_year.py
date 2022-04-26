from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from ..values.diplomacy_values import FIRST_YEAR

def validate_year(value):
    """
    Checks for a valid game year
    """
    if value < FIRST_YEAR:
        raise ValidationError(_(u'%(value)d is not a valid game year'),
                              params={'value': value})