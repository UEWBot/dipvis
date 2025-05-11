# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2019 Chris Brand
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
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.forms.formsets import BaseFormSet
from django.utils.translation import gettext as _

from tournament import backstabbr
from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.models.supply_centre import SupplyCentre
from tournament.diplomacy.values.diplomacy_values import TOTAL_SCS, FIRST_YEAR
from tournament.diplomacy.tasks.validate_preference_string import validate_preference_string
from tournament.models import Award, Game, GameImage, SeederBias
from tournament.models import DrawSecrecy, Seasons
from tournament.models import Team, TournamentPlayer
from tournament.models import validate_game_name
from tournament.players import Player


# Fields

class PlayerChoiceField(forms.ModelChoiceField):
    """Field to pick a Player"""
    def label_from_instance(self, obj):
        return obj.sortable_str()


class RoundPlayerChoiceField(forms.ModelChoiceField):
    """Field to pick a RoundPlayer"""
    def label_from_instance(self, obj):
        # flag if they are willing to sandbox
        suffix = ''
        if obj.sandboxer:
            suffix = '*'
        return obj.player.sortable_str() + suffix


class TournamentPlayerChoiceField(forms.ModelChoiceField):
    """Field to pick a TournamentPlayer"""
    def label_from_instance(self, obj):
        return obj.player.sortable_str()


class TournamentPlayerMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Field to pick TournamentPlayers"""
    def label_from_instance(self, obj):
        return obj.player.sortable_str()


# Awards

class AwardsForm(forms.Form):
    """Form to give one Award to TournamentPlayers"""
    award = forms.ModelChoiceField(queryset=Award.objects.all(),
                                   widget=forms.HiddenInput())
    players = TournamentPlayerMultipleChoiceField(queryset=TournamentPlayer.objects.none(),
                                                  required=False)

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        tournament = kwargs.pop('tournament')
        award_name = kwargs.pop('award_name')
        super().__init__(*args, **kwargs)
        # TODO we could create this queryset just once, in the formset
        self.fields['players'].queryset = tournament.tournamentplayer_set.filter(unranked=False)
        # Set the label to the award's name
        self.fields['players'].label = award_name


class BaseAwardsFormset(BaseFormSet):
    """Formset for giving Awards to TournamentPlayers"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        # Get the list of Awards
        self.awards = list(self.tournament.awards.all())
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            # And construct initial data from it
            # __init__() uses len(initial) to decide how many forms to create
            initial = []
            for award in self.awards:
                tps = [tp.id for tp in self.tournament.tournamentplayer_set.filter(awards=award).all()]
                initial.append({'award': award.id, 'players': tps})
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special kwargs down to the form itself
        kwargs['tournament'] = self.tournament
        kwargs['award_name'] = str(self.awards[index])
        return super()._construct_form(index, **kwargs)


# Backstabbr URL entry

class BackstabbrUrlForm(forms.Form):
    """Form to provide a backstabbr game URL"""
    url = forms.URLField(label=_('Backstabbr Game URL'))

    def clean_url(self):
        url = self.cleaned_data['url']
        # Check that it seems to be a backstabbr game
        try:
            g = backstabbr.Game(url, skip_read=True)
        except backstabbr.InvalidGameUrl as e:
            raise ValidationError(_('Not a valid backstabbr game URL'))
        return url


# Self Check-in

class SelfCheckInForm(forms.Form):
    """Form for one TournamentPlayer to selfcheck-in for a single Round"""
    playing = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tp = kwargs.pop('tp')
        self.round = kwargs.pop('round')
        super().__init__(*args, **kwargs)
        # Set the label appropriately
        label = _('Round %(number)d') % {'number': self.round.number()}
        if self.round.is_finished:
            label += _(' (Finished)')
        elif not self.round.enable_check_in:
            label += _(' (Self-check-in not yet allowed)')
        elif self.round.game_set.exists():
            label += _(' (Self-check-in closed)')
        self.fields['playing'].label = label
        # Set read-only if it's too late or if self-check-in isn't enabled
        readonly = (not self.round.enable_check_in) or self.round.game_set.exists()
        if readonly:
            self.fields['playing'].disabled = True


class BaseCheckInFormset(BaseFormSet):
    """Formset to provide self-check-in for every Round for a single TournamentPlayer"""
    def __init__(self, *args, **kwargs):
        # Remove our kwarg from the list
        self.tp = kwargs.pop('tp')
        # Get the list of Rounds
        self.rounds = list(self.tp.tournament.round_set.all())
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            initial = []
            for r in self.rounds:
                initial.append({'playing': r.roundplayer_set.filter(player=self.tp.player).exists()})
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['tp'] = self.tp
        kwargs['round'] = self.rounds[index]
        return super()._construct_form(index, **kwargs)


# Handicaps

class HandicapForm(forms.Form):
    """Form to set one TournamentPlayer's handicap"""
    handicap = forms.FloatField()

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tp = kwargs.pop('tp')
        # Overridable default initial value, like ModelForm
        if 'initial' not in kwargs.keys():
            kwargs['initial'] = {'handicap': self.tp.handicap}
        super().__init__(*args, **kwargs)
        # Set the label to the player's name
        self.fields['handicap'].label = str(self.tp.player)


class BaseHandicapsFormset(BaseFormSet):
    """Formset for setting handicaps for TournamentPlayers"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        # Get the list of TournamentPlayers
        self.tps = list(self.tournament.tournamentplayer_set.all())
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            # And construct initial data from it
            # __init__() uses len(initial) to decide how many forms to create
            initial = []
            for tp in self.tps:
                initial.append({'handicap': tp.handicap})
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['tp'] = self.tps[index]
        return super()._construct_form(index, **kwargs)


# Teams

class TeamForm(forms.Form):
    """Form to create/edit one Team"""
    name = forms.CharField(max_length=Team.MAX_NAME_LENGTH,
                           strip=True,
                           required=True)

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        try:
            self.team = kwargs.pop('team')
        except KeyError:
            self.team = None
        # Create an appropriate number of player fields
        queryset = Player.objects.filter(tournamentplayer__in=self.tournament.tournamentplayer_set.all()).distinct()
        # Overridable default initial value, like ModelForm
        # TODO This is dead code if we only ever use the formset
        if 'initial' not in kwargs.keys():
            if self.team:
                initial = {'name': self.team.name}
                for i, p in enumerate(self.team.players.all()):
                    initial[f'player_{i}'] = p
                kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        for n in range(self.tournament.team_size):
            # We allow Teams with as few as one player
            self.fields[f'player_{n}'] = PlayerChoiceField(queryset=queryset,
                                                           required=n==0)

    def clean(self):
        """
        Checks that the Team is reasonable

        Checks for the same player appearing multiple times
        """
        cleaned_data = super().clean()
        players = []
        for n in range(self.tournament.team_size):
            try:
                players.append(cleaned_data[f'player_{n}'])
            except KeyError:
                # If there are already errors, cleaned_data may not include all fields
                continue
        for p in players:
            if p and (players.count(p) > 1):
                raise forms.ValidationError(_('Player %(player)s appears more than once')
                                            % {'player': p})
        return cleaned_data


class BaseTeamsFormset(BaseFormSet):
    """Formset for editing Teams"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        # Get the list of Teams
        self.teams = list(self.tournament.team_set.all())
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            # And construct initial data from it
            # __init__() uses len(initial) to decide how many forms to create
            initial = []
            for tm in self.teams:
                d = {'name': tm.name}
                for i, p in enumerate(tm.players.all()):
                    d[f'player_{i}'] = p
                initial.append(d)
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special args down to the form itself
        kwargs['tournament'] = self.tournament
        # TODO is the if statement needed?
        if index < len(self.teams):
            kwargs['team'] = self.teams[index]
        return super()._construct_form(index, **kwargs)

    def clean(self):
        """
        Check for problems with the list of teams

        Checks for players in multiple teams
        """
        if any(self.errors):
            # One or more forms is invalid anyway
            return
        # Any duplicates within the page ?
        players = []
        for form in self.forms:
            for n in range(self.tournament.team_size):
                players.append(form.cleaned_data[f'player_{n}'])
        for p in players:
            if p and (players.count(p) > 1):
                raise forms.ValidationError(_('Player %(player)s appears in multiple teams')
                                                % {'player': p})


# Great Power preferences

class PrefsForm(forms.Form):
    """Form for one TournamentPlayer's Preferences"""
    prefs = forms.CharField(max_length=7,
                            strip=True,
                            required=False,
                            validators=[validate_preference_string])

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        # Store the TournamentPlayer so the view can set the right one
        self.tp = kwargs.pop('tp')
        # Overridable default initial value, like ModelForm
        if 'initial' not in kwargs.keys():
            kwargs['initial'] = {'prefs': self.tp.prefs_string()}
        super().__init__(*args, **kwargs)
        # Set the label to the player's name
        self.fields['prefs'].label = str(self.tp.player)


class BasePrefsFormset(BaseFormSet):
    """Form to specify Preferences for every TournamentPlayer"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        # Get the list of TournamentPlayers
        self.tps = list(self.tournament.tournamentplayer_set.all())
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            # And construct initial data from it
            # __init__() uses len(initial) to decide how many forms to create
            initial = []
            for tp in self.tps:
                initial.append({'prefs': tp.prefs_string()})
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['tp'] = self.tps[index]
        return super()._construct_form(index, **kwargs)


# Draws

class DrawForm(forms.Form):
    """Form for a draw vote"""
    year = forms.IntegerField(min_value=FIRST_YEAR)
    season = forms.ChoiceField(choices=Seasons.choices)
    proposer = forms.ModelChoiceField(queryset=GreatPower.objects.all(),
                                      required=False,
                                      to_field_name='name')

    def __init__(self, *args, **kwargs):
        """Adds powers field if concession or DIAS"""
        # Remove our special kwargs from the list
        concession = kwargs.pop('concession')
        is_dias = kwargs.pop('dias')
        secrecy = kwargs.pop('secrecy')
        player_count = kwargs.pop('player_count')
        super().__init__(*args, **kwargs)

        if concession:
            self.fields['powers'] = forms.ModelChoiceField(queryset=GreatPower.objects.all(),
                                                           label=_('Concede to'),
                                                           to_field_name='name')
        elif not is_dias:
            self.fields['powers'] = forms.ModelMultipleChoiceField(queryset=GreatPower.objects.all(),
                                                                   to_field_name='name',
                                                                   widget=forms.SelectMultiple(attrs={'size': '7'}))
        if secrecy == DrawSecrecy.SECRET:
            self.fields['passed'] = forms.BooleanField(initial=False,
                                                       required=False)
        elif secrecy == DrawSecrecy.COUNTS:
            self.fields['votes_in_favour'] = forms.IntegerField(min_value=0,
                                                                max_value=player_count)
        else:
            raise AssertionError(f'Unexpected draw secrecy value {secrecy}')


# Game scoring

class GameScoreForm(forms.Form):
    """Form for score for a single game"""
    name = forms.CharField(label=_(u'Game Name'),
                           max_length=Game.MAX_NAME_LENGTH,
                           disabled=True)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one score field per Great Power"""
        super().__init__(*args, **kwargs)

        attrs = self.fields['name'].widget.attrs
        attrs['size'] = attrs['maxlength']

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            # Don't require a score for every player
            self.fields[c] = forms.FloatField(required=False)
            self.fields[c].label = _(c)
            attrs = self.fields[c].widget.attrs
            attrs['size'] = 10
            attrs['maxlength'] = 10


# Game seeding

class GamePlayersForm(forms.Form):
    """Form for players of a single game"""
    game_id = forms.IntegerField(required=False,
                                 widget=forms.HiddenInput())
    name = forms.CharField(label=_(u'Game Name'),
                           max_length=Game.MAX_NAME_LENGTH,
                           validators=[validate_game_name])
    the_set = forms.ModelChoiceField(label=_(u'Game Set'),
                                     queryset=GameSet.objects.all())
    external_url = forms.URLField(label=_('URL'),
                                  required=False)
    notes = forms.CharField(required=False,
                            max_length=Game.MAX_NOTES_LENGTH)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one player field per Great Power"""
        # Remove our special kwarg from the list
        self.the_round = kwargs.pop('the_round')
        super().__init__(*args, **kwargs)

        attrs = self.fields['name'].widget.attrs
        attrs['size'] = attrs['maxlength']

        queryset = self.the_round.roundplayer_set.prefetch_related('player')

        field_order = ['name', 'the_set', 'external_url']

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            self.fields[c] = RoundPlayerChoiceField(queryset)
            self.fields[c].label = _(c)
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
    """Form to specify GamePlayers for a single Round"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.the_round = kwargs.pop('the_round')
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['the_round'] = self.the_round
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


# Power assignment

class PowerAssignForm(forms.Form):
    """Form for players of a single game"""
    name = forms.CharField(label=_(u'Game Name'),
                           max_length=Game.MAX_NAME_LENGTH,
                           validators=[validate_game_name],
                           widget=forms.TextInput(attrs={'size': f'{Game.MAX_NAME_LENGTH}'}))
    the_set = forms.ModelChoiceField(label=_(u'Game Set'),
                                     queryset=GameSet.objects.all())
    external_url = forms.URLField(label=_('URL'),
                                  required=False)
    notes = forms.CharField(required=False,
                            max_length=Game.MAX_NOTES_LENGTH)

    issues = forms.CharField(label=_('Issues'),
                             required=False,
                             disabled=True)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one GreatPower field per RoundPlayer"""
        # Remove our special kwargs from the list
        self.game = kwargs.pop('game')
        super().__init__(*args, **kwargs)

        queryset = GreatPower.objects.all()

        field_order = ['name', 'the_set', 'external_url']

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
        for player in self.game.gameplayer_set.all():
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
        # Remove our special kwargs from the list
        self.the_round = kwargs.pop('the_round')
        super().__init__(*args, **kwargs)
        self.games = self.the_round.game_set.all()
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


# Players sitting out or playing two games

class GetSevenPlayersForm(forms.Form):
    """Form to enter players to sit out or play two games"""

    LABELS = {'sitter': _('Player sitting out'),
              'standby': _('Standby player who will play'),
              'double': _('Player to play two games')}

    def __create_player_fields(self, queryset, prefix, count):
        """Do the actual field creation"""
        for i in range(count):
            self.fields[f'{prefix}_{i}'] = RoundPlayerChoiceField(queryset,
                                                                  required=False,
                                                                  label=self.LABELS[prefix])

    def __init__(self, *args, **kwargs):
        """Dynamically creates the appropriate number of player fields"""
        # Remove our special kwargs from the list
        self.the_round = kwargs.pop('the_round')

        present = self.the_round.roundplayer_set.prefetch_related('player')
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


# Supply Centre ownership

class SCOwnerForm(forms.Form):
    """Form for Supply Centre ownership for one year"""
    # Allow for an initial game-start SC ownership
    year = forms.IntegerField(min_value=FIRST_YEAR-1, required=False)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one owner field per SupplyCentre"""
        super().__init__(*args, **kwargs)

        self.fields['year'].widget.attrs['size'] = 4

        # Create the right country fields
        for sc in SupplyCentre.objects.all():
            self.fields[sc.name] = forms.ModelChoiceField(GreatPower.objects.all(),
                                                          required=False)


class BaseSCOwnerFormset(BaseFormSet):
    """Form to specify who owned which SupplyCentre when for a Game"""
    def clean(self):
        """
        Checks that no year appears more than once
        """
        if any(self.errors):
            return
        years = []
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            year = form.cleaned_data.get('year')
            if not year:
                # Blank form
                continue
            if year in years:
                raise forms.ValidationError(_('Year %(year)s appears more than once')
                                            % {'year': year})
            years.append(year)
        years.sort()
        # Check that SCs never become neutral
        for sc in SupplyCentre.objects.all():
            # Find all the listed owners for this dot
            owners = {}
            for i in range(0, self.total_form_count()):
                form = self.forms[i]
                year = form.cleaned_data.get('year')
                owner = form.cleaned_data.get(sc.name)
                owners[year] = (owner, form)
            # Check through them
            owned = False
            for key in years:
                owner, form = owners[key]
                if owner:
                    owned = True
                if owned and not owner:
                    form.add_error(sc.name,
                                   _('Supply Centres should never change from owned to neutral'))


# Registration fee payment

class PaidForm(forms.Form):
    """Form that just provides a checkbox to indicate that a TournamentPlayer has paid"""
    paid = forms.BooleanField(label=_('Paid'),
                              required=False,
                              initial=False)

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tp = kwargs.pop('tp')
        super().__init__(*args, **kwargs)
        self.fields['paid'].label = str(self.tp.player)


class BasePaidFormset(BaseFormSet):
    """Form to specify which TournamentPlayers have paid"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            initial = []
            for tp in self.tournament.tournamentplayer_set.all():
                initial.append({'paid': tp.paid})
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        self.tps = self.tournament.tournamentplayer_set.all()

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['tp'] = self.tps[index]
        return super()._construct_form(index, **kwargs)



# Game ended

class GameEndedForm(forms.Form):
    """Form that just provides a checkbox to indicate that a Game is over"""
    is_finished = forms.BooleanField(label=_('Game ended'),
                                     required=False,
                                     initial=False)


# Great power death year

class DeathYearForm(forms.Form):
    """Form for elimination year of each power"""

    # One shared label, because we expect the form to be displayed in a table
    label = forms.CharField(initial=_('Eliminated (optional):'),
                            disabled=True)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one year field per Great Power"""
        super().__init__(*args, **kwargs)

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            self.fields[c] = forms.IntegerField(min_value=FIRST_YEAR)
            self.fields[c].required = False
            self.fields[c].widget.attrs['size'] = 4
            self.fields[c].widget.attrs['maxlength'] = 4


# Supply Centre count

class SCCountForm(forms.Form):
    """Form for a Supply Centre count"""
    # Allow for an initial game-start SC count
    year = forms.IntegerField(min_value=FIRST_YEAR-1)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one count field per Great Power"""
        super().__init__(*args, **kwargs)

        self.fields['year'].widget.attrs['size'] = 4

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            # Support just providing counts for some powers (e.g. eliminations)
            self.fields[c] = forms.IntegerField(min_value=0,
                                                max_value=TOTAL_SCS,
                                                required=False)
            # We don't want the default capitalisation
            self.fields[c].label = _(c)
            self.fields[c].widget.attrs['size'] = 2
            self.fields[c].widget.attrs['maxlength'] = 2

    def clean(self):
        """Checks that the total SC count is reasonable"""
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        total_scs = 0
        got_full_set = True
        for power in GreatPower.objects.all():
            c = power.name
            dots = cleaned_data.get(c)
            if dots is None:
                # This power is either missing or didn't validate
                got_full_set = False
            else:
                total_scs += dots
        if total_scs > TOTAL_SCS:
            raise forms.ValidationError(_("Total SC count for %(year)d is %(dots)d, more than %(max)d")
                                        % {'year': year,
                                           'dots': total_scs,
                                           'max': TOTAL_SCS})
        if got_full_set:
            # Add a pseudo-field with the number of neutrals, for convenience
            cleaned_data['neutral'] = TOTAL_SCS - total_scs

        return cleaned_data


class BaseSCCountFormset(BaseFormSet):
    """Form to specify SC counts for a Game"""
    def clean(self):
        """
        Checks that no year appears more than once, and that neutrals don't increase
        """
        if any(self.errors):
            return
        years = []
        neutrals = {}
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            try:
                year = form.cleaned_data['year']
            except KeyError:
                # Blank form
                continue
            if year in years:
                raise forms.ValidationError(_('Year %(year)s appears more than once')
                                            % {'year': year})
            years.append(year)
            # Remember the number of neutrals left
            try:
                neutrals[year] = form.cleaned_data['neutral']
            except KeyError:
                # Don't check years with partial data
                pass
        # Now check that the number of neutrals only goes down
        prev_neutrals = TOTAL_SCS
        for year in sorted(neutrals.keys()):
            if neutrals[year] > prev_neutrals:
                raise forms.ValidationError(_('Neutrals increases from %(before)d to %(after)d in %(year)d')
                                            % {'before': prev_neutrals,
                                               'after': neutrals[year],
                                               'year': year})
            prev_neutrals = neutrals[year]


# Enable self check-ins

class EnableCheckInForm(forms.Form):
    """Form to enable self-check-ins for roll call"""

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        round_num = kwargs.pop('round_num', None)
        super().__init__(*args, **kwargs)

        if round_num:
            first_round_num = last_round_num = this_round_num = round_num
        else:
            first_round_num = 1
            last_round_num = self.tournament.round_set.count()
            # current_round() could return None, if all rounds are over
            cr = self.tournament.current_round()
            if cr:
                this_round_num = cr.number()
            else:
                # Use a round number higher than all that exist
                this_round_num = last_round_num + 1

        # Create the right number of enable fields, with the right ones read-only
        for i in range(first_round_num, 1 + last_round_num):
            name = f'round_{i}'
            readonly = (i < this_round_num)
            self.fields[name] = forms.BooleanField(required=False, initial=False)
            if readonly:
                self.fields[name].disabled = True


# Pick a Player

class PlayerForm(forms.Form):
    """Form to pick a Player"""
    player = PlayerChoiceField(queryset=Player.objects.all())

    def __init__(self, *args, **kwargs):
        # Optional Tournament parameter
        t = None
        try:
            t = kwargs.pop('tournament')
        except KeyError:
            pass
        super().__init__(*args, **kwargs)
        if t is not None:
            self.fields['player'].queryset = Player.objects.filter(tournamentplayer__in=t.tournamentplayer_set.all()).distinct()


# Roll call

class PlayerRoundForm(forms.Form):
    """Form to specify whether a player is available to play a specific round"""
    # We want all Players to be available to be chosen,
    # as this provides an easy way to add TournamentPlayers
    player = PlayerChoiceField(queryset=Player.objects.all())
    present = forms.BooleanField(required=False, initial=False)
    standby = forms.BooleanField(required=False, initial=False)
    sandboxer = forms.BooleanField(required=False, initial=False)
    rounds_played = forms.IntegerField(required=False,
                                       disabled=True,
                                       max_value=10,
                                       min_value=0)

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.round_num = kwargs.pop('round_num')
        super().__init__(*args, **kwargs)


class BasePlayerRoundFormset(BaseFormSet):
    """Form to specify which players are playing in a round"""
    def clean(self):
        """Checks that no player appears more than once"""
        if any(self.errors):
            return
        players = []
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            player = form.cleaned_data.get('player')
            if not player:
                continue
            if player in players:
                raise forms.ValidationError(_('Player %(player)s appears more than once')
                                            % {'player': player})
            players.append(player)

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        round_num = kwargs.pop('round_num')
        super().__init__(*args, **kwargs)
        # Cache parameters we'll pass to each form's constructor
        self.round_num = round_num

    def _construct_form(self, index, **kwargs):
        # Pass the special args down to the form itself
        kwargs['round_num'] = self.round_num
        return super()._construct_form(index, **kwargs)


# Round scoring

class PlayerRoundScoreForm(forms.Form):
    """Form to enter round score(s) for a player"""
    tp = TournamentPlayerChoiceField(queryset=TournamentPlayer.objects.none(),
                                     widget=forms.HiddenInput())
    player = forms.CharField(max_length=Player._meta.get_field('first_name').max_length + Player._meta.get_field('last_name').max_length + 1,
                             disabled=True)
    player.widget.attrs.update(size='20')

    def __init__(self, *args, **kwargs):
        # Remove our three special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        self.last_round_num = kwargs.pop('last_round_num')
        super().__init__(*args, **kwargs)

        self.fields['tp'].queryset = self.tournament.tournamentplayer_set.prefetch_related('player')

        # Create the right number of round fields, with the right ones read-only
        for i in range(1, 1 + self.last_round_num):
            name = f'round_{i}'
            # Create an additional field to show the game scores for that round
            game_scores_name = f'game_scores_{i}'
            self.fields[game_scores_name] = forms.CharField(max_length=10,
                                                            required=False,
                                                            disabled=True)
            self.fields[name] = forms.FloatField(required=False)
            attrs = self.fields[name].widget.attrs
            attrs['size'] = 10
            attrs['maxlength'] = 40

        # Last field is for the overall tournament score
        self.fields['overall_score'] = forms.FloatField(required=False)
        attrs = self.fields['overall_score'].widget.attrs
        attrs['size'] = 10
        attrs['maxlength'] = 20


class BasePlayerRoundScoreFormset(BaseFormSet):
    """Form to enter round scores for all players"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        super().__init__(*args, **kwargs)
        # Cache value we'll pass to each form's constructor
        self.last_round_num = self.tournament.round_set.count()

    def _construct_form(self, index, **kwargs):
        # Pass the three special args down to the form itself
        kwargs['tournament'] = self.tournament
        kwargs['last_round_num'] = self.last_round_num
        return super()._construct_form(index, **kwargs)


# Seeder bias

class SeederBiasForm(ModelForm):
    """Form to create/update a SeederBias object"""
    player1 = TournamentPlayerChoiceField(queryset=TournamentPlayer.objects.none())
    player2 = TournamentPlayerChoiceField(queryset=TournamentPlayer.objects.none())

    class Meta:
        model = SeederBias
        fields = ['player1', 'player2']

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        super().__init__(*args, **kwargs)
        self.fields['player1'].queryset = self.tournament.tournamentplayer_set.prefetch_related('player')
        self.fields['player2'].queryset = self.tournament.tournamentplayer_set.prefetch_related('player')


# Game images

class GameImageForm(ModelForm):
    """Form for a single GameImage"""
    class Meta:
        model = GameImage
        fields = ('game', 'year', 'season', 'phase', 'image')

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        tournament = kwargs.pop('tournament')
        super().__init__(*args, **kwargs)
        self.fields['game'].queryset = Game.objects.filter(the_round__tournament=tournament).distinct()
