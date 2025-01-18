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
WDD Views for the Diplomacy Tournament Visualiser.
"""

import csv

from django.http import HttpResponse

from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR
from tournament.models import Game, Tournament
from tournament.models import GamePlayer
from tournament.tournament_views import get_visible_tournament_or_404
from tournament.wdd import WDD_MAX_ROUNDS, WDD_MAX_AWARDS, WDD_MAX_YEAR
from tournament.wdd import country_name_to_wdd, country_to_wdd
from tournament.wdd import power_name_to_wdd, WDD_UNKNOWN_COUNTRY


class TooManyAwards(Exception):
    """WDD Only supports a limited number of awards"""
    pass


def _centrecount_year_to_wdd(year):
    """Map a year to a WDD centrecount column name"""
    return 'CT_%02d' % (year % (FIRST_YEAR-1))


def _game_to_wdd_id(game):
    """Return the game number for the specified game"""
    # We identify boards as names, not numbers
    # g.id is globally-unique. What we really want is number within the round
    return game.id


def _power_award_to_gameplayers(tournament, award):
    """
    Map a "best country" award to the corresponding GamePlayers in the Tournament.

    Returns a list of GamePlayers.
    """
    assert award.power is not None
    ret = []
    # First find the TournamentPlayers who got the specified award at this tournament
    for tp in award.tournamentplayer_set.filter(tournament=tournament):
        # Find the corresponding GamePlayer
        for rp in tp.roundplayers().all():
            for gp in rp.gameplayers().filter(power=award.power):
                ret.append(gp)
    return ret


def _award_number(tournament, award):
    """
    Returns the number (1..12) for the specified (non-best country) award at the tournament

    Can raise TooManyAwards.
    """
    n = tournament.award_number(award)
    if n > WDD_MAX_AWARDS:
        raise TooManyAwards(n)
    return n


# Map common name of countries to name used by the WDD
SPECIAL_CASE_COUNTRIES = {
    'USA': 'United States',
    'UK': 'United Kingdom',
}


def _location_country(location):
    """
    Tries to extract the country name from the specified location string.
    """
    # If there's a comma, we only want what comes after it
    try:
        comma = location.rindex(',')
    except ValueError:
        pass
    else:
        location = location[comma+1:]
        location = location.lstrip()
    # Handle special cases (commonly-abbreviated country names)
    try:
        return SPECIAL_CASE_COUNTRIES[location]
    except KeyError:
        pass
    # Hope we're left with a country name
    return location


def view_classification_csv(request, tournament_id):
    """Return a WDD-compatible "classification" CSV file for the tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    tps = t.tournamentplayer_set.order_by('-score').prefetch_related('awards')
    # Grab the tournament scores and positions, "if it ended now"
    t_positions_and_scores = t.positions_and_scores()
    # Grab the top board, if any
    try:
        top_board = Game.objects.get(is_top_board=True,
                                     the_round__tournament=t)
        tb_positions = top_board.positions()
        tb_dots = top_board.centrecount_set.filter(year__gt=1900)
    except Game.DoesNotExist:
        top_board = None
    # What fields we want to write
    headers = ['FIRST NAME',
               'NAME',
               'HOMONYME',
               'RANK',
               'EXAEQUO',  # Last of the mandatory ones
               'LOCATION',
               'NATIONALITY',
               'SCORE',
              ]
    # Score for each round (extras don't matter)
    for i in range(1, WDD_MAX_ROUNDS + 1):
        headers.append(f'R{i}')
    # Best country stuff
    for p in GreatPower.objects.all():
        wdd_pwr = power_name_to_wdd(p.name)
        headers.append(f'RK_{wdd_pwr}')
        headers.append(f'PT_{wdd_pwr}')
        headers.append(f'CT_{wdd_pwr}')
        headers.append(f'HEAT_{wdd_pwr}')
        headers.append(f'BOARD_{wdd_pwr}')
    # Other awards
    for n in range(1, WDD_MAX_AWARDS + 1):
        headers.append(f'RK_AWA_{n}')
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
    response['Content-Disposition'] = f'attachment; filename="{t.name}{t.start_date.year}classification.csv"'

    writer = csv.DictWriter(response, fieldnames=headers)
    writer.writeheader()
    # One row per player (row order and field order don't matter)
    for tp in tps:
        rps = tp.roundplayers()
        if not rps:
            # Player was registered but didn't actually play, so omit them
            continue
        p = tp.player
        rank = t_positions_and_scores[p][0]
        # First the stuff that is global to the tournament and applies to all players
        names = p.wdd_firstname_lastname()
        if not names[0] and not names[1]:
            names = (p.first_name, p.last_name)
        row_dict = {'FIRST NAME': names[0],
                    'NAME': names[1],
                    'HOMONYME': '1',  # User Guide says "Set to 1"
                    'RANK': rank,
                    # No. of players with the same rank
                    'EXAEQUO': len([r for r, _ in t_positions_and_scores.values() if r == rank]),
                    'SCORE': tp.score,
                   }
        if rank == Tournament.UNRANKED:
            row_dict['RANK'] = '999'
        if len(p.nationalities) == 1:
            row_dict['NATIONALITY'] = country_to_wdd(p.nationalities[0])
        if tp.location:
            wdd_country = country_name_to_wdd(_location_country(tp.location))
            # Only set it if we have a reasonable value - location parsing is hit-or-miss
            if wdd_country != WDD_UNKNOWN_COUNTRY:
                row_dict['LOCATION'] = wdd_country
        # Add in round score for each round played
        for rp in rps:
            row_dict[f'R{rp.the_round.number()}'] = rp.score
        # Add awards
        for award in tp.awards.all():
            if award.power is not None:
                for gp in _power_award_to_gameplayers(t, award):
                    if gp.player == p:
                        wdd_pwr = power_name_to_wdd(award.power.name)
                        # TODO WDD actually supports a full ranking for these fields,
                        #      so ideally we'd also set row_dict['RK_0AU'] = 2 for second-best Austria, etc
                        row_dict[f'RK_{wdd_pwr}'] = 1
                        row_dict[f'PT_{wdd_pwr}'] = gp.score
                        row_dict[f'CT_{wdd_pwr}'] = gp.game.centrecount_set.filter(power=award.power).last().count
                        row_dict[f'HEAT_{wdd_pwr}'] = gp.game.the_round.number()
                        row_dict[f'BOARD_{wdd_pwr}'] = _game_to_wdd_id(gp.game)
            else:
                try:
                    row_dict[f'RK_AWA_{_award_number(t, award)}'] = 1
                except TooManyAwards:
                    # Cannot tell WDD about this one
                    pass
        # Add top board fields if applicable
        if top_board:
            try:
                gp = top_board.gameplayer_set.get(player=p)
                row_dict['NAME_TOPBOARD'] = 'A'  # This seems to be arbitrary
                row_dict['HEAT_TOPBOARD'] = top_board.the_round.number()
                row_dict['BOARD_TOPBOARD'] = _game_to_wdd_id(top_board)
                row_dict['RK_TOPBOARD'] = tb_positions[gp.power]
                row_dict['CT_TOPBOARD'] = tb_dots.filter(power=gp.power).last().count
                # TODO Not certain that this is the correct value
                row_dict['COUNTRY_TOPBOARD'] = power_name_to_wdd(gp.power.name)
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
               'EXAEQUO',  # Last of the mandatory ones
               'SCORE',
               'NB_CENTRE',
               'YEAR_ELIMINATION',
               'DRAW',
              ]
    # Centre count for each year (extras don't matter)
    for i in range(1, WDD_MAX_YEAR + 1):
        headers.append('CT_%02d' % i)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{t.name}{t.start_date.year}boards.csv"'

    writer = csv.DictWriter(response, fieldnames=headers)
    writer.writeheader()

    # One row per game, per player
    r_row_dict = {}
    r_row_dict['HOMONYME'] = '1'  # User Guide says "Set to 1"
    for n, r in enumerate(t.round_set.prefetch_related('game_set'), 1):
        r_row_dict['ROUND'] = n
        g_row_dict = r_row_dict.copy()
        for g in r.game_set.prefetch_related('gameplayer_set'):
            g_row_dict['BOARD'] = _game_to_wdd_id(g)
            positions = g.positions()
            centrecount_set = g.centrecount_set.filter(year__gt=1900)
            draw = g.passed_draw()
            if draw is not None:
                draw_powers = draw.drawing_powers.all()
            soloer = g.soloer()
            # TODO This is broken with replacement players
            for gp in g.gameplayer_set.all():
                names = gp.player.wdd_firstname_lastname()
                if not names[0] and not names[1]:
                    names = (gp.player.first_name, gp.player.last_name)
                row_dict = g_row_dict.copy()
                row_dict['FIRST NAME'] = names[0]
                row_dict['NAME'] = names[1]
                row_dict['COUNTRY'] = power_name_to_wdd(gp.power.name)
                row_dict['SCORE'] = gp.score
                rank = positions[gp.power]
                row_dict['RANK'] = rank
                row_dict['EXAEQUO'] = len([r for r in positions.values() if r == rank])
                # How did the game end?
                if soloer is not None:
                    if soloer == gp:
                        # This player won
                        row_dict['DRAW'] = 1
                    else:
                        # Another player won
                        row_dict['DRAW'] = 0
                if draw is not None:
                    if gp.power in draw_powers:
                        row_dict['DRAW'] = draw_powers.count()
                    else:
                        row_dict['DRAW'] = 0
                # Add in centre counts
                dots = centrecount_set.filter(power=gp.power)
                cc = None
                for cc in dots:
                    row_dict[_centrecount_year_to_wdd(cc.year)] = cc.count
                    if cc.count == 0 and not 'YEAR_ELIMINATION' in row_dict:
                        row_dict['YEAR_ELIMINATION'] = cc.year % (FIRST_YEAR-1)
                if cc:
                    row_dict['NB_CENTRE'] = cc.count
                # Write a row for this player in this game
                writer.writerow(row_dict)

    return response
