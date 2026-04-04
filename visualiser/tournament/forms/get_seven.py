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
Forms for getting seven in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.utils.translation import gettext as _

from .fields import RoundPlayerChoiceField


class GetSevenPlayersForm(forms.Form):
    """Form to enter players to sit out or play two games"""

    LABELS = {'sitter': _('Player sitting out'),
              'standby': _('Standby player who will play'),
              'double': _('Player to play two games')}

    def __create_player_fields(self, queryset, prefix, count):
        """Do the actual field creation"""
        for i in range(count):
            self.fields[f'{prefix}_{i}'] = RoundPlayerChoiceField(queryset=queryset,
                                                                  required=False,
                                                                  label=self.LABELS[prefix])

    def __init__(self, *args, **kwargs):
        """
        Dynamically creates the appropriate number of player fields

        Only RoundPlayers in the specified Round and Pool (which may be None) can be picked.
        """
        # Remove our special kwargs from the list
        self.the_round = kwargs.pop('the_round')
        self.pool = kwargs.pop('pool')  # May be None

        assert (self.pool is None) or (self.pool.board_count is None)

        present = self.the_round.roundplayer_set.filter(pool=self.pool).prefetch_related('player').order_by('player')
        playing = present.filter(standby=False)
        standbys = present.filter(standby=True)

        # Overridable default initial value, like ModelForm
        if 'initial' not in kwargs.keys():
            initial = {}
            sitters = 0
            doublers = 0
            for rp in playing:
                if rp.game_count == 0:
                    initial[f'sitter_{sitters}'] = rp
                    sitters += 1
                if rp.game_count == 2:
                    initial[f'double_{doublers}'] = rp
                    doublers += 1
            standing = 0
            for rp in standbys:
                initial[f'standby_{standing}'] = rp
                standing += 1
            kwargs['initial'] = initial

        super().__init__(*args, **kwargs)

        # Figure out how many standbys, sitters and doubles we need
        # If we have an exact multiple of 7 with no standbys playing, perfect
        # Otherwise, if can get there with some or all standbys playing, do that
        # Otherwise, either all standbys play and some people play two boards
        #            or no standbys play and some others also sit the round out
        playing_count = playing.count()
        standby_count = standbys.count()
        self.all_standbys_needed = False
        if playing_count % 7 == 0:
            # Perfect !
            self.sitters = 0
            self.doubles = 0
            self.standbys = 0
        else:
            # How many more players do we need to make up another full board?
            short = 7 - (playing_count % 7)
            if standby_count == short:
                # Need all standbys to play, so no need to pick them
                self.sitters = 0
                self.doubles = 0
                self.standbys = 0
                self.all_standbys_needed = True
            elif standby_count > short:
                # Just need some standbys to play
                self.sitters = 0
                self.doubles = 0
                self.standbys = short
            else:
                # Either need some who want to play to sit out
                self.sitters = playing_count % 7
                # Or all standbys play and some people play two boards
                self.doubles = short - standby_count
                # If we need all the standbys, we won't get the user to pick them
                self.standbys = 0

        # Create the right number of player fields
        self.__create_player_fields(standbys, 'standby', self.standbys)
        self.__create_player_fields(playing, 'sitter', self.sitters)
        # We might have standbys willing to play two games, so choose from all present
        self.__create_player_fields(present, 'double', self.doubles)

    def _check_duplicates(self, cleaned_data, prefix, count):
        """Does the check for a player entered multiple times"""
        round_players = []
        for i in range(count):
            rp = cleaned_data.get(f'{prefix}_{i}')
            # If the field is empty, ignore it
            if rp is None:
                continue
            if rp in round_players:
                raise forms.ValidationError(_('Player %(player)s appears more than once')
                                            % {'player': rp.player})
            round_players.append(rp)
        return len(round_players)

    def clean(self):
        """
        Validate the form

        Checks that no player is entered more than once,
        that we have either sitters or (standbys or doubles), but not both,
        and that we have the right number of either sitters or (standbys and doubles).
        """
        cleaned_data = super().clean()

        standbys = self._check_duplicates(cleaned_data, 'standby', self.standbys)
        sitters = self._check_duplicates(cleaned_data, 'sitter', self.sitters)
        doubles = self._check_duplicates(cleaned_data, 'double', self.doubles)

        if (doubles > 0) and (sitters > 0):
            raise forms.ValidationError(_('Either have players sit out the round or have players play two games'))

        if 0 < standbys < self.standbys:
            raise forms.ValidationError(_('Too few standby players selected to play. Got %(actual)d, expected %(expected)d')
                                        % {'actual': standbys,
                                           'expected': self.standbys})
        if 0 < sitters < self.sitters:
            raise forms.ValidationError(_('Too few players sitting out games. Got %(actual)d, expected %(expected)d')
                                        % {'actual': sitters,
                                           'expected': self.sitters})
        if 0 < doubles < self.doubles:
            raise forms.ValidationError(_('Too few players playing two games. Got %(actual)d, expected %(expected)d')
                                        % {'actual': doubles,
                                           'expected': self.doubles})
        # Note that we always require all standbys to play before anyone is asked to play
        # two boards, so there's no danger of a standby player being listed in doubles
        # but not in standbys

        # Also, we only allow either sitters or doubles, so we already error out if
        # the same player is listed in both

        # If the user has chosen to have people play two games,
        # we need all standby players to play, too
        if doubles > 0:
            self.all_standbys_needed = True

        return cleaned_data
