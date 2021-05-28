# Diplomacy Tournament Visualiser
# Copyright (C) 2019 Chris Brand
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

# This file contains assorted utility code.
# Most of these functions are not used by DipVis, but have proved
# useful to maintain a DipVis site.

"""
This module provides utility functions for DipVis.
"""

from tournament import backstabbr
from tournament.diplomacy import FIRST_YEAR
from tournament.models import CentreCount, DrawProposal, Game, GameImage, GamePlayer
from tournament.models import Preference, Round, RoundPlayer, SeederBias
from tournament.models import SupplyCentreOwnership, Tournament, TournamentPlayer
from tournament.game_views import _bs_ownerships_to_sco, _bs_counts_to_cc


def map_to_backstabbr_power(gp):
    """Map a GreatPower to a Backstabbr.POWER."""
    for power in backstabbr.POWERS:
        if gp.abbreviation == power[0]:
            return power
    raise ValueError(gp)

def populate_bs_profile_urls(dry_run=False):
    """
    Finds as many Backstabbr profile URLs as possible
    and adds them to the appropriate Players.
    """
    games = 0
    players_left = 0
    players_changed = 0
    mismatches = 0
    for g in Game.objects.filter(external_url__contains='backstabbr.com'):
        print("Checking game %s" % g.external_url)
        # read the game page
        bg = g.backstabbr_game()
        if bg is None:
            print("Failed to extract backstabbr URL - skipping")
            continue
        games += 1
        for gp in g.gameplayer_set.all():
            player, url = bg.players[map_to_backstabbr_power(gp.power)]
            if gp.player.backstabbr_profile_url:
                if url == gp.player.backstabbr_profile_url:
                    players_left += 1
                else:
                    print("%s: In-game URL %s doesn't match stored URL %s" % (str(gp.player),
                                                                              url,
                                                                              gp.player.backstabbr_profile_url))
                    mismatches += 1
            else:
                # Add the profile URL
                print("Adding URL %s to %s" % (url, str(gp.player)))
                if not dry_run:
                    gp.player.backstabbr_profile_url = url
                    gp.player.save()
                players_changed += 1
    print("Checked %d games" % games)
    print("Matched %d profile URLs" % players_left)
    if dry_run:
        print("Updated %d profile URLs" % players_changed)
    else:
        print("Would have updated %d profile URLs" % players_changed)
    print("%d mismatches detected" % mismatches)

def populate_missed_years(game, dry_run=False):
    """
    For a game on backstabbr, check for missing years and fill them in.
    """
    # Parse the current game page on Backstabbr
    bg = game.backstabbr_game()
    if bg is None:
        print("No Backstabbr URL for %s" % game)
        return
    for year in range(FIRST_YEAR, bg.year):
        if not game.centrecount_set.filter(year=year).exists():
            print("Reading results for %d" % year)
            if dry_run:
                continue
            parsed_turn = bg.turn_details(backstabbr.SPRING, year+1)
            sc_counts = parsed_turn[0]
            sc_ownership = parsed_turn[2]
            # Add the appropriate SupplyCentreOwnerships and/or CentreCounts
            _bs_ownerships_to_sco(game, year, sc_ownership)
            if len(bg.sc_ownership):
                game.create_or_update_sc_counts_from_ownerships(year)
            else:
                _bs_counts_to_cc(game, year, sc_counts)

def clean_duplicate_player(del_player, keep_player, dry_run=False):
    """
    Moves any TournamentPlayers, RoundPlayers, and GamePlayers
    from del_player to keep_player.
    If dry_run is True, just report what changes would be made.
    """
    # First check that what we're doing makes sense
    if del_player.first_name != keep_player.first_name:
        print("Player first names don't match!")
        return
    if del_player.last_name != keep_player.last_name:
        print("Player last names don't match!")
        return
    if del_player.wdd_player_id is not None:
        print("Player to delete has a WDD player id!")
        return

    if keep_player.email != del_player.email:
        if del_player.email:
            print("Player to delete has an email address!")
            return

    if keep_player.backstabbr_username != del_player.backstabbr_username:
        if del_player.backstabbr_username:
            print("Player to delete has a backstabbr username!")
            return

    if keep_player.backstabbr_profile_url != del_player.backstabbr_profile_url:
        if del_player.backstabbr_profile_url:
            print("Player to delete has a backstabbr profile URL!")
            return

    if keep_player.picture != del_player.picture:
        if del_player.picture:
            print("Player to delete has a picture!")
            return

    if keep_player.user != del_player.user:
        if del_player.user is not None:
            print("Player to delete has an account!")
            return

    # Move GamePlayers
    for gp in del_player.gameplayer_set.all():
        print("Moving %s" % gp)
        if not dry_run:
            gp.player = keep_player
            gp.save()

    # Move RoundPlayers
    for rp in del_player.roundplayer_set.all():
        print("Moving %s" % rp)
        if not dry_run:
            rp.player = keep_player
            rp.save()

    # Move TournamentPlayers
    for tp in del_player.tournamentplayer_set.all():
        print("Moving %s" % tp)
        if not dry_run:
            tp.player = keep_player
            tp.save()

    if dry_run:
        print("No issues found")
    else:
        print("Player with private key %d ready to delete from the admin" % del_player.pk)


def clone_tournament(t):
    """
    Creates a copy of Tournament t, with the same players,
    rounds, results, etc.
    Returns the new Tournament, which can then safely be
    manipulated without changing the original.
    The attributes will all be identical except for:
    - the name will have " Copy" appended
    - editable will be True
    - is_published will be False
    - wdd_tournament_id will be null
    """
    new_t = Tournament.objects.create(name=t.name + " Copy",
                                      start_date=t.start_date,
                                      end_date=t.end_date,
                                      tournament_scoring_system=t.tournament_scoring_system,
                                      round_scoring_system=t.round_scoring_system,
                                      draw_secrecy=t.draw_secrecy,
                                      is_published=False,
                                      seed_games=t.seed_games,
                                      power_assignment=t.power_assignment,
                                      editable=True,
                                      best_country_criterion=t.best_country_criterion)
    for m in t.managers.all():
        new_t.managers.add(m)

    # Copy TournamentPlayers and Preferences
    for tp in t.tournamentplayer_set.all():
        new_tp = TournamentPlayer.objects.create(player=tp.player,
                                                 tournament=new_t,
                                                 score=tp.score,
                                                 unranked=tp.unranked)
        if tp.uuid_str:
            # Create a different UUID for the new TP
            new_tp._generate_uuid()
            new_tp.save()
        for p in tp.preference_set.all():
            Preference.objects.create(player=new_tp,
                                      power=p.power,
                                      ranking=p.ranking)

    # Copy Rounds and RoundPlayers, Games and GamePlayers,
    # DrawProposals, GameImages, CentreCounts, and SupplyCentreOwnerships
    for r in t.round_set.all():
        new_r = Round.objects.create(tournament=new_t,
                                     scoring_system=r.scoring_system,
                                     dias=r.dias,
                                     start=r.start,
                                     final_year=r.final_year,
                                     earliest_end_time=r.earliest_end_time,
                                     latest_end_time=r.latest_end_time)
        for rp in r.roundplayer_set.all():
            RoundPlayer.objects.create(player=rp.player,
                                       the_round=new_r,
                                       score=rp.score,
                                       game_count=rp.game_count)
        for g in r.game_set.all():
            new_g = Game.objects.create(name=g.name,
                                        started_at=g.started_at,
                                        is_finished=g.is_finished,
                                        is_top_board=g.is_top_board,
                                        the_round=new_r,
                                        the_set=g.the_set)
            for gp in g.gameplayer_set.all():
                GamePlayer.objects.create(player=gp.player,
                                          game=new_g,
                                          power=gp.power,
                                          score=gp.score)
            for dp in g.drawproposal_set.all():
                new_dp = DrawProposal.objects.create(game=new_g,
                                                     year=dp.year,
                                                     season=dp.season,
                                                     passed=dp.passed,
                                                     proposer=dp.proposer,
                                                     votes_in_favour=dp.votes_in_favour)
                for p in dp.drawing_powers.all():
                    new_dp.drawing_powers.add(p)
            for gi in g.gameimage_set.all():
                # Skip the auto-created image
                GameImage.objects.get_or_create(game=new_g,
                                                year=gi.year,
                                                season=gi.season,
                                                phase=gi.phase,
                                                image=gi.image)
            for cc in g.centrecount_set.all():
                # Skip the auto-created ones
                CentreCount.objects.get_or_create(power=cc.power,
                                                  game=new_g,
                                                  year=cc.year,
                                                  count=cc.count)
            for sco in g.supplycentreownership_set.all():
                # Skip the auto-created ones
                SupplyCentreOwnership.objects.get_or_create(game=new_g,
                                                            year=sco.year,
                                                            sc=sco.sc,
                                                            owner=sco.owner)

    # copy SeederBiases
    for sb in SeederBias.objects.filter(player1__tournament=t):
        p1 = TournamentPlayer.objects.get(tournament=new_t, player=sb.player1.player)
        p2 = TournamentPlayer.objects.get(tournament=new_t, player=sb.player2.player)
        SeederBias.objects.create(player1=p1,
                                  player2=p2)

    return new_t


def fix_round_players(the_round, dry_run=False):
    """
    Utility to clean up RoundPlayers.
    Checks for any RoundPlayers without Games in the Round.
    If they don't have a game_count of zero, delete them.
    Then checks for any Games in the Round where there is no
    corresponding RoundPlayer, and creates one.
    Finally, triggers a score recalculation for all Games in the round.
    If dry_run is True, just report what would be done.

    Note that this can remove RoundPlayers who checked in but didn't play
    """
    # First, check that the Round does have Games. If not, abort
    game_set = the_round.game_set.all()
    if not game_set.exists():
        print("No games in round - exiting.\n")
        return;
    # Check for spurious RoundPlayers
    # game_count gets reset back to 1 by the roll call page,
    # so this could delete a player who sat out the round
    for rp in the_round.roundplayer_set.filter(game_count=1):
        if not game_set.filter(gameplayer__player=rp.player).exists():
            print("%s didn't actually play in the round - deleting.\n" % rp)
            if not dry_run:
                rp.delete()
    # Check for missing RoundPlayers
    for g in game_set.all():
        for gp in g.gameplayer_set.all():
            if not RoundPlayer.objects.filter(player=gp.player).exists():
                print("Missing RoundPlayer %s - adding\n" % gp.player)
                if not dry_run:
                    RoundPlayer.objects.create(player=gp.player,
                                               the_round=the_round)
        # Trigger a score recalculation
        print("Saving game %s to trigger score recalculation\n" % g);
        if not dry_run:
            g.save()
