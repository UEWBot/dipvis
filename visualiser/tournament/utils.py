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

from tournament.models import CentreCount, DrawProposal, Game, GameImage, GamePlayer
from tournament.models import Preference, Round, RoundPlayer, SeederBias
from tournament.models import SupplyCentreOwnership, Tournament, TournamentPlayer


def clean_duplicate_player(del_player, keep_player):
    """
    Moves any TournamentPlayers, RoundPlayers, and GamePlayers
    from del_player to keep_player.
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
        gp.player = keep_player
        gp.save()

    # Move RoundPlayers
    for rp in del_player.roundplayer_set.all():
        print("Moving %s" % rp)
        rp.player = keep_player
        rp.save()

    # Move TournamentPlayers
    for tp in del_player.tournamentplayer_set.all():
        print("Moving %s" % tp)
        tp.player = keep_player
        tp.save()

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
                                          first_year=gp.first_year,
                                          first_season=gp.first_season,
                                          last_year=gp.last_year,
                                          last_season=gp.last_season,
                                          score=gp.score)
            for dp in g.drawproposal_set.all():
                DrawProposal.objects.create(game=new_g,
                                            year=dp.year,
                                            season=dp.season,
                                            passed=dp.passed,
                                            proposer=dp.proposer,
                                            power_1=dp.power_1,
                                            power_2=dp.power_2,
                                            power_3=dp.power_3,
                                            power_4=dp.power_4,
                                            power_5=dp.power_5,
                                            power_6=dp.power_6,
                                            power_7=dp.power_7,
                                            votes_in_favour=dp.votes_in_favour)
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
                                  player2=p2,
                                  weight=sb.weight)

    return new_t


def fix_round_players(the_round):
    """
    Utility to clean up RoundPlayers.
    Checks for any RoundPlayers without Games in the Round.
    If they don't have a game_count of zero, delete them.
    Then checks for any Games in the Round where there is no
    corresponding RoundPlayer, and creates one.
    Finally, triggers a score recalculation for all Games in the round.
    """
    # First, check that the Round does have Games. If not, abort
    game_set = the_round.game_set.all()
    if not game_set.exists():
        print("No games in round - exiting.\n")
        return;
    # Check for suprious RoundPlayers
    for rp in the_round.roundplayer_set.filter(game_count=1):
        if not game_set.filter(gameplayer__player=rp.player).exists():
            print("%s didn't actually play in the round.\n" % rp)
            rp.delete()
    # Check for missing RoundPlayers
    for g in game_set.all():
        for gp in g.gameplayer_set.all():
            if not RoundPlayer.filter(player=gp.player).exists():
                print("Missing RoundPlayer %s\n" % gp.player)
                RoundPlayer.objects.create(player=gp.player,
                                           the_round=the_round)
        # Trigger a score recalculation
        g.save()
