# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016 Chris Brand
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

import csv

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms import ModelForm
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError

from tournament.players import Player
from tournament.diplomacy import GreatPower, GameSet, SupplyCentre
from tournament.diplomacy import TOTAL_SCS, FIRST_YEAR, WINNING_SCS
from tournament.models import Tournament, Round, Game, DrawProposal, GameImage, SupplyCentreOwnership, CentreCount
from tournament.models import SPRING, SECRET, POWER_ASSIGNS, COUNTS, SEASONS
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
from tournament.models import SCOwnershipsNotFound

# Redirect times are specified in seconds
INTER_IMAGE_TIME = 15
REFRESH_TIME = 60

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
        super(DrawForm, self).__init__(*args, **kwargs)

        if not is_dias:
            self.fields['powers'] = forms.ModelMultipleChoiceField(queryset=GreatPower.objects.all(),
                                                                   to_field_name='name',
                                                                   widget=forms.SelectMultiple(attrs={'size':'7'}))
        if secrecy == SECRET:
            self.fields['passed'] = forms.BooleanField(initial=False, required=False)
        elif secrecy == COUNTS:
            self.fields['votes_in_favour'] = forms.IntegerField(min_value = 0, max_value = 7)
        else:
            assert 0, 'Unexpected draw secrecy value %c' % secrecy

class GameScoreForm(forms.Form):
    """Form for score for a single game"""
    game_name = forms.CharField(label=_(u'Game Name'), max_length=10)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one score field per Great Power"""
        super(GameScoreForm, self).__init__(*args, **kwargs)

        # No changing the game name !
        attrs = self.fields['game_name'].widget.attrs
        attrs['size'] = attrs['maxlength']
        attrs['readonly'] = 'readonly'

        # Create the right country fields
        for power in GreatPower.objects.all():
            c = power.name
            # Don't require a score for every player
            self.fields[c] = forms.FloatField(required=False)
            attrs = self.fields[c].widget.attrs
            attrs['size'] = 10
            attrs['maxlength'] = 10

class RoundPlayerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.player.__str__()

class GamePlayersForm(forms.Form):
    """Form for players of a single game"""
    game_name = forms.CharField(label=_(u'Game Name'), max_length=10)
    the_set = forms.ModelChoiceField(label=_(u'Game Set'), queryset=GameSet.objects.all())
    power_assignment = forms.ChoiceField(label=_(u'Power Assignment'), choices=POWER_ASSIGNS)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one player field per Great Power"""
        # Remove our special kwarg from the list
        self.the_round = kwargs.pop('the_round')
        super(GamePlayersForm, self).__init__(*args, **kwargs)

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
        players = []
        for power in GreatPower.objects.all():
            c = power.name
            player = cleaned_data.get(c)
            # If the field itself didn't validate, drop out
            if player == None:
                return cleaned_data
            if player in players:
                raise forms.ValidationError(_('Player %(player)s appears more than once') % {'player':player})
            players.append(player)

        return cleaned_data

class BaseGamePlayersForm(BaseFormSet):
    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.the_round = kwargs.pop('the_round')
        super(BaseGamePlayersForm, self).__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the special arg down to the form itself
        kwargs['the_round'] = self.the_round
        return super(BaseGamePlayersForm, self)._construct_form(index, **kwargs)

    def clean(self):
        cleaned_data = super(BaseGamePlayersForm, self).clean()
        # Any duplicates within the page ?
        try:
            names = [cd['game_name'] for cd in self.cleaned_data]
        except AttributeError:
            # This happens when we have a form left blank
            return []
        if len(set(names)) != len(names):
            raise forms.ValidationError(_('Game names must be unique within the tournament'))
        return cleaned_data

class SCOwnerForm(forms.Form):
    """Form for Supply Centre ownership for one year"""
    # Allow for an initial game-start SC ownership
    year = forms.IntegerField(min_value=FIRST_YEAR-1)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one owner field per SupplyCentre"""
        super(SCOwnerForm, self).__init__(*args, **kwargs)

        self.fields['year'].widget.attrs['size'] = 4

        # Create the right country fields
        for sc in SupplyCentre.objects.all():
            self.fields[sc.name] = forms.ModelChoiceField(GreatPower.objects.all(), required=False)

class BaseSCOwnerFormset(BaseFormSet):
    def clean(self):
        """
        Checks that no year appears more than once
        """
        if any(self.errors):
            return
        years = {}
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            year = form.cleaned_data.get('year')
            if not year:
                continue
            if year in years:
                raise forms.ValidationError(_('Year %(year)s appears more than once') % {'year': year})
        # TODO check that SCs never become neutral

class SCCountForm(forms.Form):
    """Form for a Supply Centre count"""
    # Allow for an initial game-start SC count
    year = forms.IntegerField(min_value=FIRST_YEAR-1)

    def __init__(self, *args, **kwargs):
        """Dynamically creates one count field per Great Power"""
        super(SCCountForm, self).__init__(*args, **kwargs)

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
            if dots == None:
                return cleaned_data
            total_scs += dots
        if total_scs > TOTAL_SCS:
            raise forms.ValidationError(_("Total SC count for %(year)d is %(dots)d, more than %(max)d") % {'year': year,
                                                                                                           'dots': total_scs,
                                                                                                           'max': TOTAL_SCS})
        # Add a pseudo-field with the number of neutrals, for convenience
        self.cleaned_data['neutral'] = TOTAL_SCS - total_scs

        return cleaned_data

class BaseSCCountFormset(BaseFormSet):
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
                continue
            if year in years:
                raise forms.ValidationError(_('Year %(year)s appears more than once') % {'year': year})
            # For convenience, store the number of neutrals left each year
            years[year] = form.cleaned_data.get('neutral')
        # Now check that the number of neutrals only goes down
        neutrals = TOTAL_SCS
        for year in sorted(years.keys()):
            if years[year] > neutrals:
                raise forms.ValidationError(_('Neutrals increases from %(before)d to %(after)d in %(year)d') % {'before': neutrals,
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
        self.tournament = kwargs.pop('tournament')
        self.rounds = kwargs.pop('rounds')
        self.this_round = kwargs.pop('this_round')
        super(PlayerRoundForm, self).__init__(*args, **kwargs)

        # Create the right number of round fields, with the right ones read-only
        for i in range(1, 1 + self.rounds):
            name = 'round_%d' % i
            readonly = (i < self.this_round)
            self.fields[name] = forms.BooleanField(required=False, initial=False)
            if readonly:
                # "readonly" on checkboxes is purely visual, but good enough for now
                self.fields[name].widget.attrs['readonly'] = 'readonly'

class BasePlayerRoundFormset(BaseFormSet):
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
                raise forms.ValidationError(_('Player %(player)s appears more than once') % {'player': player})
            players.append(player)

    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        super(BasePlayerRoundFormset, self).__init__(*args, **kwargs)

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
        return super(BasePlayerRoundFormset, self)._construct_form(index, **kwargs)

class TournamentPlayerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.player.__str__()

class PlayerRoundScoreForm(forms.Form):
    """Form to enter round score(s) for a player"""
    tp_id = TournamentPlayerChoiceField(queryset=TournamentPlayer.objects.none(),
                                            widget=forms.HiddenInput(attrs={'readonly':'readonly'}))
    player = forms.CharField(max_length=20)

    def __init__(self, *args, **kwargs):
        # Remove our three special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        self.rounds = kwargs.pop('rounds')
        self.this_round = kwargs.pop('this_round')
        super(PlayerRoundScoreForm, self).__init__(*args, **kwargs)

        self.fields['tp_id'].queryset = self.tournament.tournamentplayer_set.all()
        self.fields['player'].widget.attrs['readonly'] = 'readonly'

        # Create the right number of round fields, with the right ones read-only
        for i in range(1, 1 + self.rounds):
            name = 'round_%d' % i
            readonly = (i < self.this_round)
            if not readonly:
                # Create an additional field to show the game scores for that round
                game_scores_name = 'game_scores_%d' %i
                self.fields[game_scores_name] = forms.CharField(max_length=10,
                                                                required=False)
                attrs = self.fields[game_scores_name].widget.attrs
                attrs['readonly'] = 'readonly'
            self.fields[name] = forms.FloatField(required=False)
            attrs = self.fields[name].widget.attrs
            attrs['size'] = 10
            attrs['maxlength'] = 10
            if readonly:
                # "readonly" on checkboxes is purely visual, but good enough for now
                self.fields[name].widget.attrs['readonly'] = 'readonly'

        # Last field is for the overall tournament score
        self.fields['overall_score'] = forms.FloatField(required=False)
        attrs = self.fields[name].widget.attrs
        attrs['size'] = 10
        attrs['maxlength'] = 10

class BasePlayerRoundScoreFormset(BaseFormSet):
    def __init__(self, *args, **kwargs):
        # Remove our special kwargs from the list
        self.tournament = kwargs.pop('tournament')
        super(BasePlayerRoundScoreFormset, self).__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        # Pass the three special args down to the form itself
        kwargs['tournament'] = self.tournament
        kwargs['rounds'] = self.tournament.round_set.count()
        # current_round() could return None, if all rounds are over,
        # but that just gives us a blank form, which is fine
        kwargs['this_round'] = self.tournament.current_round().number()
        return super(BasePlayerRoundScoreFormset, self)._construct_form(index, **kwargs)

class GameImageForm(ModelForm):
    class Meta:
        model = GameImage
        fields = ('game', 'year', 'season', 'phase', 'image')

# Index of Tournaments

def tournament_index(request):
    """Display a list of tournaments"""
    # We actually retrieve two separate lists, one of all published tournaments (visible to all)
    main_list = Tournament.objects.filter(is_published=True)
    # and a second list of unpublished tournaents visible to the current user
    if request.user.is_superuser:
        # All unpublished tournaments
        unpublished_list = Tournament.objects.filter(is_published=False)
    elif request.user.is_active:
        # All unpublished tournaments where the current user is listed as a manager
        unpublished_list = request.user.tournament_set.filter(is_published=False)
    else:
        # None at all
        unpublished_list = Tournament.objects.none()
    context = {'tournament_list': main_list, 'unpublished_list': unpublished_list}
    return render(request, 'tournaments/index.html', context)

# Tournament views

def get_visible_tournament_or_404(pk, user):
    """
    Get the specified Tournament object, if it exists, and check that it is visible to the user.
    If it doesn't exist or isn't visible, raise Http404.
    """
    t = get_object_or_404(Tournament, pk=pk)
    # Visible to all if published
    if t.is_published:
        return t
    # Also visible if the user is a manager for the tournament
    if user.is_active and t in user.tournament_set.all():
        return t
    # Superusers see all
    if user.is_superuser:
        return t
    # Default to not visible
    raise Http404

def tournament_simple(request, tournament_id, template):
    """Just render the specified template with the tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    context = {'tournament': t}
    return render(request, 'tournaments/%s.html' % template, context)

def tournament_scores(request, tournament_id, refresh=False, redirect_url_name='tournament_scores_refresh'):
    """Display scores of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    tps = t.tournamentplayer_set.order_by('-score', 'player__last_name', 'player__first_name')
    rds = t.round_set.all()
    rounds = [r.number() for r in rds]
    # Grab the scores for each round once.
    # This will get us the "if the round ended now" scores
    round_scores = {}
    for r in rds:
        round_scores[r] = r.scores()
    # Grab the tournament scores and positions, which will also be "if it ended now"
    t_positions_and_scores = t.positions_and_scores()
    # Construct a list of lists with [position, player name, round 1 score, ..., round n score, tournament score]
    scores = []
    for p in tps:
        rs = []
        for r in rds:
            try:
                rs.append('%.2f' % round_scores[r][p.player])
            except KeyError:
                # This player didn't play this round
                rs.append('')
        scores.append(['%d' % t_positions_and_scores[p.player][0]] + ['<a href="%s">%s</a>' % (p.player.get_absolute_url(), p.player)] + rs + ['%.2f' % t_positions_and_scores[p.player][1]])
    # sort rows by tournament score (they'll retain the alphabetic sorting if equal)
    scores.sort(key = lambda row: float(row[-1]), reverse=True)
    # Add one final row showing whether each round is ongoing or not
    row = ['', '']
    for r in rds:
        if r.is_finished():
            row.append(_(u'Final'))
        else:
            row.append('')
    if t.is_finished():
        row.append(_(u'Final'))
    else:
        row.append('')
    scores.append(row)
    context = {'tournament': t, 'scores': scores, 'rounds': rounds}
    if refresh:
        context['refresh'] = True
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse(redirect_url_name, args=(tournament_id,))
    return render(request, 'tournaments/scores.html', context)

def tournament_game_results(request, tournament_id, refresh=False, redirect_url_name='tournament_game_results_refresh'):
    """Display the results of all the games of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    tps = t.tournamentplayer_set.order_by('player__last_name', 'player__first_name')
    rds = t.round_set.all()
    rounds = [r.number() for r in rds]
    # Grab the games for each round
    round_games = {}
    for r in rds:
        round_games[r] = r.game_set.all()
    # Construct a list of lists with [player name, round 1 game results, ..., round n game results]
    results = []
    for p in tps:
        # All the games (in every tournament) this player has played in
        gps = p.player.gameplayer_set.all()
        rs = []
        for r in rds:
            gs = ''
            for g in round_games[r]:
                # Is this game one that this player played in?
                try:
                    gp = gps.filter(game=g).get()
                    # New line if they played multiple games in this round
                    if len(gs):
                        gs += '<br>'
                    # Final year of the game as a whole
                    final_year = g.centrecount_set.order_by('-year').first().year
                    # Final CentreCount for this player in this game
                    final_sc = g.centrecount_set.filter(power=gp.power).order_by('-year').first()
                    if final_sc.count == 0:
                        # We need to look back to find the first CentreCount with no dots
                        final_sc = g.centrecount_set.filter(power=gp.power).filter(count=0).order_by('year').first()
                        gs += _('Eliminated as %(power)s in %(year)d') % {'year': final_sc.year,
                                                                          'power': gp.power.name}
                    else:
                        if final_sc.count == 1:
                            centre_str = _('centre')
                        else:
                            centre_str = _('centres')
                        # Was the game soloed ?
                        soloer = g.soloer()
                        if gp == soloer:
                            gs += _('Solo as %(power)s with %(dots)d %(dot_str)s in %(year)d') % {'year': final_year,
                                                                                                  'power': gp.power.name,
                                                                                                  'dot_str': centre_str,
                                                                                                  'dots': final_sc.count}
                        elif soloer is not None:
                            gs += _('Loss as %(power)s with %(dots)d %(dot_str)s in %(year)d') % {'year': final_sc.year,
                                                                                                  'power': gp.power.name,
                                                                                                  'dot_str': centre_str,
                                                                                                  'dots': final_sc.count}
                        # Did a draw vote pass ?
                        res = g.passed_draw()
                        if res:
                            if gp.power in res.powers():
                                gs += _('%(n)d-way draw as %(power)s with %(dots)d %(dot_str)s in %(year)d') % {'n': res.draw_size(),
                                                                                                                'power': gp.power.name,
                                                                                                                'dots': final_sc.count,
                                                                                                                'dot_str': centre_str,
                                                                                                                'year': final_year}
                            else:
                                gs += _('Loss as %(power)s with %(dots)d %(dot_str)s in %(year)d') % {'year': final_sc.year,
                                                                                                      'power': gp.power.name,
                                                                                                      'dot_str': centre_str,
                                                                                                      'dots': final_sc.count}
                        else:
                            # Game is either ongoing or reached a timed end
                            gs += _('%(dots)d %(dot_str)s as %(power)s in %(year)d') % {'year': final_sc.year,
                                                                                        'power': gp.power.name,
                                                                                        'dot_str': centre_str,
                                                                                        'dots': final_sc.count}
                    # game name and link
                    gs += _(' in <a href="%(url)s">%(game)s</a>') % {'game': g.name, 'url': g.get_absolute_url()}
                    # Additional info
                    if g.is_top_board:
                        gs += _(' [Top Board]')
                    if not g.is_finished:
                        gs += _(' [Ongoing]')
                except GamePlayer.DoesNotExist:
                    pass
            rs.append(gs)
        results.append(['<a href=%s>%s</a>' % (p.player.get_absolute_url(), p.player)] + rs)
    # Add one final row showing whether each round is ongoing or not
    row = ['']
    for r in rds:
        if r.is_finished():
            row.append(_(u'Final'))
        else:
            row.append('')
    results.append(row)
    context = {'tournament': t, 'scores': results, 'rounds': rounds}
    if refresh:
        context['refresh'] = True
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse(redirect_url_name, args=(tournament_id,))
    return render(request, 'tournaments/game_results.html', context)

def tournament_best_countries(request, tournament_id, refresh=False, redirect_url_name='tournament_best_countries_refresh'):
    """Display best countries of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    gps = list(GamePlayer.objects.filter(game__the_round__tournament=t).order_by('-score').distinct())
    # We have to just pick a set here. Avalon Hill is most common in North America
    set_powers = GameSet.objects.get(name='Avalon Hill').setpower_set.order_by('power')
    # TODO Sort set_powers alphabetically by translated power.name
    rows = []
    while len(gps) > 0:
        row = []
        for p in set_powers:
            # Find the first in gps for this power
            for gp in gps:
                if gp.power == p.power:
                    gps.remove(gp)
                    break
            row.append('<a href="%s">%s</a><br/><a href="%s">%s</a><br/>%f' % (gp.player.get_absolute_url(),
                                                                               gp.player,
                                                                               gp.game.get_absolute_url(),
                                                                               gp.game.name,
                                                                               gp.score))
        rows.append(row)
    context = {'tournament': t, 'powers': set_powers, 'rows': rows}
    if refresh:
        context['refresh'] = True
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse(redirect_url_name, args=(tournament_id,))
    return render(request, 'tournaments/best_countries.html', context)

def tournament_background(request, tournament_id, as_ticker=False):
    """Display background info for a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    context = {'tournament': t, 'subject': 'Background', 'content': t.background()}
    if as_ticker:
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse('tournament_ticker',
                                          args=(tournament_id,))
        return render(request, 'tournaments/info_ticker.html', context)
    else:
        return render(request, 'tournaments/info.html', context)

def tournament_news(request, tournament_id, as_ticker=False):
    """Display the latest news of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    context = {'tournament': t, 'subject': 'News', 'content': t.news()}
    if as_ticker:
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse('tournament_ticker',
                                          args=(tournament_id,))
        return render(request, 'tournaments/info_ticker.html', context)
    else:
        return render(request, 'tournaments/info.html', context)

def tournament_round(request, tournament_id):
    """Display details of the currently in-progress round of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = t.current_round()
    if r:
        context = {'tournament': t, 'round': r}
        return render(request, 'rounds/detail.html', context)
    # TODO There must be a better way than this
    return HttpResponse("No round currently being played")

# TODO Name is confusing - sounds like it takes a round_num
@permission_required('tournament.change_roundplayer')
def round_scores(request, tournament_id):
    """Provide a form to enter each player's score for each round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    PlayerRoundScoreFormset = formset_factory(PlayerRoundScoreForm,
                                              extra=0,
                                              formset=BasePlayerRoundScoreFormset)
    if request.method == 'POST':
        formset = PlayerRoundScoreFormset(request.POST, tournament=t)
        if formset.is_valid():
            for form in formset:
                tp = form.cleaned_data['tp_id']
                for r_name,value in form.cleaned_data.items():
                    # Skip if no score was entered
                    if not value:
                        continue
                    # We're only interested in the round score fields
                    if r_name.startswith('round_'):
                        # Extract the round number from the field name
                        i = int(r_name[6:])
                        # Find that Round
                        r = t.round_numbered(i)
                        # Update the score
                        i, created = RoundPlayer.objects.get_or_create(player=tp.player,
                                                                       the_round=r)
                        i.score = value
                        try:
                            i.full_clean()
                        except ValidationError as e:
                            form.add_error(form.fields[r_name], e)
                            i.delete()
                            return render(request,
                                          'tournaments/round_players.html',
                                          {'title': 'Scores',
                                           'tournament': t,
                                           'post_url': reverse('enter_scores', args=(tournament_id,)),
                                           'formset' : formset})

                        i.save()
                    elif r_name == 'overall_score':
                        # Store the player's tournament score
                        tp.score = value
                        try:
                            tp.full_clean()
                        except ValidationError as e:
                            form.add_error(form.fields[r_name], e)
                            return render(request,
                                          'tournaments/round_players.html',
                                          {'title': 'Scores',
                                           'tournament': t,
                                           'post_url': reverse('enter_scores', args=(tournament_id,)),
                                           'formset' : formset})
                        tp.save()
            # Redirect to the read-only version
            return HttpResponseRedirect(reverse('tournament_scores',
                                                args=(tournament_id)))
    else:
        data = []
        # Go through each player in the Tournament
        for tp in t.tournamentplayer_set.all():
            current = {'tp_id': tp, 'player': tp.player, 'overall_score':tp.score}
            for rp in tp.player.roundplayer_set.filter(the_round__tournament=t).all():
                current['round_%d'%rp.the_round.number()] = rp.score
                # Scores for any games in the round
                games = GamePlayer.objects.filter(player=tp.player,
                                                  game__the_round=rp.the_round).distinct()
                current['game_scores_%d'%rp.the_round.number()] = ', '.join([str(g.score) for g in games])
            data.append(current)
        formset = PlayerRoundScoreFormset(tournament=t, initial=data)

    return render(request,
                  'tournaments/round_players.html',
                  {'title': 'Scores',
                   'tournament': t,
                   'post_url': reverse('enter_scores', args=(tournament_id,)),
                   'formset' : formset})

@permission_required('tournament.add_roundplayer')
def roll_call(request, tournament_id):
    """Provide a form to specify which players are playing each round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    PlayerRoundFormset = formset_factory(PlayerRoundForm,
                                         extra=2,
                                         formset=BasePlayerRoundFormset)
    if request.method == 'POST':
        formset = PlayerRoundFormset(request.POST, tournament=t)
        if formset.is_valid():
            for form in formset:
                try:
                    p = form.cleaned_data['player']
                except KeyError:
                    # This must be one of the extra forms, still empty
                    continue
                # Ensure that this Player is in the Tournament
                i, created = TournamentPlayer.objects.get_or_create(player=p,
                                                                    tournament=t)
                try:
                    i.full_clean()
                except ValidationError as e:
                    form.add_error(form.fields['player'], e)
                    i.delete()
                    return render(request,
                                  'tournaments/round_players.html',
                                  {'title': 'Roll Call',
                                   'tournament': t,
                                   'post_url': reverse('roll_call', args=(tournament_id,)),
                                   'formset' : formset})
                i.save()
                for r_name,value in form.cleaned_data.items():
                    # Ignore non-bool fields and ones that aren't True
                    if value != True:
                        # TODO Ideally, we should delete any corresponding RoundPlayer here
                        # This could be a player who was previously checked-off in error
                        continue
                    # Extract the round number from the field name
                    i = int(r_name[6:])
                    # Find that Round
                    r = t.round_numbered(i)
                    # Ensure that we have a corresponding RoundPlayer
                    i, created = RoundPlayer.objects.get_or_create(player=p,
                                                                   the_round=r)
                    try:
                        i.full_clean()
                    except ValidationError as e:
                        form.add_error(None, e)
                        i.delete()
                        return render(request,
                                      'tournaments/round_players.html',
                                      {'title': 'Roll Call',
                                       'tournament': t,
                                       'post_url': reverse('roll_call', args=(tournament_id,)),
                                       'formset' : formset})
                    i.save()
            # Next job is almost certainly to create the actual games
            return HttpResponseRedirect(reverse('create_games',
                                                args=(tournament_id, t.current_round().number())))
    else:
        data = []
        # Go through each player in the Tournament
        for tp in t.tournamentplayer_set.all():
            current = {'player':tp.player}
            # And each round of the Tournament
            for r in t.round_set.all():
                i = r.number()
                # Is this player listed as playing this round ?
                played = r.roundplayer_set.filter(player=tp.player).exists()
                current['round_%d'%i] = played
            data.append(current)
        formset = PlayerRoundFormset(tournament=t, initial=data)

    return render(request,
                  'tournaments/round_players.html',
                  {'title': 'Roll Call',
                   'tournament': t,
                   'post_url': reverse('roll_call', args=(tournament_id,)),
                   'formset' : formset})

def round_index(request, tournament_id):
    """Display a list of rounds of a tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    the_list = t.round_set.all()
    context = {'tournament': t, 'round_list': the_list}
    return render(request, 'rounds/index.html', context)

# Round views

def get_round_or_404(tournament, round_num):
    """Return the specified numbered round of the specified tournament or raise Http404."""
    try:
        return tournament.round_numbered(round_num)
    except Round.DoesNotExist:
        raise Http404

def round_simple(request, tournament_id, round_num, template):
    """Just render the specified template with the round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    context = {'tournament': t, 'round': r}
    return render(request, 'rounds/%s.html' % template, context)

# TODO Replace with return round_simple(request, tournament_id, round_num, 'detail') ?
def round_detail(request, tournament_id, round_num):
    """Display the details of a round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    context = {'tournament': t, 'round': r}
    return render(request, 'rounds/detail.html', context)

@permission_required('tournament.add_game')
def create_games(request, tournament_id, round_num):
    """Provide a form to create the games for a round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    if request.method == 'POST':
        GamePlayersFormset = formset_factory(GamePlayersForm, formset=BaseGamePlayersForm)
        formset = GamePlayersFormset(request.POST, the_round=r)
        if formset.is_valid():
            for f in formset:
                # Update/create the game
                try:
                    g, created = Game.objects.get_or_create(name=f.cleaned_data['game_name'],
                                                            the_round=r,
                                                            the_set=f.cleaned_data['the_set'],
                                                            power_assignment=f.cleaned_data['power_assignment'])
                except KeyError:
                    # This must be an extra, unused formset
                    continue
                try:
                    g.full_clean()
                except ValidationError as e:
                    f.add_error(None, e)
                    g.delete()
                    return render(request,
                                  'rounds/create_games.html',
                                  {'tournament': t,
                                   'round': r,
                                   'formset' : formset})
                g.save()
                # Assign the players to the game
                for power, field in f.cleaned_data.items():
                    try:
                        p = GreatPower.objects.get(name=power)
                    except GreatPower.DoesNotExist:
                        continue
                    # Is there already a player for this power in this game ?
                    try:
                        i = GamePlayer.objects.filter(game=g).filter(power=p).get()
                    except GamePlayer.DoesNotExist:
                        # Create one (default first_season and first_year)
                        i = GamePlayer(player=field.player, game=g, power=p)
                    else:
                        # Change the player (if necessary)
                        i.player = field.player
                    try:
                        i.full_clean()
                    except ValidationError as e:
                        f.add_error(None, e)
                        # TODO Not 100% certain that this is the right thing to do here
                        i.delete()
                        return render(request,
                                      'rounds/create_games.html',
                                      {'tournament': t,
                                       'round': r,
                                       'formset' : formset})
                    i.save()
            # Redirect to the index of games in the round
            return HttpResponseRedirect(reverse('game_index',
                                                args=(tournament_id, round_num)))
    else:
        # Do any games already exist for the round ?
        games = r.game_set.all()
        data = []
        for g in games:
            current = {'game_name': g.name, 'power_assignment': g.power_assignment, 'the_set': g.the_set}
            for gp in g.gameplayer_set.all():
                current[gp.power.name] = RoundPlayer.objects.filter(the_round=g.the_round).filter(player=gp.player).get()
            data.append(current)
        # Estimate the number of games for the round
        round_players = r.roundplayer_set.count()
        expected_games = (round_players + 6) // 7
        # This can happen if there are no RoundPlayers for this round
        if expected_games < 1:
            expected_games = 1
        GamePlayersFormset = formset_factory(GamePlayersForm,
                                             extra=expected_games - games.count(),
                                             formset=BaseGamePlayersForm)
        formset = GamePlayersFormset(the_round=r, initial=data)

    return render(request,
                  'rounds/create_games.html',
                  {'tournament': t,
                   'round': r,
                   'formset' : formset})

@permission_required('tournament.change_gameplayer')
def game_scores(request, tournament_id, round_num):
    """Provide a form to enter scores for all the games in a round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    GameScoreFormset = formset_factory(GameScoreForm,
                                       extra=0)
    if request.method == 'POST':
        formset = GameScoreFormset(request.POST)
        if formset.is_valid():
            for f in formset:
                # Find the game
                g = Game.objects.get(name=f.cleaned_data['game_name'],
                                     the_round=r)
                # Set the score for each player
                for power, field in f.cleaned_data.items():
                    # Ignore non-GreatPower fields (game_name)
                    try:
                        p = GreatPower.objects.get(name=power)
                    except GreatPower.DoesNotExist:
                        continue
                    # Find the matching GamePlayer
                    # TODO This will fail if there was a replacement
                    i = GamePlayer.objects.get(game=g, power=p)
                    # Set the score
                    i.score = field
                    try:
                        i.full_clean()
                    except ValidationError as e:
                        f.add_error(None, e)
                        return render(request,
                                      'rounds/game_score.html',
                                      {'tournament': t,
                                       'round': r,
                                       'formset' : formset})
                    i.save()
            # Redirect to the round index
            return HttpResponseRedirect(reverse('round_index',
                                                args=(tournament_id)))
    else:
        # Initial data
        data = []
        the_list = r.game_set.all()
        for game in the_list:
            content = {'game_name': game.name}
            for gp in game.gameplayer_set.all():
                content[gp.power.name] = gp.score
            data.append(content)
        formset = GameScoreFormset(initial=data)

    return render(request,
                  'rounds/game_score.html',
                  {'tournament': t,
                   'round': r,
                   'formset' : formset})

def game_index(request, tournament_id, round_num):
    """Display a list of games in the round"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    r = get_round_or_404(t, round_num)
    the_list = r.game_set.all()
    context = {'round': r, 'game_list': the_list}
    return render(request, 'games/index.html', context)

# Game views

def get_game_or_404(tournament, game_name):
    """Return the specified game of the specified tournament or raise Http404."""
    try:
        return Game.objects.filter(name=game_name, the_round__tournament=tournament).get()
    except Game.DoesNotExist:
        raise Http404

def game_simple(request, tournament_id, game_name, template):
    """Just render the specified template with the game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    context = {'tournament': t, 'game': g}
    return render(request, 'games/%s.html' % template, context)

# TODO Replace with return game_simple(request, tournament_id, game_name, 'detail') ?
def game_detail(request, tournament_id, game_name):
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    context = {'tournament': t, 'game': g}
    return render(request, 'games/detail.html', context)

def game_sc_owners(request,
                   tournament_id,
                   game_name,
                   refresh=False,
                   redirect_url_name='game_sc_owners_refresh'):
    """Display the SupplyCentre ownership for a game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    scs = SupplyCentre.objects.all()
    scos = SupplyCentreOwnership.objects.filter(game=g)
    set_powers = g.the_set.setpower_set.all()
    # Create a list of years that have been played, starting with the most recent
    years = g.years_played()
    years.reverse()
    context = {'game': g, 'centres': scs}
    # If we don't have ownership data for the current year,
    # and we're refreshing to somewhere else, just move straight along
    this_year = years[0]
    if refresh and redirect_url_name != 'game_sc_owners_refresh' and not scos.filter(year=this_year).exists():
        context['rows'] = []
        context['refresh'] = True
        context['redirect_time'] = 0
        context['redirect_url'] = reverse(redirect_url_name,
                                          args=(tournament_id, game_name))
        return render(request, 'games/sc_owners.html', context)
    # Create a list of rows, each with a year and each supply centre's owner
    rows = []
    for year in years:
        yscos = scos.filter(year=year)
        if len(yscos) == 0:
            # This year we have no data
            no_data_str = '?'
        else:
            # No ownership this year implies neutral
            no_data_str = '-'
        row = []
        row.append(year)
        for sc in scs:
            try:
                sco = yscos.filter(sc=sc).get()
                row.append({'color': set_powers.get(power=sco.owner).colour,
                            'text': sco.owner.abbreviation})
            except SupplyCentreOwnership.DoesNotExist:
                # This is presumably because the centre was still neutral
                row.append({'color': 'white', 'text': no_data_str})
        # Only add this year if there is some SC ownership recorded
        if len(row) > 1:
            rows.append(row)
    context['rows'] = rows
    if refresh:
        context['refresh'] = True
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse(redirect_url_name,
                                          args=(tournament_id, game_name))
    return render(request, 'games/sc_owners.html', context)

def game_sc_chart(request,
                  tournament_id,
                  game_name,
                  refresh=False,
                  redirect_url_name='game_sc_chart_refresh'):
    """Display the SupplyCentre chart for a game"""
    #CentreCountFormSet = inlineformset_factory(Game, CentreCount)
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    set_powers = g.the_set.setpower_set.order_by('power')
    # TODO Sort set_powers alphabetically by translated power.name
    # Massage ps so we have one entry per power
    players = g.players(latest=False)
    ps = []
    for sp in set_powers:
        power_players = ['<a href="%s">%s</a>' % (p.get_absolute_url(), p) for p in players[sp.power]]
        names = '<br>'.join(map(str, power_players))
        ps.append(names)
    scs = g.centrecount_set.order_by('power', 'year')
    # Create a list of years that have been played, starting with the most recent
    years = g.years_played()
    years.reverse()
    # Create a list of rows, each with a year and each power's SC count
    rows = []
    # Start with a row with the current scores
    scores = g.scores()
    row = [_(u'Score')]
    for sp in set_powers:
        row.append(scores[sp.power])
    rows.append(row)
    for year in years:
        yscs = scs.filter(year=year)
        row = []
        row.append(year)
        for sp in set_powers:
            try:
                sc = yscs.filter(power=sp.power).get()
                row.append(sc.count)
            except CentreCount.DoesNotExist:
                # This is presumably because they were eliminated
                row.append(0)
        row.append(g.neutrals(year))
        rows.append(row)
    context = {'game': g, 'powers': set_powers, 'players': ps, 'rows': rows}
    if refresh:
        context['refresh'] = True
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse(redirect_url_name,
                                          args=(tournament_id, game_name))
    #formset = CentreCountFormSet(instance=g, queryset=scs)
    return render(request, 'games/sc_count.html', context)

@permission_required('tournament.add_centrecount')
def sc_owners(request, tournament_id, game_name):
    """Provide a form to enter SC ownership for a game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    # If the round ends with a certain year, provide the right number of blank rows
    # Otherwise, just give them two
    years_to_go = 2
    last_year_played = g.final_year()
    final_year = g.the_round.final_year
    if final_year:
        years_to_go = final_year - last_year_played
    SCOwnerFormset = formset_factory(SCOwnerForm,
                                     extra=years_to_go,
                                     formset=BaseSCOwnerFormset)
    if request.method == 'POST':
        formset = SCOwnerFormset(request.POST)
        if formset.is_valid():
            for form in formset:
                try:
                    year = form.cleaned_data['year']
                except KeyError:
                    # Must be one of the extra forms, still blank
                    continue
                for name, value in form.cleaned_data.items():
                    try:
                        dot = SupplyCentre.objects.get(name=name)
                    except:
                        continue
                    # Can't use get_or_create() here,
                    # because owner has no default and may have changed
                    try:
                        i = SupplyCentreOwnership.objects.get(sc=dot,
                                                              game=g,
                                                              year=year)
                        if value == None:
                            # There is an owner in the db, but now we want this dot to be neutral
                            i.delete()
                            continue
                        else:
                            # Ensure the owner has the value we want
                            i.owner = value
                    except SupplyCentreOwnership.DoesNotExist:
                        if value == None:
                            # Still neutral
                            continue
                        i = SupplyCentreOwnership(sc=dot,
                                                  game=g,
                                                  year=year,
                                                  owner=value)
                    try:
                        i.full_clean()
                    except ValidationError as e:
                        form.add_error(None, e)
                        i.delete()
                        return render(request,
                                      'games/sc_owners_form.html',
                                      {'formset': formset,
                                       'tournament': t,
                                       'game': g})

                    i.save()
                # Ensure that CentreCounts for this year match
                try:
                    g.create_or_update_sc_counts_from_ownerships(year)
                except SCOwnershipsNotFound:
                    # We have a blank row
                    continue
                if (year == final_year) or (g.soloer() is not None):
                    # We now have final CentreCounts
                    g.is_finished = True
                    g.save()
            # Redirect to the read-only version
            return HttpResponseRedirect(reverse('game_sc_owners',
                                                args=(tournament_id, game_name)))
    else:
        # Put in all the existing SupplyCentreOwnerships for this game
        data = []
        for year in g.years_played():
            scs = {'year': year}
            owners = g.supplycentreownership_set.filter(year=year)
            for o in owners:
                scs[o.sc.name] = o.owner
            data.append(scs)
        formset = SCOwnerFormset(initial=data)

    return render(request,
                  'games/sc_owners_form.html',
                  {'formset': formset,
                   'tournament': t,
                   'game': g})

@permission_required('tournament.add_centrecount')
def sc_counts(request, tournament_id, game_name):
    """Provide a form to enter SC counts for a game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    # If the round ends with a certain year, provide the right number of blank rows
    # Otherwise, just give them two
    years_to_go = 2
    last_year_played = g.final_year()
    final_year = g.the_round.final_year
    if final_year:
        years_to_go = final_year - last_year_played
    SCCountFormset = formset_factory(SCCountForm,
                                     extra=years_to_go,
                                     formset=BaseSCCountFormset)
    if request.method == 'POST':
        formset = SCCountFormset(request.POST)
        if formset.is_valid():
            for form in formset:
                try:
                    year = form.cleaned_data['year']
                except KeyError:
                    # Must be one of the extra forms, still blank
                    continue
                solo = False
                for name, value in form.cleaned_data.items():
                    try:
                        power = GreatPower.objects.get(name=name)
                    except:
                        continue
                    if value >= WINNING_SCS:
                        solo = True
                    # Can't use get_or_create() here,
                    # because count has no default and may have changed
                    try:
                        i = CentreCount.objects.get(power=power,
                                                    game=g,
                                                    year=year)
                        # Ensure the count has the value we want
                        i.count = value
                    except CentreCount.DoesNotExist:
                        i = CentreCount(power=power,
                                        game=g,
                                        year=year,
                                        count=value)
                    try:
                        i.full_clean()
                    except ValidationError as e:
                        form.add_error(form.fields[name], e)
                        i.delete()
                        return render(request,
                                      'games/sc_counts_form.html',
                                      {'formset': formset,
                                       'tournament': t,
                                       'game': g})

                    i.save()
                if (year == final_year) or solo:
                    # We now have final CentreCounts
                    g.is_finished = True
                    g.save()
            # Redirect to the read-only version
            return HttpResponseRedirect(reverse('game_sc_chart',
                                                args=(tournament_id, game_name)))
    else:
        # Put in all the existing CentreCounts for this game
        data = []
        for year in g.years_played():
            scs = {'year': year}
            counts = g.centrecount_set.filter(year=year)
            for c in counts:
                scs[c.power.name] = c.count
            data.append(scs)
        formset = SCCountFormset(initial=data)

    return render(request,
                  'games/sc_counts_form.html',
                  {'formset': formset,
                   'tournament': t,
                   'game': g})

def game_news(request, tournament_id, game_name, as_ticker=False):
    """Display news for a game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    context = {'tournament': t, 'game': g, 'subject': 'News', 'content': g.news()}
    if as_ticker:
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse('game_ticker',
                                          args=(tournament_id, game_name))
        return render(request, 'games/info_ticker.html', context)
    else:
        return render(request, 'games/info.html', context)

def game_background(request, tournament_id, game_name, as_ticker=False):
    """Display background info for a game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    context = {'tournament': t, 'game': g, 'subject': 'Background', 'content': g.background()}
    if as_ticker:
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse('game_ticker',
                                          args=(tournament_id, game_name))
        return render(request, 'games/info_ticker.html', context)
    else:
        return render(request, 'games/info.html', context)

@permission_required('tournament.add_drawproposal')
def draw_vote(request, tournament_id, game_name):
    """Provide a form to enter a draw vote for a game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    last_image = g.gameimage_set.last()
    years_played = g.years_played()
    final_year = years_played[-1]
    # Try to put in reasonable defaults for year and season
    if last_image.year < final_year:
        # In this case, we only have the centre count to go on
        year = final_year + 1
        season = SPRING
    else:
        # Assume we're currently playing the season the image is for
        year = last_image.year
        season = last_image.season
    form = DrawForm(request.POST or None,
                    dias = g.is_dias(),
                    secrecy = t.draw_secrecy,
                    initial = {'year': year, 'season' : season})
    if form.is_valid():
        year = form.cleaned_data['year']
        try:
            countries = form.cleaned_data['powers']
        except KeyError:
            # Must be DIAS
            # Find the last year before the draw year for which we have CentreCounts
            while years_played[-1] >= year:
                years_played.pop()
            scs = g.survivors(years_played[-1])
            countries = [sc.power for sc in scs]

        # Create a dict from countries, to pass as kwargs
        kwargs = {}
        for i in range(0,len(countries)):
            kwargs['power_%d'%(i+1)] = countries[i]

        try:
            passed = form.cleaned_data['passed']
        except KeyError:
            passed = None
        try:
            votes_in_favour = form.cleaned_data['votes_in_favour']
        except KeyError:
            votes_in_favour = None

        # Create the DrawProposal
        dp = DrawProposal(game=g,
                          year = year,
                          season = form.cleaned_data['season'],
                          passed = passed,
                          votes_in_favour = votes_in_favour,
                          proposer = form.cleaned_data['proposer'],
                          **kwargs)
        try:
            dp.full_clean()
        except ValidationError as e:
            form.add_error(None, e)
            return render(request,
                          'games/vote.html',
                          {'tournament': t,
                           'game': g,
                           'form' : form})
        dp.save()
        # Redirect to the page for the game
        return HttpResponseRedirect(reverse('game_detail',
                                            args=(tournament_id, game_name)))

    return render(request,
                  'games/vote.html',
                  {'tournament': t,
                   'game': g,
                   'form' : form})

def game_image(request,
               tournament_id,
               game_name,
               turn='',
               timelapse=False,
               redirect_url_name='game_image_seq'):
    """Display the image for the game at the specified time"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    # Display each image for a short time
    refresh_time = INTER_IMAGE_TIME
    if turn == '':
        # With the URLs as they stand, turn='' only occurs with timelapse=True
        if not timelapse:
            raise Http404
        # If we're just showing the current position, use the standard refresh time
        refresh_time = REFRESH_TIME
        # Always display the latest image
        this_image = g.gameimage_set.last()
        next_image_str = ''
        this_year = g.years_played()[-1]
        # If we don't have any image for the current year,
        # and we're refreshing to somewhere else, just move straight along
        if redirect_url_name != 'game_image_seq' and not g.gameimage_set.filter(year=this_year).exists():
            refresh_time = 0
    else:
        # Look for the specified image for that game
        # And while we're at it, also find the one that follows it
        # TODO There may be a better way than iterating through all of them...
        this_image = None
        all_images = g.gameimage_set.all()
        if timelapse:
            # If there is no "next turn", timelapse should loop back to the first
            next_image_str = all_images[0].turn_str()
        for i in all_images:
            if i.turn_str() == turn:
                this_image = i
                if not timelapse:
                    break
            elif this_image:
                next_image_str = i.turn_str()
                break
    if not this_image:
        raise Http404
    context = {'tournament': t, 'image': this_image}
    if timelapse:
        context['refresh'] = True
        context['redirect_time'] = refresh_time
        # Note that this works even if there is just one image.
        # In that case, this becomes a refresh, which will then check
        # for new images at the redirect time
        if redirect_url_name == 'game_image_seq':
            context['redirect_url'] = reverse(redirect_url_name,
                                              args=(tournament_id,
                                                    game_name,
                                                    next_image_str))
        else:
            context['redirect_url'] = reverse(redirect_url_name,
                                              args=(tournament_id,
                                                    game_name))
    return render(request, 'games/image.html', context)

@permission_required('tournament.add_gameimage')
def add_game_image(request, tournament_id, game_name=''):
    """Add an image for a game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    if request.method == 'POST':
        form = GameImageForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the new image in the database
            image = form.save()
            return HttpResponseRedirect(reverse('game_image',
                                                args=(tournament_id,
                                                      image.game.name,
                                                      image.turn_str())))
    else:
        initial = {}
        if game_name != '':
            g = get_game_or_404(t, game_name)
            #last_image = g.gameimage_set.last()
            next_year = g.final_year() + 1
            initial = {'game': g, 'year': next_year}
        form = GameImageForm(initial=initial)

    return render(request,
                  'games/add_image.html',
                  {'tournament': t,
                   'form' : form})

# Player views

class PlayerIndexView(generic.ListView):
    model = Player
    template_name = 'players/index.html'
    context_object_name = 'player_list'

class PlayerDetailView(generic.DetailView):
    model = Player
    template_name = 'players/detail.html'

# CSV export for WDD

def _power_name_to_wdd(name):
    """Map a power name to a WDD country code"""
    # 0 for variant (standard), plus first two letters of the country name (in English)
    return '0%s' % name[0:2].upper()

def _centrecount_year_to_wdd(year):
    """Map a year to a WDD centrecount column name"""
    return 'CT_%02d' % (year % (FIRST_YEAR-1))

def view_classification_csv(request, tournament_id):
    """Return a WDD-compatible "classification" CSV file for the tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    tps = t.tournamentplayer_set.order_by('-score')
    # Grab the tournament scores and positions, which will also be "if it ended now"
    t_positions_and_scores = t.positions_and_scores()
    # Grab the tournament rounds
    rds = t.round_set.all()
    # Grab the best country rankings
    best_countries = t.best_countries()
    # Grab the top board, if any
    try:
        top_board = Game.objects.filter(is_top_board=True).filter(the_round__tournament=t).get()
        tb_positions = top_board.positions()
        tb_dots = top_board.centrecount_set.filter(year__gt=1900)
    except Game.DoesNotExist:
        top_board = None
    # What fields we want to write
    headers = ['FIRST NAME',
               'NAME',
               'HOMONYME',
               'RANK',
               'EXAEQUO', # Last of the mandatory ones
               'SCORE',
              ]
    # Centre count for each year (extras don't matter)
    for i in range(1,9):
        headers.append('R%d' % i)
    # Best country stuff
    for p in GreatPower.objects.all():
        wdd_pwr = _power_name_to_wdd(p.name)
        headers.append('RK_%s' % wdd_pwr)
        headers.append('PT_%s' % wdd_pwr)
        headers.append('CT_%s' % wdd_pwr)
        headers.append('HEAT_%s' % wdd_pwr)
        headers.append('BOARD_%s' % wdd_pwr)
    # Top Board stuff
    # Only add these headers if there was a top board
    if top_board:
        headers.append('NAME_TOPBOARD')
        headers.append('HEAT_TOPBOARD')
        headers.append('BOARD_TOPBOARD')
        headers.append('RK_TOPBOARD')
        headers.append('CT_TOPBOARD')
        headers.append('COUNTRY_TOPBOARD')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s%dclassification.csv"' % (t.name, t.start_date.year)

    writer = csv.DictWriter(response, fieldnames=headers)
    writer.writeheader()
    # One row per player (row order and field order don't matter)
    for tp in tps:
        p = tp.player
        p_score = t_positions_and_scores[p][1]
        # First the stuff that is global to the tournament and applies to all players
        row_dict = {'FIRST NAME': p.first_name,
                    'NAME': p.last_name,
                    'HOMONYME': '1', # User Guide says "Set to 1"
                    'RANK': t_positions_and_scores[p][0],
                    'EXAEQUO': len([s for x,s in t_positions_and_scores.values() if s == p_score]), # No. of players with the same rank
                    'SCORE': p_score,
                   }
        # Add in round score for each round played
        for r in rds:
            for rp in r.roundplayer_set.filter(player=p):
                row_dict['R%d' % r.number()] = rp.score
        # Add best country fields if any
        for power,bc in best_countries.items():
            # Did this player win best country with this power?
            for gp in bc:
                if gp.player == p:
                    wdd_pwr = _power_name_to_wdd(power.name)
                    row_dict['RK_%s' % wdd_pwr] = 1
                    row_dict['PT_%s' % wdd_pwr] = gp.score
                    row_dict['CT_%s' % wdd_pwr] = gp.game.centrecount_set.filter(power=power).last().count
                    row_dict['HEAT_%s' % wdd_pwr] = gp.game.the_round.number()
                    # We store boards as names, not numbers
                    # g.id is globally-unique. What we really want is number within the round
                    row_dict['BOARD_%s' % wdd_pwr] = gp.game.id
                    break
        # Add top board fields if applicable
        if top_board:
            try:
                gp = top_board.gameplayer_set.filter(player=p).get()
                row_dict['NAME_TOPBOARD'] = 'A' # This seems to be arbitrary
                row_dict['HEAT_TOPBOARD'] = top_board.the_round.number()
                row_dict['BOARD_TOPBOARD'] = top_board.id
                row_dict['RK_TOPBOARD'] = tb_positions[gp.power]
                row_dict['CT_TOPBOARD'] = tb_dots.filter(power=gp.power).last().count
                # TODO Not certain that this is the correct value
                row_dict['COUNTRY_TOPBOARD'] = _power_name_to_wdd(gp.power.name)
            except GamePlayer.DoesNotExist:
                # This player did not make the top board
                pass
        # Write this player's row out
        writer.writerow(row_dict)

    return response

def view_boards_csv(request, tournament_id):
    """Return a WDD-compatible "boards" CSV file for the tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    # What fields we want to write
    headers = ['FIRST NAME',
               'NAME',
               'HOMONYME',
               'ROUND',
               'BOARD',
               'COUNTRY',
               'RANK',
               'EXAEQUO', # Last of the mandatrory ones
               'SCORE',
               'NB_CENTRE',
               'YEAR_ELIMINATION',
               'DRAW',
              ]
    # Centre count for each year (extras don't matter)
    for i in range(1,21):
        headers.append('CT_%02d' % i)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s%dboards.csv"' % (t.name, t.start_date.year)

    writer = csv.DictWriter(response, fieldnames=headers)
    writer.writeheader()

    # One row per game, per player
    r_row_dict = {}
    r_row_dict['HOMONYME'] = '1' # User Guide says "Set to 1"
    for r in t.round_set.all():
        r_row_dict['ROUND'] = r.number()
        g_row_dict = r_row_dict.copy()
        for g in r.game_set.all():
            # We store boards as names, not numbers
            # g.id is globally-unique. What we really want is number within the round
            g_row_dict['BOARD'] = g.id
            positions = g.positions()
            draw = g.passed_draw()
            soloer = g.soloer()
            # TODO This is broken with replacement players
            for gp in g.gameplayer_set.all():
                row_dict = g_row_dict.copy()
                row_dict['FIRST NAME'] = gp.player.first_name
                row_dict['NAME'] = gp.player.last_name
                row_dict['COUNTRY'] = _power_name_to_wdd(gp.power.name)
                row_dict['SCORE'] = gp.score
                rank = positions[gp.power]
                row_dict['RANK'] = rank
                row_dict['EXAEQUO'] = len([r for r in positions.values() if r == rank])
                dots = g.centrecount_set.filter(power=gp.power).filter(year__gt=1900)
                # How did the game end?
                if soloer is not None:
                    if soloer == gp:
                        # This player won
                        row_dict['DRAW'] = 1
                    else:
                        # Another player won
                        row_dict['DRAW'] = 0
                if draw is not None:
                    if draw.power_is_part(gp.power):
                        row_dict['DRAW'] = draw.draw_size()
                    else:
                        row_dict['DRAW'] = 0
                row_dict['NB_CENTRE'] = dots.last().count
                elim = gp.elimination_year()
                if elim is not None:
                    row_dict['YEAR_ELIMINATION'] = elim % (FIRST_YEAR-1)
                # Add in centre counts
                for cc in dots:
                    row_dict[_centrecount_year_to_wdd(cc.year)] = cc.count
                # Write a row for this player in this game
                writer.writerow(row_dict)

    return response

