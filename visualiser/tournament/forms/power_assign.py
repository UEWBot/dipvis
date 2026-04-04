# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2026 Chris Brand
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

"""
Forms for power assignment in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.formsets import BaseFormSet
from django.utils.translation import gettext as _

from tournament.diplomacy import GameSet, GreatPower
from tournament.models import Game, validate_game_name


class PowerAssignForm(forms.Form):
    """Form for players of a single game"""
    name = forms.CharField(label=_(u'Game Name'),
                           max_length=Game.MAX_NAME_LENGTH,
                           validators=[validate_game_name],
                           widget=forms.TextInput(attrs={'size': f'{Game.MAX_NAME_LENGTH}'}))
    the_set = forms.ModelChoiceField(label=_(u'Game Set'),
                                     queryset=GameSet.objects.all())
    top_board = forms.BooleanField(required=False)
    external_url = forms.URLField(label=_('URL'),
                                  required=False)
    notes = forms.CharField(required=False,
                            max_length=Game.MAX_NOTES_LENGTH)

    issues = forms.CharField(label=_('Issues'),
                             required=False,
                             disabled=True)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one GreatPower field per RoundPlayer"""
        # Remove our special kwarg from the list
        self.game = kwargs.pop('game')
        super().__init__(*args, **kwargs)

        queryset = GreatPower.objects.all()

        field_order = ['name', 'the_set', 'top_board', 'external_url']

        # Create the right player fields
        for gp in self.game.gameplayer_set.order_by('power__abbreviation'):
            c = str(gp.id)
            # flag if they are able to sandbox
            suffix = ''
            if gp.roundplayer().sandboxer:
                suffix = '*'
            label = str(gp.player) + suffix
            self.fields[c] = forms.ModelChoiceField(label=label,
                                                    queryset=queryset)
            field_order.append(c)

        # Put notes and issues at the end
        field_order.extend(['notes', 'issues'])
        self.order_fields(field_order)

    def clean(self):
        """Checks that no power is played by multiple players"""
        cleaned_data = super().clean()
        powers = []
        for player in self.game.gameplayer_set.order_by():
            c = str(player.id)
            power = cleaned_data.get(c)
            # If the field itself didn't validate, drop out
            if power is None:
                return cleaned_data
            if power in powers:
                raise forms.ValidationError(_('Power %(power)s appears more than once')
                                            % {'power': power})
            powers.append(power)

        return cleaned_data


class BasePowerAssignFormset(BaseFormSet):
    """Form to assign GreatPowers to all GamePlayers for a single Round"""
    def __init__(self, *args, **kwargs):
        # This formset only makes sense if the Games already exist and have GamePlayers assigned
        assert self.extra == 0
        # Remove our special kwarg from the list
        self.the_round = kwargs.pop('the_round')
        super().__init__(*args, **kwargs)
        self.games = self.the_round.game_set.order_by('name')
        assert self.games

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['game'] = self.games[index]
        return super()._construct_form(index, **kwargs)

    def clean(self):
        if any(self.errors):
            # One or more forms is invalid anyway
            return
        # Any duplicates within the page ?
        names = [form.cleaned_data['name'] for form in self.forms]
        if len(set(names)) != len(names):
            raise forms.ValidationError(_('Game names must be unique within the tournament'))
