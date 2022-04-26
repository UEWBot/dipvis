from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from ..values.diplomacy_values import FIRST_YEAR

def validate_year_including_start(value):
    """
    Checks for a valid game year, allowing 1900, too
    """
    if value < FIRST_YEAR-1:
        raise ValidationError(_(u'%(value)d is not a valid game year'),
                              params={'value': value})