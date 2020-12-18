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
Game Views for the Diplomacy Tournament Visualiser.
"""

from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.forms.formsets import formset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext as _

from tournament import backstabbr

from tournament.forms import BaseSCCountFormset
from tournament.forms import BaseSCOwnerFormset
from tournament.forms import DrawForm
from tournament.forms import GameEndedForm
from tournament.forms import DeathYearForm
from tournament.forms import GameImageForm
from tournament.forms import SCCountForm
from tournament.forms import SCOwnerForm

from tournament.tournament_views import get_modifiable_tournament_or_404
from tournament.tournament_views import get_visible_tournament_or_404

from tournament.diplomacy import GreatPower, SupplyCentre
from tournament.diplomacy import TOTAL_SCS, WINNING_SCS
from tournament.models import Game, DrawProposal
from tournament.models import SupplyCentreOwnership, CentreCount
from tournament.models import SPRING
from tournament.models import SCOwnershipsNotFound
from tournament.news import news

# Redirect times are specified in seconds
INTER_IMAGE_TIME = 15
REFRESH_TIME = 60

# Game views


def get_game_or_404(tournament, game_name):
    """
    Return the specified game of the specified tournament or raise Http404.
    """
    try:
        return Game.objects.get(name=game_name,
                                the_round__tournament=tournament)
    except Game.DoesNotExist:
        raise Http404


def game_simple(request, tournament_id, game_name, template):
    """Just render the specified template with the game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    context = {'tournament': t, 'game': g}
    return render(request, 'games/%s.html' % template, context)


def game_sc_owners(request,
                   tournament_id,
                   game_name,
                   refresh=False,
                   redirect_url_name='game_sc_owners_refresh'):
    """Display the SupplyCentre ownership for a game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    scs = SupplyCentre.objects.all()
    scos = g.supplycentreownership_set.all()
    # Create a list of years that have been played, starting with the most recent
    years = g.years_played()
    years.reverse()
    context = {'game': g, 'centres': scs}
    # If we don't have ownership data for the current year,
    # and we're refreshing to somewhere else, just move straight along
    this_year = years[0]
    if (refresh
            and redirect_url_name != 'game_sc_owners_refresh'
            and not scos.filter(year=this_year).exists()):
        context['rows'] = []
        context['refresh'] = True
        context['redirect_time'] = 0
        context['redirect_url'] = reverse(redirect_url_name,
                                          args=(tournament_id, game_name))
        return render(request, 'games/sc_owners.html', context)
    set_powers = g.the_set.setpower_set.all()
    power_to_colour = {}
    for o in set_powers:
        power_to_colour[o.power] = o.colour
    # Create a list of rows, each with a year and each supply centre's owner
    rows = []
    issues = []
    for year in years:
        yscos = scos.filter(year=year)
        if not yscos:
            # This year we have no data
            no_data_str = '?'
        else:
            # No ownership this year implies neutral
            no_data_str = '-'
        row = []
        row.append(year)
        for sc in scs:
            try:
                sco = yscos.get(sc=sc)
            except SupplyCentreOwnership.DoesNotExist:
                # This is presumably because the centre was still neutral
                row.append({'color': 'white', 'text': no_data_str})
            else:
                row.append({'color': power_to_colour[sco.owner],
                            'text': sco.owner.abbreviation})
        rows.append(row)
        try:
            # Check for any problems, and add them to the list
            issues += g.compare_sc_counts_and_ownerships(year)
        except SCOwnershipsNotFound:
            # We have no ownership data for this year, which is fine
            pass
    context['rows'] = rows
    context['issues'] = issues
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
        power_players = ['<a href="%s">%s</a>'
                         % (p.get_absolute_url(), p) for p in players[sp.power]]
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
                sc = yscs.get(power=sp.power)
                row.append(sc.count)
            except CentreCount.DoesNotExist:
                row.append('?')
        neutrals = g.neutrals(year)
        if neutrals == TOTAL_SCS:
            neutrals = '?'
        row.append(neutrals)
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
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    # If the round ends with a certain year, provide the right number of blank rows
    # Otherwise, just give them four
    years_to_go = 4
    last_year_played = g.final_year()
    final_year = g.the_round.final_year
    if final_year:
        years_to_go = final_year - last_year_played
    SCOwnerFormset = formset_factory(SCOwnerForm,
                                     extra=years_to_go,
                                     formset=BaseSCOwnerFormset)
    # Put in all the existing SupplyCentreOwnerships for this game
    data = []
    for year in g.years_played():
        scs = {'year': year}
        owners = g.supplycentreownership_set.filter(year=year)
        for o in owners:
            scs[o.sc.name] = o.owner
        data.append(scs)
    formset = SCOwnerFormset(request.POST or None, initial=data)
    if formset.is_valid():
        for form in formset:
            try:
                year = form.cleaned_data['year']
            except KeyError:
                # Must be one of the extra forms, still blank
                continue
            if year is None:
                continue
            for name, value in form.cleaned_data.items():
                try:
                    dot = SupplyCentre.objects.get(name=name)
                except SupplyCentre.DoesNotExist:
                    continue
                # Can't use get_or_create() here,
                # because owner has no default and may have changed
                try:
                    i = SupplyCentreOwnership.objects.get(sc=dot,
                                                          game=g,
                                                          year=year)
                    if value is None:
                        # There is an owner in the db,
                        # but now we want this dot to be neutral
                        i.delete()
                        continue
                    else:
                        # Ensure the owner has the value we want
                        i.owner = value
                except SupplyCentreOwnership.DoesNotExist:
                    if value is None:
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

    return render(request,
                  'games/sc_owners_form.html',
                  {'formset': formset,
                   'tournament': t,
                   'game': g})


@permission_required('tournament.add_centrecount')
def sc_counts(request, tournament_id, game_name):
    """Provide a form to enter SC counts for a game"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    # If the round ends with a certain year, provide the right number of blank rows
    # Otherwise, just give them two
    # TODO Fix this properly - we need to allow for "filling in the gaps"
    years_to_go = 4
    last_year_played = g.final_year()
    final_year = g.the_round.final_year
    #if final_year:
    #    years_to_go = final_year - last_year_played
    SCCountFormset = formset_factory(SCCountForm,
                                     extra=years_to_go,
                                     formset=BaseSCCountFormset)
    # Put in all the existing CentreCounts for this game
    data = []
    death_data = {}
    for year in g.years_played():
        scs = {'year': year}
        counts = g.centrecount_set.filter(year=year)
        for c in counts:
            scs[c.power.name] = c.count
            if (c.count == 0) and (c.power.name not in death_data):
                death_data[c.power.name] = year
        data.append(scs)
    formset = SCCountFormset(request.POST or None, prefix='scs', initial=data)
    end_form = GameEndedForm(request.POST or None,
                             prefix='end',
                             initial={'is_finished': g.is_finished})
    death_form = DeathYearForm(request.POST or None,
                               prefix='death',
                               initial=death_data)
    if formset.is_valid() and end_form.is_valid() and death_form.is_valid():
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
                except GreatPower.DoesNotExist:
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
                                   'end_form': end_form,
                                   'tournament': t,
                                   'game': g})

                i.save()
            if (year == final_year) or solo:
                # We now have final CentreCounts
                g.is_finished = True
                g.save()

        # Add eliminations for any eliminated powers, if needed
        for name, value in death_form.cleaned_data.items():
            if value is None:
                continue
            try:
                power = GreatPower.objects.get(name=name)
            except GreatPower.DoesNotExist:
                continue
            try:
                i = CentreCount.objects.get(power=power,
                                            game=g,
                                            year=value)
            except CentreCount.DoesNotExist:
                # Create a zero-SC count
                i = CentreCount.objects.create(power=power,
                                               game=g,
                                               year=value,
                                               count=0)
            try:
                if i.count != 0:
                    raise ValidationError(_('%(power)s cannot have %(count)d SCs and be eliminated in %(year)d')
                                          % {'power': power,
                                             'count': i.count,
                                             'year': value})
                i.full_clean()
            except ValidationError as e:
                death_form.add_error(form.fields[name], e)
                i.delete()
                return render(request,
                              'games/sc_counts_form.html',
                              {'formset': formset,
                               'end_form': end_form,
                               'death_form': death_form,
                               'tournament': t,
                               'game': g})

            i.save()

        # Set the "game over" flag as appropriate
        # Game is over if it reached the final year,
        # somebody won, or the checkbox was checked
        g.is_finished = g.is_finished or end_form.cleaned_data['is_finished']
        g.save()
        # Redirect to the read-only version
        return HttpResponseRedirect(reverse('game_sc_chart',
                                            args=(tournament_id, game_name)))

    return render(request,
                  'games/sc_counts_form.html',
                  {'formset': formset,
                   'end_form': end_form,
                   'death_form': death_form,
                   'tournament': t,
                   'game': g})


def game_news(request, tournament_id, game_name, for_year=None, as_ticker=False):
    """Display news for a game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    context = {'tournament': t,
               'game': g,
               'subject': 'News',
               'content': news(g, for_year)}
    if as_ticker:
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse('game_ticker',
                                          args=(tournament_id, game_name))
        return render(request, 'games/info_ticker.html', context)
    return render(request, 'games/info.html', context)


def game_background(request, tournament_id, game_name, as_ticker=False):
    """Display background info for a game"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    context = {'tournament': t,
               'game': g,
               'subject': 'Background',
               'content': g.background()}
    if as_ticker:
        context['redirect_time'] = REFRESH_TIME
        context['redirect_url'] = reverse('game_ticker',
                                          args=(tournament_id, game_name))
        return render(request, 'games/info_ticker.html', context)
    return render(request, 'games/info.html', context)


@permission_required('tournament.add_drawproposal')
def draw_vote(request, tournament_id, game_name):
    """Provide a form to enter a draw vote for a game"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
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
                    dias=g.is_dias(),
                    secrecy=t.draw_secrecy,
                    initial={'year': year, 'season': season})
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
        for i, c in enumerate(countries, start=1):
            kwargs['power_%d' % i] = c

        passed = form.cleaned_data.get('passed')
        votes_in_favour = form.cleaned_data.get('votes_in_favour')

        # Create the DrawProposal
        dp = DrawProposal(game=g,
                          year=year,
                          season=form.cleaned_data['season'],
                          passed=passed,
                          votes_in_favour=votes_in_favour,
                          proposer=form.cleaned_data['proposer'],
                          **kwargs)
        try:
            dp.full_clean()
        except ValidationError as e:
            form.add_error(None, e)
            return render(request,
                          'games/vote.html',
                          {'tournament': t,
                           'game': g,
                           'form': form})
        dp.save()
        # Redirect to the page for the game
        return HttpResponseRedirect(reverse('game_detail',
                                            args=(tournament_id, game_name)))

    return render(request,
                  'games/vote.html',
                  {'tournament': t,
                   'game': g,
                   'form': form})


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
        if (redirect_url_name != 'game_image_seq'
                and not g.gameimage_set.filter(year=this_year).exists()):
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
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    initial = {}
    if game_name != '':
        g = get_game_or_404(t, game_name)
        next_year = g.final_year() + 1
        initial = {'game': g, 'year': next_year}
    form = GameImageForm(request.POST or None,
                         request.FILES or None,
                         tournament=t,
                         initial=initial)
    if form.is_valid():
        # Create the new image in the database
        image = form.save()
        return HttpResponseRedirect(reverse('game_image',
                                            args=(tournament_id,
                                                  image.game.name,
                                                  image.turn_str())))

    return render(request,
                  'games/add_image.html',
                  {'tournament': t,
                   'form': form})

@permission_required('tournament.add_centrecount')
def scrape_backstabbr(request, tournament_id, game_name):
    """Import CentreCounts from backstabbr"""
    t = get_modifiable_tournament_or_404(tournament_id, request.user)
    g = get_game_or_404(t, game_name)
    # Do we have a backstabbr game?
    if backstabbr.BACKSTABBR_GAME_URL not in g.notes:
        raise Http404
    # Extract the backstabbr game id
    # Here we assume that it's "everything after the final /"
    game_number = int(g.notes.split('/')[-1])
    # Parse the current game page on Backstabbr
    bg = backstabbr.Game(game_number)
    # Figure out what year we have centre counts for
    if bg.season == backstabbr.SPRING:
        year = bg.year - 1
    elif bg.season == backstabbr.FALL:
        year = bg.year - 1
    elif bg.season == backstabbr.WINTER:
        year = bg.year
    else:
        raise Http404
    # Add the appropriate CentreCounts
    for k, v in bg.powers.items():
        # Map k to GreatPower (assuming that backstabbr.POWERS all start with the appropriate abbreviation)
        power = GreatPower.objects.get(abbreviation=k[0])
        # Can't use get_or_create() here,
        # because count has no default and may have changed
        try:
            i = CentreCount.objects.get(power=power,
                                        game=g,
                                        year=year)
            # Ensure the count has the value we want
            i.count = v[0]
        except CentreCount.DoesNotExist:
            i = CentreCount(power=power,
                            game=g,
                            year=year,
                            count=v[0])
        try:
            i.full_clean()
        except ValidationError as e:
            raise Http404
        i.save()
    # TODO There's more information in bg - like whether the game is over...
    # Report what was done
    return render(request,
                  'games/scrape_backstabbr.html',
                  {'tournament': t,
                   'game': g,
                   'year': year,
                   'centrecounts': g.centrecount_set.filter(year=year).order_by('power')})
