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
Forms for the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.formsets import BaseFormSet
from django.utils.translation import gettext as _

from tournament.diplomacy import GameSet, GreatPower
from tournament.models import Game, Team, validate_game_name

from .fields import RoundPlayerChoiceField


class GamePlayersForm(forms.Form):
    """Form for players of a single game"""
    game_id = forms.IntegerField(required=False,
                                 widget=forms.HiddenInput())
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

    def __init__(self, *args, **kwargs):
        """
        Dynamically creates one player field per Great Power

        Only RoundPlayers in the specified Round and Pool (which may be None) can be picked.
        """
        # Remove our special kwargs from the list
        self.the_round = kwargs.pop('the_round')
        self.pool = kwargs.pop('pool')
        super().__init__(*args, **kwargs)

        try:
            game_id = kwargs['initial']['game_id']
        except KeyError:
            pass
        else:
            game = Game.objects.get(pk=game_id)
            assert (game.pool == self.pool) or (self.pool is None)
            # We may have a form with games for the whole round, some for each pool
            # This form should be restricted to the pool the game is for
            self.pool = game.pool
        # Restrict to players from the relevant Pool
        queryset = self.the_round.roundplayer_set.filter(pool=self.pool).prefetch_related('player').order_by('player')

        field_order = ['name', 'the_set', 'top_board', 'external_url']

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            self.fields[c] = RoundPlayerChoiceField(flag_sandboxers=True,
                                                    label=_(c),
                                                    queryset=queryset)
            field_order.append(c)

        # Put notes at the end
        field_order.append('notes')
        self.order_fields(field_order)

    def clean(self):
        """
        Checks that the Game is reasonable

        Checks that no player is playing multiple powers.
        If the Game is in a team round, checks that no two players are from the same team.
        """
        cleaned_data = super().clean()
        r_players = []
        for power in GreatPower.objects.all():
            c = power.name
            r_player = cleaned_data.get(c)
            # If the field itself didn't validate, drop out
            if r_player is None:
                return cleaned_data
            if r_player in r_players:
                raise forms.ValidationError(_('Player %(player)s appears more than once')
                                            % {'player': r_player.player})
            r_players.append(r_player)
        if self.the_round.is_team_round:
            teams = []
            for rp in r_players:
                try:
                    team = rp.player.team_set.get(tournament=self.the_round.tournament)
                except Team.DoesNotExist:
                    continue
                if team in teams:
                    raise forms.ValidationError(_('Multiple players from team %(team)s')
                                                % {'team': team.name})
                teams.append(team)

        return cleaned_data


class BaseGamePlayersFormset(BaseFormSet):
    """Form to specify GamePlayers for a single Round, or single Pool within a Round"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.the_round = kwargs.pop('the_round')
        self.pool = kwargs.pop('pool')  # May be None
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special args down to the form itself
        kwargs['the_round'] = self.the_round
        kwargs['pool'] = self.pool
        return super()._construct_form(index, **kwargs)

    def clean(self):
        if any(self.errors):
            # One or more forms is invalid anyway
            return
        # Any duplicates within the page ?
        names = []
        for form in self.forms:
            try:
                names.append(form.cleaned_data['name'])
            except KeyError:
                # This happens when we have a form left blank
                pass
        if len(set(names)) != len(names):
            raise forms.ValidationError(_('Game names must be unique within the tournament'))
