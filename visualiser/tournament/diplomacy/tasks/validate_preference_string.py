from django.core.exceptions import ValidationError

from ..models.great_power import GreatPower

def validate_preference_string(the_string):
    """
    Checks that the string represents a valid power preference list.
    It must only contain the single-letter abbreviations for the great powers
    (upper or lower case), with each present at most once.
    """
    # Convert the preference string to all uppercase
    the_string = the_string.upper()
    # Check for duplicated powers in the string
    if len(the_string) != len(set(the_string)):
        raise ValidationError(_('%(prefs)s contains duplicate characters'),
                              params={'prefs': the_string})
    # Check for invalid powers in the string
    all_powers = set()
    for p in GreatPower.objects.all():
        all_powers.add(p.abbreviation)
    invalid = set(the_string) - all_powers
    if invalid:
        raise ValidationError(_('%(prefs)s contains invalid character(s)'),
                              params={'prefs': the_string})