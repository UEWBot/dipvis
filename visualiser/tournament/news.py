# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2020 Chris Brand
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
Django news file for the Diplomacy Tournament Visualiser.
"""

import random

from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from tournament.models import DrawSecrecy
from tournament.models import Tournament, Round, Game, CentreCount
from tournament.players import position_str

# Mask values to choose which news strings to include
MASK_BOARD_TOP = 1 << 0
MASK_GAINERS = 1 << 1
MASK_LOSERS = 1 << 2
MASK_DRAW_VOTES = 1 << 3
MASK_ELIMINATIONS = 1 << 4
MASK_SC_CHANGES = 1 << 5
MASK_SC_CHANGE_COUNTS = 1 << 6
MASK_SC_OWNER_COUNTS = 1 << 7
MASK_ALL_NEWS = (1 << 8) - 1
# All the ones that require SC ownership information
MASK_OWNERSHIP = MASK_SC_CHANGES | MASK_SC_CHANGE_COUNTS | MASK_SC_OWNER_COUNTS


def _tournament_news(t):
    """
    Returns a list of news strings for the tournament
    """
    results = []
    include_leader = False
    current_round = t.current_round()
    # Always include the number of players
    if t.is_finished():
        tense_str = _('were')
    else:
        tense_str = _('are')
    results.append(_('%(count)d players %(are)s registered to play in the tournament.')
                   % {'count': t.tournamentplayer_set.count(),
                      'are': tense_str})
    if current_round:
        # Include who is leading the tournament
        include_leader = True
        if current_round.in_progress():
            # And which round is currently being played
            results.append(_(u'Round %(r_num)d of %(rounds)d is currently being played.')
                           % {'r_num': current_round.number(),
                              'rounds': t.round_set.count()})
        else:
            results.append(_(u'Round %(r_num)d of %(rounds)d will start at %(date)s.')
                           % {'r_num': current_round.number(),
                              'rounds': t.round_set.count(),
                              'date': str(current_round.start)})
        # Get the news for the current round
        results += _round_news(current_round)
    # If the tournament is over, just report the top three players, plus best countries
    elif t.is_finished():
        for player, (rank, score) in t.positions_and_scores().items():
            if rank in [1, 2, 3]:
                results.append(_(u'%(player)s came %(pos)s, with a score of %(score).2f.')
                               % {'player': str(player),
                                  'pos':  position_str(rank),
                                  'score':  score})
        # Add best countries
        for power, gps in t.best_countries().items():
            gp = gps[0]
            if len(gps) == 1:
                results.append(ngettext('%(player)s won Best %(country)s with one centre and a score of %(score).2f in game %(game)s of round %(round)d.',
                                        '%(player)s won Best %(country)s with %(dots)d centres and a score of %(score).2f in game %(game)s of round %(round)d.',
                                  gp.final_sc_count())
                               % {'player': str(gp.player),
                                  'country': _(power.name),
                                  'dots': gp.final_sc_count(),
                                  'score': gp.score,
                                  'game': gp.game.name,
                                  'round': gp.game.the_round.number()})
            else:
                # Tie for best power
                winner_str = ', '.join([str(p.player) for p in gps])
                results.append(ngettext('Best %(country)s was jointly won by %(winner_str)s with one centre and a score of %(score).2f.',
                                        'Best %(country)s was jointly won by %(winner_str)s with %(dots)d centres and a score of %(score).2f.',
                               gp.final_sc_count())
                               % {'country': _(power.name),
                                  'winner_str': winner_str,
                                  'dots': gp.final_sc_count(),
                                  'score': gp.score})
    else:
        # which rounds have been played ?
        played_rounds = 0
        for r in t.round_set.all():
            if r.is_finished():
                played_rounds += 1
        if played_rounds == 0:
            results.append(_(u'Tournament has yet to start.'))
        else:
            results.append(ngettext('One of %(rounds)d has been played.',
                                    '%(r_num)d of %(rounds)d have been played.',
                                    played_rounds) % {'r_num': played_rounds,
                                                      'rounds': t.round_set.count()})
            # Include who is leading the tournament
            include_leader = True
    if include_leader:
        the_scores = t.scores_detail()
        if the_scores:
            max_score = max(the_scores.values())
            winners = [str(k) for k, v in the_scores.items() if v == max_score]
            player_str = ', '.join(winners)
            results.append(_(u'If the tournament ended now, the winning score would be %(score).2f for %(players)s.')
                           % {'score': max_score,
                              'players': player_str})
            # How many players are close to the leader?
            contenders = len([s for s in the_scores.values() if s >= max_score * 0.9]) - 1
            results.append(ngettext("One player has at least 90%% of the leader's current tournament score",
                                    "%(count)d players have at least 90%% of the leader's current tournament score",
                                    contenders) % {'count': contenders})
        # Include the top score from each previous round (if any)
        for r in t.round_set.all():
            if r.is_finished():
                results.append(_round_leader_str(r))
    # Shuffle the resulting list
    random.shuffle(results)
    return results


def _round_leader_str(r):
    """
    Returns a news string detailing the person with the best score for the round.
    """
    the_scores = r.scores()
    if not the_scores:
        return None
    max_score = max(the_scores.values())
    winners = [k for k, v in the_scores.items() if v == max_score]
    if r.is_finished():
        done_str = _(u'Final')
    else:
        done_str = _(u'Current')
    player_str = ', '.join([str(w) for w in winners])
    return _(u'%(done)s top score for round %(r_num)d is %(score).2f for %(players)s.') % {'done': done_str,
                                                                                           'r_num': r.number(),
                                                                                           'score': max_score,
                                                                                           'players': player_str}


def _round_news(r):
    """
    Returns a list of news strings for the round.

    This is the latest news for every game in the round.
    """
    results = []
    # Include who has done best in the round (so far)
    ls = _round_leader_str(r)
    if ls:
        results.append(ls)
    # Always include the number of players
    if r.is_finished():
        plural_tense_str = _('were')
        singular_tense_str = _('was')
    else:
        plural_tense_str = _('are')
        singular_tense_str = _('is')
    results.append(_('%(count)d players %(are)s registered to play in the round.')
                   % {'count': r.roundplayer_set.count(),
                      'are': plural_tense_str})
    # Get the news for every game in the round
    done_games = 0
    toppers = []
    for g in r.game_set.all():
        toppers += g.board_toppers()
        if g.is_finished:
            done_games += 1
        results += _game_news(g, include_game_name=True)
    if toppers:
        max_centres = max(cc.count for cc in toppers)
        toppers = [cc for cc in toppers if cc.count == max_centres]
        toppers_str = ', '.join([_('%(power)s in %(game)s') % {'power': _(cc.power.abbreviation),
                                                               'game': cc.game.name} for cc in toppers])
        results.append(_('Highest centre count in round %(r_num)d %(is)s %(dots)d for %(players)s.') % {'r_num': r.number(),
                                                                                                        'is': singular_tense_str,
                                                                                                        'dots': max_centres,
                                                                                                        'players': toppers_str})
    # Note if the round has finished
    if r.is_finished():
        results.append(_(u'Round %(r_num)d has ended.') % {'r_num': r.number()})
    elif not r.in_progress():
        results.append(_(u'Round %(r_num)d has not yet started.') % {'r_num': r.number()})
    else:
        # Otherwise, add a count of completed games
        results.append(ngettext('One of the %(total_num)d games in round %(r_num)d has ended.',
                                '%(num_done)d of the %(total_num)d games in round %(r_num)d have ended.',
                                done_games) % {'num_done': done_games,
                                               'r_num': r.number(),
                                               'total_num': r.game_set.count()})
        # TODO Add time played in the round so far (difficult to internationalise ?)
    # Shuffle the resulting list
    random.shuffle(results)
    return results


def _sc_gains_and_losses(prev_scos, current_scos):
    """
    Find interesting changes in SC ownership

    Returns two dicts (gains then losses), indexed by GreatPower, of
      2-tuples containing SupplyCentre and other Power (previous owner
      (None if neutral) or new owner).
    Parameters are two QuerySets for last year and this year's
      SupplyCentreOwnerships.
    """
    # Can't do anything without two consecutive years information
    if not prev_scos.exists() or not current_scos.exists():
        return {}, {}
    # Extract the info we need into two sets that can be operated on
    prev = set()
    for sco in prev_scos.all():
        prev.add((sco.sc, sco.owner))
    current = set()
    for sco in current_scos.all():
        current.add((sco.sc, sco.owner))
    gains = {}
    losses = {}
    for sc, owner in prev - current:
        for s, o in current:
            if s == sc:
                new_owner = o
                break
        losses.setdefault(owner, []).append((sc, new_owner))
    for sc, owner in current - prev:
        prev_owner = None
        for s, o in prev:
            if s == sc:
                prev_owner = o
                break
        gains.setdefault(owner, []).append((sc, prev_owner))
    return gains, losses


def _game_news(g, include_game_name=False, mask=MASK_ALL_NEWS, for_year=None):
    """
    Returns a list of strings the describe the latest events in the game
    """
    if include_game_name:
        gn_str = _(u' in game %(name)s') % {'name': g.name}
    else:
        gn_str = ''
    if g.is_finished and ((for_year is None) or (for_year >= g.final_year())):
        # Just report the final result
        return [g.result_str(include_game_name) + '.']
    centres_set = g.centrecount_set.order_by('-year')
    if for_year:
        centres_set = centres_set.filter(year__lte=for_year)
    # Which is the most recent year we have info for ?
    last_year = centres_set[0].year
    # If the game just started, there is no news, so return the background instead
    if last_year == 1900:
        return g.background()
    gps = g.gameplayer_set.all()
    current_scs = centres_set.filter(year=last_year)
    current_scos = g.supplycentreownership_set.filter(year=last_year)
    results = []
    if (mask & MASK_SC_OWNER_COUNTS) != 0:
        # Which dots have had lots of owners?
        owner_sets = {}
        for sco in g.supplycentreownership_set.filter(year__lte=last_year):
            if sco.sc not in owner_sets:
                owner_sets[sco.sc] = set()
            owner_sets[sco.sc].add(sco.owner)
        for sc, set_ in owner_sets.items():
            if len(set_) > 3:
                results.append(_('%(dot)s has been owned by %(owners)d different Great Powers (%(list)s).')
                               % {'dot': sc,
                                  'owners': len(set_),
                                  'list': ','.join([_(p.abbreviation) for p in set_])})
    if (mask & MASK_BOARD_TOP) != 0:
        # Who's topping the board ?
        max_scs = current_scs.order_by('-count')[0].count
        first = current_scs.order_by('-count').filter(count=max_scs)
        first_str = ', '.join([f'{gps.get(power=scs.power).player} ({_(scs.power.abbreviation)}' for scs in list(first)])
        results.append(_(u'Highest SC count%(game)s is %(dots)d, for %(player)s.')
                       % {'game': gn_str,
                          'dots': max_scs,
                          'player': first_str})
    # TODO Guaranteed to be True?
    if last_year > 1900:
        prev_scs = centres_set.filter(year=last_year-1)
        prev_scos = g.supplycentreownership_set.filter(year=last_year-1)
        sc_gains, sc_losses = _sc_gains_and_losses(prev_scos, current_scos)
        if not prev_scos.exists() or not current_scos.exists():
            # Filter out stuff that needs supply centre ownership information
            mask &= ~MASK_OWNERSHIP
    else:
        # We only look for differences, so just force no differences
        prev_scs = current_scs
        sc_gains = {}
        sc_losses = {}
    for scs in current_scs:
        power = scs.power
        try:
            prev = prev_scs.get(power=power)
        except CentreCount.DoesNotExist:
            continue
        # Who gained 2 or more centres in the last year ?
        if (mask & MASK_GAINERS) != 0:
            if scs.count - prev.count > 1:
                results.append(_(u'%(player)s (%(power)s) grew from %(old)d to %(new)d centres%(game)s.')
                               % {'player': gps.get(power=power).player,
                                  'power': _(power.abbreviation),
                                  'old': prev.count,
                                  'new': scs.count,
                                  'game': gn_str})
        # Who lost 2 or more centres in the last year ?
        if (mask & MASK_LOSERS) != 0:
            if prev.count - scs.count > 1:
                results.append(ngettext('%(player)s (%(power)s) shrank from %(old)d to %(new)d centre%(game)s.',
                                        '%(player)s (%(power)s) shrank from %(old)d to %(new)d centres%(game)s.',
                                        scs.count)
                               % {'player': gps.get(power=power).player,
                                  'power': _(power.abbreviation),
                                  'old': prev.count,
                                  'new': scs.count,
                                  'game': gn_str})
        # Who took 2 or more, lost 2 or more, or had a total of 4 or more gains and losses?
        if (mask & MASK_SC_CHANGES) != 0:
            gains = sc_gains.get(power, [])
            losses = sc_losses.get(power, [])
            if (len(gains) > 2) or (len(losses) > 2) or (len(gains) + len(losses) > 3):
                if gains:
                    gains_str = ''
                    for s, p in gains:
                        if gains_str:
                            gains_str += ', '
                        if p:
                            gains_str += _('%(sc)s (from %(power)s)') % {'sc': _(s.abbreviation),
                                                                         'power': _(p.abbreviation)}
                        else:
                            gains_str += _('%(sc)s (neutral)') % {'sc': _(s.abbreviation)}
                else:
                    gains_str = _('no centres')
                if losses:
                    losses_str = ', '.join(_('%(sc)s (to %(power)s)') % {'sc': _(s.abbreviation),
                                                                         'power': _(p.abbreviation)} for s, p in losses)
                else:
                    losses_str = _('no centres')
                results.append(_('%(player)s (%(power)s) took %(gains)s and lost %(losses)s%(game)s.')
                               % {'player': gps.get(power=power).player,
                                  'power': _(power.abbreviation),
                                  'gains': gains_str,
                                  'losses': losses_str,
                                  'game': gn_str})
    # How many non-neutrals were captured?
    if (last_year > 1900) and ((mask & MASK_SC_CHANGE_COUNTS) != 0):
        count = 0
        for loss in sc_losses.values():
            count += len(loss)
        results.append(ngettext('One non-neutral centre changed hands%(game)s.',
                                '%(count)d non-neutral centres changed hands%(game)s.',
                                count)
                       % {'count': count,
                          'game': gn_str})
    if (mask & MASK_DRAW_VOTES) != 0:
        # How many draw votes have there been ?
        dp_queryset = g.drawproposal_set.filter(year__lte=last_year)
        votes = dp_queryset.count()
        results.append(ngettext('One draw vote has been taken%(game)s.',
                                '%(count)d draw votes have been taken%(game)s.',
                                votes) % {'count': votes, 'game': gn_str})
        # What draw votes failed recently ?
        # Note that it's fairly arbitrary where we draw the line here
        draws_set = dp_queryset.order_by('-year').filter(year__gte=last_year)
        for d in draws_set:
            powers = d.powers()
            sz = len(powers)
            incl = []
            for power in powers:
                game_player = g.gameplayer_set.get(power=power)
                incl.append(_(u'%(player)s (%(power)s)') % {'player': game_player.player,
                                                            'power': _(power.abbreviation)})
            incl_str = ', '.join(incl)
            if g.the_round.tournament.draw_secrecy == DrawSecrecy.COUNTS:
                count_str = _(', %(for)d for, %(against)d against') % {'for': d.votes_in_favour,
                                                                      'against': d.votes_against()}
            else:
                count_str = ''
            if sz == 1:
                d_str = _(u'Vote to concede to %(powers)s failed%(game)s%(count)s.') % {'powers': incl_str,
                                                                                        'game': gn_str,
                                                                                        'count': count_str}
            else:
                d_str = _(u'Draw vote for %(n)d-way between %(powers)s failed%(game)s%(count)s.') % {'n': sz,
                                                                                                     'powers': incl_str,
                                                                                                     'game': gn_str,
                                                                                                     'count': count_str}
            results.append(d_str)
    if (mask & MASK_ELIMINATIONS) != 0:
        # Who has been eliminated so far, and when ?
        zeroes = centres_set.filter(count=0).reverse()
        while zeroes:
            scs = zeroes[0]
            power = scs.power
            zeroes = zeroes.exclude(power=power)
            results.append(_(u'%(player)s (%(power)s) was eliminated in %(year)d%(game)s.')
                           % {'player': gps.get(power=power).player,
                              'power': _(power.abbreviation),
                              'year': scs.year,
                              'game': gn_str})
    # Shuffle the resulting list
    random.shuffle(results)
    return results

def news(obj, for_year=None):
    """Return a list of events in obj"""
    if isinstance(obj, Tournament):
        return _tournament_news(obj)
    if isinstance(obj, Round):
        return _round_news(obj)
    if isinstance(obj, Game):
        return _game_news(obj, for_year=for_year)
    raise NotImplementedError
