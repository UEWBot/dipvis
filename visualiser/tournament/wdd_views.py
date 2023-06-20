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

# CSV export for WDD


def _power_name_to_wdd(name):
    """Map a power name to a WDD country code"""
    # 0 for variant (standard), plus first two letters of the country name (in English)
    return '0%s' % name[0:2].upper()


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
    """Returns the number (1..12) for the specified award at the tournament"""
    # We don't actually check that we return <= 12. WDD will ignore any extras
    assert award.power is None
    for i, a in enumerate(tournament.awards.order_by('name'), 1):
        if a == award:
            return i
    raise AssertionError(f'award {award} not found in {tournament}')


def view_classification_csv(request, tournament_id):
    """Return a WDD-compatible "classification" CSV file for the tournament"""
    t = get_visible_tournament_or_404(tournament_id, request.user)
    tps = t.tournamentplayer_set.order_by('-score')
    # Grab the tournament scores and positions, "if it ended now"
    t_positions_and_scores = t.positions_and_scores()[0]
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
               'SCORE',
              ]
    # Score for each round (extras don't matter)
    for i in range(1, 9):
        headers.append('R%d' % i)
    # Best country stuff
    for p in GreatPower.objects.all():
        wdd_pwr = _power_name_to_wdd(p.name)
        headers.append('RK_%s' % wdd_pwr)
        headers.append('PT_%s' % wdd_pwr)
        headers.append('CT_%s' % wdd_pwr)
        headers.append('HEAT_%s' % wdd_pwr)
        headers.append('BOARD_%s' % wdd_pwr)
    # Other awards
    for n in range(1, 13):
        headers.append('RK_AWA_%d' % n)
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
    response['Content-Disposition'] = 'attachment; filename="%s%dclassification.csv"' % (t.name,
                                                                                         t.start_date.year)

    writer = csv.DictWriter(response, fieldnames=headers)
    writer.writeheader()
    # One row per player (row order and field order don't matter)
    for tp in tps:
        p = tp.player
        p_score = t_positions_and_scores[p][1]
        rank = t_positions_and_scores[p][0]
        if rank == Tournament.UNRANKED:
            rank = '999'
        # First the stuff that is global to the tournament and applies to all players
        names = p.wdd_firstname_lastname()
        row_dict = {'FIRST NAME': names[0],
                    'NAME': names[1],
                    'HOMONYME': '1',  # User Guide says "Set to 1"
                    'RANK': rank,
                    # No. of players with the same rank
                    'EXAEQUO': len([s for _, s in t_positions_and_scores.values() if s == p_score]),
                    'SCORE': p_score,
                   }
        # Add in round score for each round played
        for rp in tp.roundplayers():
            row_dict['R%d' % rp.the_round.number()] = rp.score
        # Add awards
        for award in tp.awards.all():
            if award.power is not None:
                for gp in _power_award_to_gameplayers(t, award):
                    if gp.player == p:
                        wdd_pwr = _power_name_to_wdd(award.power.name)
                        row_dict['RK_%s' % wdd_pwr] = 1
                        row_dict['PT_%s' % wdd_pwr] = gp.score
                        row_dict['CT_%s' % wdd_pwr] = gp.game.centrecount_set.filter(power=award.power).last().count
                        row_dict['HEAT_%s' % wdd_pwr] = gp.game.the_round.number()
                        row_dict['BOARD_%s' % wdd_pwr] = _game_to_wdd_id(gp.game)
            else:
                row_dict['RK_AWA_%d' % _award_number(t, award)] = 1
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
               'EXAEQUO',  # Last of the mandatory ones
               'SCORE',
               'NB_CENTRE',
               'YEAR_ELIMINATION',
               'DRAW',
              ]
    # Centre count for each year (extras don't matter)
    for i in range(1, 21):
        headers.append('CT_%02d' % i)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s%dboards.csv"' % (t.name,
                                                                                 t.start_date.year)

    writer = csv.DictWriter(response, fieldnames=headers)
    writer.writeheader()

    # One row per game, per player
    r_row_dict = {}
    r_row_dict['HOMONYME'] = '1'  # User Guide says "Set to 1"
    for r in t.round_set.all():
        r_row_dict['ROUND'] = r.number()
        g_row_dict = r_row_dict.copy()
        for g in r.game_set.all():
            g_row_dict['BOARD'] = _game_to_wdd_id(g)
            positions = g.positions()
            draw = g.passed_draw()
            soloer = g.soloer()
            # TODO This is broken with replacement players
            for gp in g.gameplayer_set.all():
                names = gp.player.wdd_firstname_lastname()
                row_dict = g_row_dict.copy()
                row_dict['FIRST NAME'] = names[0]
                row_dict['NAME'] = names[1]
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
