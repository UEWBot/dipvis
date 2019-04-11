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
from django.forms import ModelForm
from django.forms.formsets import BaseFormSet
from django.utils.translation import ugettext as _

from tournament.diplomacy import GreatPower, GameSet, SupplyCentre
from tournament.diplomacy import TOTAL_SCS, FIRST_YEAR
from tournament.diplomacy import validate_preference_string
from tournament.models import Game, GameImage
from tournament.models import SECRET, COUNTS, SEASONS
from tournament.models import TournamentPlayer
from tournament.players import Player

class PrefsForm(forms.Form):
    """Form for one TournamentPlayer's Preferences"""
    prefs = forms.CharField(max_length=7,
                            strip=True,
                            required=False,
                            validators=[validate_preference_string])

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tp = kwargs.pop('tp')
        # Overridable default initial value, like ModelForm
        if 'initial' not in kwargs.keys():
            kwargs['initial'] = {'prefs': self.tp.prefs_string()}
        super().__init__(*args, **kwargs)
        # Set the label to the player's name
        self.fields['prefs'].label = str(self.tp.player)

class BasePrefsFormset(BaseFormSet):
    """Form to spcify Preferences for every TournamentPlayer"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament = kwargs.pop('tournament')
        # Get the list of TournamentPlayers
        self.tps = list(self.tournament.tournamentplayer_set.all())
        # Create initial if not provided
        if 'initial' not in kwargs.keys():
            # And construct inital data from it
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

class DrawForm(forms.Form):
    """Form for a draw vote"""
    year = forms.IntegerField(min_value=FIRST_YEAR)
    season = forms.ChoiceField(choices=SEASONS)
    proposer = forms.ModelChoiceField(queryset=GreatPower.objects.all(),
                                      to_field_name='name')

    def __init__(self, *args, **kwargs):
        """Adds powers field if game is not set Draws Include All Survivors"""
        # Remove our special kwargs from the list
        is_dias = kwargs.pop('dias')
        secrecy = kwargs.pop('secrecy')
        super().__init__(*args, **kwargs)

        if not is_dias:
            self.fields['powers'] = forms.ModelMultipleChoiceField(queryset=GreatPower.objects.all(),
                                                                   to_field_name='name',
                                                                   widget=forms.SelectMultiple(attrs={'size': '7'}))
        if secrecy == SECRET:
            self.fields['passed'] = forms.BooleanField(initial=False,
                                                       required=False)
        elif secrecy == COUNTS:
            self.fields['votes_in_favour'] = forms.IntegerField(min_value=0,
                                                                max_value=7)
        else:
            assert 0, 'Unexpected draw secrecy value %c' % secrecy

class GameScoreForm(forms.Form):
    """Form for score for a single game"""
    game_name = forms.CharField(label=_(u'Game Name'),
                                max_length=10,
                                disabled=True)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one score field per Great Power"""
        super().__init__(*args, **kwargs)

        attrs = self.fields['game_name'].widget.attrs
        attrs['size'] = attrs['maxlength']

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            # Don't require a score for every player
            self.fields[c] = forms.FloatField(required=False)
            attrs = self.fields[c].widget.attrs
            attrs['size'] = 10
            attrs['maxlength'] = 10

class RoundPlayerChoiceField(forms.ModelChoiceField):
    """Field to pick a RoundPlayer"""
    def label_from_instance(self, obj):
        return obj.player.__str__()

class GamePlayersForm(forms.Form):
    """Form for players of a single game"""
    game_name = forms.CharField(label=_(u'Game Name'), max_length=10)
    the_set = forms.ModelChoiceField(label=_(u'Game Set'),
                                     queryset=GameSet.objects.all())

    def __init__(self, *args, **kwargs):
        """Dynamically creates one player field per Great Power"""
        # Remove our special kwarg from the list
        self.the_round = kwargs.pop('the_round')
        super().__init__(*args, **kwargs)

        attrs = self.fields['game_name'].widget.attrs
        attrs['size'] = attrs['maxlength']

        queryset = self.the_round.roundplayer_set.all()

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            self.fields[c] = RoundPlayerChoiceField(queryset)

    def clean(self):
        """Checks that no player is playing multiple powers"""
        cleaned_data = self.cleaned_data
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
                names.append(form.cleaned_data['game_name'])
            except KeyError:
                # This happens when we have a form left blank
                pass
        if len(set(names)) != len(names):
            raise forms.ValidationError(_('Game names must be unique within the tournament'))

class PowerAssignForm(forms.Form):
    """Form for players of a single game"""
    game_name = forms.CharField(label=_(u'Game Name'), max_length=10)
    the_set = forms.ModelChoiceField(label=_(u'Game Set'),
                                     queryset=GameSet.objects.all())

    def __init__(self, *args, **kwargs):
        """Dynamically creates one GreatPower field per RoundPlayer"""
        # Remove our special kwargs from the list
        self.game = kwargs.pop('game')
        super().__init__(*args, **kwargs)

        attrs = self.fields['game_name'].widget.attrs
        attrs['size'] = attrs['maxlength']

        queryset = GreatPower.objects.all()

        # Create the right player fields
        for gp in self.game.gameplayer_set.all().order_by('power__abbreviation'):
            c = gp.id
            self.fields[c] = forms.ModelChoiceField(label=str(gp.player),
                                                    queryset=queryset)

    def clean(self):
        """Checks that no power is played by multiple players"""
        cleaned_data = super().clean()
        powers = []
        for player in self.game.gameplayer_set.all():
            c = player.id
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
        names = [form.cleaned_data['game_name'] for form in self.forms]
        if len(set(names)) != len(names):
            raise forms.ValidationError(_('Game names must be unique within the tournament'))

# TODO Should this be a formset?
class GetSevenPlayersForm(forms.Form):
    """Form to enter players to sit out or play two games"""

    LABELS = {'sitter': _('Player sitting out'),
              'double': _('Player to play two games')}

    def __create_player_fields(self, queryset, prefix, count):
        """Do the actual field creation"""
        for i in range(count):
            self.fields['%s_%d' % (prefix, i)] = RoundPlayerChoiceField(queryset,
                                                                        required=False,
                                                                        label=self.LABELS[prefix])

    def __init__(self, *args, **kwargs):
        """Dynamically creates the specified number of player fields"""
        # Remove our special kwargs from the list
        self.the_round = kwargs.pop('the_round')

        queryset = self.the_round.roundplayer_set.all()

        # Overridable default initial value, like ModelForm
        if 'initial' not in kwargs.keys():
            initial = {}
            sitters = 0
            doublers = 0
            for rp in queryset:
                if rp.game_count == 0:
                    initial['sitter_%d' % sitters] = rp
                    sitters += 1
                if rp.game_count == 2:
                    initial['double_%d' % doublers] = rp
                    doublers += 1
            kwargs['initial'] = initial

        super().__init__(*args, **kwargs)

        # Figure out how many sitters and doubles we need
        count = queryset.count()
        self.sitters = count % 7
        self.doubles = (7 - self.sitters) % 7

        # Create the right number of player fields
        self.__create_player_fields(queryset, 'sitter', self.sitters)
        self.__create_player_fields(queryset, 'double', self.doubles)

    def _check_duplicates(self, cleaned_data, prefix, count):
        """Does the check for a player entered multiple times"""
        round_players = []
        for i in range(count):
            rp = cleaned_data.get('%s_%d' % (prefix, i))
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
        Checks that no player is entered more than once,
        that we have either sitters or doubles, but not both,
        and that we have the right number of either sitters or doubles.
        """
        cleaned_data = self.cleaned_data

        sitters = self._check_duplicates(cleaned_data, 'sitter', self.sitters)
        doubles = self._check_duplicates(cleaned_data, 'double', self.doubles)

        if (sitters > 0) and (sitters < self.sitters):
            raise forms.ValidationError(_('Too few players sitting out games. Got %(actual)d, expected %(expected)d')
                                        % {'actual': sitters,
                                           'expected' : self.sitters})
        if (doubles > 0) and (doubles < self.doubles):
            raise forms.ValidationError(_('Too few players playing two games. Got %(actual)d, expected %(expected)d')
                                        % {'actual': doubles,
                                           'expected' : self.doubles})
        if (doubles > 0) and (sitters > 0):
            raise forms.ValidationError(_('Either have players sit out the round or have players play two games'))

        return cleaned_data

class SCOwnerForm(forms.Form):
    """Form for Supply Centre ownership for one year"""
    # Allow for an initial game-start SC ownership
    year = forms.IntegerField(min_value=FIRST_YEAR-1)

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
                    form.add_error(sc.name, _('Supply Centres should never change from owned to neutral'))

class GameEndedForm(forms.Form):
    """Form that just provides a checkbox to indicate that a Game is over"""
    is_finished = forms.BooleanField(label=_('Game ended'),
                                     required=False,
                                     initial=False)

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
            # TODO It may make sense to use required=False
            # and to default any not provided to zero
            # It may also make sense for that default to be in the model...
            self.fields[c] = forms.IntegerField(min_value=0, max_value=TOTAL_SCS)
            self.fields[c].widget.attrs['size'] = 2
            self.fields[c].widget.attrs['maxlength'] = 2

    def clean(self):
        """Checks that the total SC count is reasonable"""
        cleaned_data = self.cleaned_data
        year = self.cleaned_data.get('year')
        total_scs = 0
        for power in GreatPower.objects.all():
            c = power.name
            dots = cleaned_data.get(c)
            # If the field itself didn't validate, drop out
            if dots is None:
                return cleaned_data
            total_scs += dots
        if total_scs > TOTAL_SCS:
            raise forms.ValidationError(_("Total SC count for %(year)d is %(dots)d, more than %(max)d")
                                        % {'year': year,
                                           'dots': total_scs,
                                           'max': TOTAL_SCS})
        # Add a pseudo-field with the number of neutrals, for convenience
        self.cleaned_data['neutral'] = TOTAL_SCS - total_scs

        return cleaned_data

class BaseSCCountFormset(BaseFormSet):
    """Form to specify SC counts for a Game"""
    def clean(self):
        """
        Checks that no year appears more than once,
        and that neutrals always decrease
        """
        if any(self.errors):
            return
        years = {}
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            year = form.cleaned_data.get('year')
            if not year:
                # Blank form
                continue
            if year in years:
                raise forms.ValidationError(_('Year %(year)s appears more than once')
                                            % {'year': year})
            # Remember the number of neutrals left
            years[year] = form.cleaned_data.get('neutral')
        # Now check that the number of neutrals only goes down
        neutrals = TOTAL_SCS
        for year in sorted(years.keys()):
            if years[year] > neutrals:
                raise forms.ValidationError(_('Neutrals increases from %(before)d to %(after)d in %(year)d')
                                            % {'before': neutrals,
                                               'after': years[year],
                                               'year': year})
            neutrals = years[year]

class PlayerRoundForm(forms.Form):
    """Form to specify which rounds a player played in"""
    # We want all Players to be available to be chosen,
    # as this provides an easy way to add TournamentPlayers
    player = forms.ModelChoiceField(queryset=Player.objects.all())

    def __init__(self, *args, **kwargs):
        # Remove our three special kwargs from the list
        # TODO - self.tournament looks unused - remove?
        self.tournament = kwargs.pop('tournament')
        self.rounds = kwargs.pop('rounds')
        self.this_round = kwargs.pop('this_round')
        super().__init__(*args, **kwargs)

        # Create the right number of round fields, with the right ones read-only
        for i in range(1, 1 + self.rounds):
            name = 'round_%d' % i
            readonly = (i < self.this_round)
            self.fields[name] = forms.BooleanField(required=False, initial=False)
            if readonly:
                self.fields[name].disabled = True

class BasePlayerRoundFormset(BaseFormSet):
    """Form to specify which players are playing in each round"""
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
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the three special args down to the form itself
        kwargs['tournament'] = self.tournament
        kwargs['rounds'] = self.tournament.round_set.count()
        # current_round() could return None, if all rounds are over
        cr = kwargs['this_round'] = self.tournament.current_round()
        if cr:
            kwargs['this_round'] = cr.number()
        else:
            kwargs['this_round'] = -1
        return super()._construct_form(index, **kwargs)

class TournamentPlayerChoiceField(forms.ModelChoiceField):
    """Field to pick a TournamentPlayer"""
    def label_from_instance(self, obj):
        return obj.player.__str__()

class PlayerRoundScoreForm(forms.Form):
    """Form to enter round score(s) for a player"""
    tp_id = TournamentPlayerChoiceField(queryset=TournamentPlayer.objects.none(),
                                        widget=forms.HiddenInput(),
                                        disabled=True)
    player = forms.CharField(max_length=20, disabled=True)

    def __init__(self, *args, **kwargs):
        # Remove our three special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        self.rounds = kwargs.pop('rounds')
        self.this_round = kwargs.pop('this_round')
        super().__init__(*args, **kwargs)

        self.fields['tp_id'].queryset = self.tournament.tournamentplayer_set.all()

        # Create the right number of round fields, with the right ones read-only
        for i in range(1, 1 + self.rounds):
            name = 'round_%d' % i
            readonly = (i < self.this_round)
            if not readonly:
                # Create an additional field to show the game scores for that round
                game_scores_name = 'game_scores_%d' % i
                self.fields[game_scores_name] = forms.CharField(max_length=10,
                                                                required=False,
                                                                disabled=True)
            self.fields[name] = forms.FloatField(required=False)
            attrs = self.fields[name].widget.attrs
            attrs['size'] = 10
            attrs['maxlength'] = 10
            if readonly:
                self.fields[name].disabled = True

        # Last field is for the overall tournament score
        self.fields['overall_score'] = forms.FloatField(required=False)
        attrs = self.fields[name].widget.attrs
        attrs['size'] = 10
        attrs['maxlength'] = 10

class BasePlayerRoundScoreFormset(BaseFormSet):
    """Form to enter round scores for all players"""
    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the three special args down to the form itself
        kwargs['tournament'] = self.tournament
        kwargs['rounds'] = self.tournament.round_set.count()
        # current_round() could return None, if all rounds are over
        cr = kwargs['this_round'] = self.tournament.current_round()
        if cr:
            kwargs['this_round'] = cr.number()
        else:
            kwargs['this_round'] = -1
        return super()._construct_form(index, **kwargs)

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
