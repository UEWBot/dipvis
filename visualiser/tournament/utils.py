# Diplomacy Tournament Visualiser
# Copyright (C) 2019-2024 Chris Brand
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

import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime, time, timedelta

from django_countries.fields import Country

from django.utils import timezone

from tournament import backstabbr
from tournament.background import WDDBackground
from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR
from tournament.models import Award, CentreCount, DrawProposal, Game, GameImage
from tournament.models import GamePlayer, Preference, Round, RoundPlayer, SeederBias
from tournament.models import SupplyCentreOwnership, Tournament, TournamentPlayer
from tournament.models import NO_SCORING_SYSTEM_STR
from tournament.players import Player
from tournament.players import PlayerTournamentRanking, PlayerGameResult, PlayerAward
from tournament.round_views import _create_game_seeder, _generate_game_name
from tournament.game_views import _bs_ownerships_to_sco, _sc_counts_to_cc
from tournament.wdd import wdd_nation_to_country, wdd_url_to_tournament_id, UnrecognisedCountry
from tournament.wdd_views import _power_award_to_gameplayers


def add_wep_scores(player, dry_run=False):
    """Update the Player's PlayerTournamentRankings to set the wep_score attribute."""
    # First get the WPE scores
    bg = WDDBackground(player.wdd_player_id)
    scores = bg.wpe_scores()
    # Now update their rankings
    ptr_s = player.playertournamentranking_set.all()
    for score in scores:
        wdd_id = wdd_url_to_tournament_id(score['WDD WPE URL'])
        for ptr in ptr_s.filter(wdd_tournament_id=wdd_id):
            print("Setting wpe_score for %s to %.2f" % (score['Tournament'], float(score['Score'])))
            if not dry_run:
                ptr.wpe_score = score['Score']
                ptr.save(update_fields=['wpe_score'])


def map_to_backstabbr_power(gp):
    """Map a GreatPower to a Backstabbr.POWER."""
    for power in backstabbr.POWERS:
        if gp.abbreviation == power[0]:
            return power
    raise ValueError(gp)


def populate_bs_profile_urls(dry_run=False):
    """
    Finds as many Backstabbr profile URLs as possible and adds them to the appropriate Players.
    """
    games = 0
    players_left = 0
    players_changed = 0
    mismatches = 0
    for g in Game.objects.filter(external_url__contains='backstabbr.com'):
        print("Checking game %s" % g.external_url)
        # read the game page
        try:
            bg = g.backstabbr_game()
        except backstabbr.InvalidGameUrl:
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
                    gp.player.save(update_fields=['backstabbr_profile_url'])
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
    For a game on Backstabbr, check for missing years and fill them in.
    """
    # Parse the current game page on Backstabbr
    try:
        bg = game.backstabbr_game()
    except backstabbr.InvalidGameUrl:
        print("No Backstabbr URL for %s" % game)
        return
    for year in range(FIRST_YEAR, bg.year):
        if not game.centrecount_set.filter(year=year).count() == 7:
            print("Reading results for %d" % year)
            if dry_run:
                continue
            try:
                parsed_turn = bg.turn_details(backstabbr.SPRING, year+1)
            except backstabbr.InvalidGameUrl:
                print("Failed to read that year from backstabbr")
                continue
            sc_counts = parsed_turn[0]
            sc_ownership = parsed_turn[2]
            # Add the appropriate SupplyCentreOwnerships and/or CentreCounts
            _bs_ownerships_to_sco(game, year, sc_ownership)
            if len(bg.sc_ownership):
                game.create_or_update_sc_counts_from_ownerships(year)
            else:
                _sc_counts_to_cc(game, year, sc_counts)


def clean_duplicate_player(del_player, keep_player, dry_run=False):
    """
    Moves any TournamentPlayers, RoundPlayers, and GamePlayers from del_player to keep_player.

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
            gp.save(update_fields=['player'])

    # Move RoundPlayers
    for rp in del_player.roundplayer_set.all():
        print("Moving %s" % rp)
        if not dry_run:
            rp.player = keep_player
            rp.save(update_fields=['player'])

    # Move TournamentPlayers
    for tp in del_player.tournamentplayer_set.all():
        print("Moving %s" % tp)
        if not dry_run:
            tp.player = keep_player
            tp.save(update_fields=['player'])

    if dry_run:
        print("No issues found")
    else:
        print("Player with private key %d ready to delete from the admin" % del_player.pk)


def clone_tournament(t):
    """
    Clone a Tournament

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
        return
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
        print("Saving game %s to trigger score recalculation\n" % g)
        if not dry_run:
            g.save()


def find_missing_wdd_ids():
    """
    Report all Players with no wdd_player_id that should have one.
    """
    for p in Player.objects.filter(wdd_player_id=None):
        for tp in p.tournamentplayer_set.exclude(tournament__wdd_tournament_id=None):
            # It's possible that they were registered but never played
            if tp.roundplayers():
                print(p)
                break


def add_missing_wdd_ids(dry_run=False):
    """
    Find Players with no wdd_player_id that should have one and add it.
    """
    for p in Player.objects.filter(wdd_player_id=None):
        for tp in p.tournamentplayer_set.exclude(tournament__wdd_tournament_id=None):
            url = tp.tournament.wdd_url()
            page = requests.get(url,
                                timeout=1.0)
            soup = BeautifulSoup(page.text)
            for a in soup.find_all('a'):
                if not a.string:
                    continue
                url = a['href']
                if 'id_player' not in url:
                    continue
                wdd_id = url.split('=')[-1]
                name = str(a.string)
                if name.lower() == str(p).lower():
                    print("Giving %s WDD id %s" % (str(p), wdd_id))
                    if not dry_run:
                        p.wdd_player_id = int(wdd_id)
                        p.save(update_fields=['wdd_player_id'])
                        break


def add_best_country_awards_to_tournament(tournament, dry_run=False):
    """
    Add "Best Country" awards to a Tournament.

    Assumes that the seven "Best Country" awards have been created.
    """
    for power, gp_list in tournament.best_countries().items():
        a = Award.objects.filter(power=power).first()
        # First, add the Award to the Tournament
        print(f'Adding award "{a}" to {tournament}')
        if not dry_run:
            tournament.awards.add(a)
        # Then give to the appropriate TournamentPlayers
        for gp in gp_list:
            tp = gp.tournamentplayer()
            print(f'  Adding award "{a}" to {tp}')
            if not dry_run:
                tp.awards.add(a)


def add_best_country_awards(dry_run=False):
    """
    Add "Best Country" awards to all existing Tournaments.

    Useful after the new Award class is added and Tournaments already exist.
    Assumes that the seven "Best Country" awards have been created.
    """
    for t in Tournament.objects.all():
        add_best_country_awards_for_tournament(t, dry_run)


def clean_best_country_awards(dry_run=False):
    """
    Check for spurious "Best Country" awards and remove them.
    """
    for t in Tournament.objects.all():
        for a in t.awards.filter(power__isnull=False):
            best = t.best_countries()[a.power]
            tps = a.tournamentplayer_set.filter(tournament=t)
            if len(tps) > 1:
                # We have a best country award with multple recipients
                gps = _power_award_to_gameplayers(t, a)
                for tp in tps:
                    # Did any recipients not play that power?
                    tp_gp = None
                    for gp in gps:
                        if gp.player == tp.player:
                            tp_gp = gp
                            break;
                    if not tp_gp:
                        print(f"{tp} didn't play {a.power}")
                        if not dry_run:
                            tp.awards.remove(a)
                    # Was any recipient outplayed as that power?
                    if tp_gp not in best:
                        print(f'{tp} was outplayed as {a.power}')
                        if not dry_run:
                            tp.awards.remove(a)
                    # Are any recipients unranked?
                    if tp.unranked:
                        print(f'Removing {a} from unranked {tp}')
                        if not dry_run:
                            tp.awards.remove(a)


def set_nationalities(dry_run=False):
    """
    Set Player.nationalities as specified in the WDD, unless already set.
    """
    for p in Player.objects.filter(nationalities='', wdd_player_id__isnull=False):
        bg = WDDBackground(p.wdd_player_id)
        nats = bg.nationalities()
        if not nats:
            # No nationality information in the WDD
            print(f'WDD has no nationality for {p}')
            continue
        elif len(nats) > 1:
            # This is currently impossible
            print('Setting multiple nationalities is not supported')
        n = nats[0]
        try:
            c = wdd_nation_to_country(n)
        except UnrecognisedCountry:
            print(f'Skipping unrecognised country "{n}" for WDD player {p.wdd_player_id}')
            continue
        print(f'Setting nationality of {p} to {c.name}')
        if not dry_run:
            p.nationalities = c
            p.save(update_fields=['nationalities'])


def list_tournaments_missing_wdd_ids():
    """List completed tournaments without WDD ids (they should probably have one)"""
    for t in Tournament.objects.filter(wdd_tournament_id=None):
        if not t.is_finished:
            continue
        print(t)


def player_emails(for_tournament):
    """Return a list of emails for players registered for the Tournament"""
    return [tp.player.email for tp in for_tournament.tournamentplayer_set.all()]


def recreate_seeder(for_tournament, round_number):
    """
    Prepare to seed games for the specified Round

    Returns a GameSeeder, set of players sitting out,
    and set of players playing two games.
    """
    r = for_tournament.round_numbered(round_number)
    seeder = _create_game_seeder(for_tournament, r)
    sitters = set()
    two_boarders = set()
    for tp in for_tournament.tournamentplayer_set.all():
        try:
            rp = r.roundplayer_set.get(player=tp.player)
        except RoundPlayer.DoesNotExist:
            sitters.add(tp)
        else:
            if rp.game_count == 0:
                sitters.add(tp)
            elif rp.game_count == 2:
                two_boarders.add(tp)
    return seeder, sitters, two_boarders


def _import_dixie_round(r_num, player, tournament, row):
    """
    Utility function for import_dixie_csv()
    """
    if row['round%d' % r_num] == '%d' % r_num:
        # Create a RoundPlayer
        r = tournament.round_numbered(r_num)
        rp = RoundPlayer.objects.create(player=player,
                                        the_round=r,
                                        score=float(row['score%d' % r_num]))
        # And a GamePlayer
        gp = GamePlayer.objects.create(player=player,
                                       game=Game.objects.get(the_round=r,
                                                             name='R%dG%c' % (r_num, row['game%d' % r_num])),
                                       power=GreatPower.objects.get(abbreviation=row['power%d' % r_num]),
                                       score=float(row['score%d' % r_num]))


def import_dixie_csv(csvfilename, start_date, end_date, name='DixieCon'):
    """
    Import a CSV file containing results from Dixie

    Given the name of a CSV file containing DixeCon results,
    create the Tournament with all the data provided.
    Probably loads of assumptions...
    """
    with open(csvfilename) as csvfile:
        cols = ['first', 'last', 'round1', 'game1', 'power1', 'score1', 'round2', 'game2', 'power2', 'score2', 'round3', 'game3', 'power3', 'score3', 'blank', 'total']
        reader = csv.DictReader(csvfile, fieldnames=cols)
        # Create the tournament
        a_set = GameSet.objects.first()
        t = Tournament.objects.create(name=name,
                                      start_date=start_date,
                                      end_date=end_date,
                                      round_scoring_system=NO_SCORING_SYSTEM_STR,
                                      tournament_scoring_system='Sum best 2 rounds')
        # Create 3 rounds
        for r_num in range(1, 4):
            r = Round.objects.create(tournament=t,
                                     scoring_system='Dixie',
                                     dias=False,
                                     start=datetime.combine(t.start_date, time(hour=r_num, tzinfo=timezone.utc)))
            # Create 4 Games
            for g_num in range(1,5):
                g = Game.objects.create(name=_generate_game_name(r_num, g_num),
                                        the_round=r,
                                        the_set=a_set,
                                        is_finished=True)
        for row in reader:
            # Skip rows with no player name
            if not row['first'].lstrip() or not row['first'].isprintable():
                continue
            try:
                p = Player.objects.get(first_name=row['first'], last_name=row['last'])
            except Player.DoesNotExist:
                first=row['first']
                last=row['last']
                print(f'Unable to find player "{first} {last}"')
                continue
            # Create a TournamentPlayer
            tp = TournamentPlayer.objects.create(player=p,
                                                 tournament=t,
                                                 score=float(row['total']))
            # Create RoundPlayer and GamePlayer for each applicable Round
            for r_num in range(1, 4):
                _import_dixie_round(r_num, p, t, row)
    add_best_country_awards_for_tournament(t, False)

def add_wdr_player_ids(csv_filename, dry_run=False):
    """
    Add wdr_player_id attributes to Players

    csv_filename is the name of a CSV file giving the mapping
      columns are:
        id - wdr_player_id
        player_wdd_id - wdd_player_id
        player_name - player's first name
        player_surname - player's last name
    """
    with open(csv_filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                p = Player.objects.get(wdd_player_id=int(row['player_wdd_id']))
            except Player.DoesNotExist:
                continue
            print(f'Setting wdr_player_id for {p.first_name} {p.last_name} to {row["id"]}')
            p.wdr_player_id = row['id']
            if not dry_run:
                p.save(update_fields=['wdr_player_id'])

def add_wdr_tournament_ids(csv_filename, dry_run=False):
    """
    Add wdr_tournament_id attributes to Tournaments, PlayerTournamentRankings,
    PlayerGameResults, and PlayerAwards

    csv_filename is the name of a CSV file giving the mapping
      columns are:
        id - wdr_tournament_id
        tournament_wdd_id - wdd_tournament_id
        tournament_name - tournament name
    """
    with open(csv_filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['tournament_wdd_id'] != -1:
                for t in Tournament.objects.filter(wdd_tournament_id=int(row['tournament_wdd_id'])):
                    print(f'Setting wdr_tournament_id for {t} to {row["id"]}')
                    t.wdr_tournament_id = row['id']
                    if not dry_run:
                        t.save(update_fields=['wdr_tournament_id'])
                for ptr in PlayerTournamentRanking.objects.filter(wdd_tournament_id=int(row['tournament_wdd_id'])):
                    print(f'Setting wdr_tournament_id for {ptr} to {row["id"]}')
                    ptr.wdr_tournament_id = row['id']
                    if not dry_run:
                        ptr.save(update_fields=['wdr_tournament_id'])
                for pgr in PlayerGameResult.objects.filter(wdd_tournament_id=int(row['tournament_wdd_id'])):
                    print(f'Setting wdr_tournament_id for {pgr} to {row["id"]}')
                    pgr.wdr_tournament_id = row['id']
                    if not dry_run:
                        pgr.save(update_fields=['wdr_tournament_id'])
                for pa in PlayerAward.objects.filter(wdd_tournament_id=int(row['tournament_wdd_id'])):
                    print(f'Setting wdr_tournament_id for {pa} to {row["id"]}')
                    pa.wdr_tournament_id = row['id']
                    if not dry_run:
                        pa.save(update_fields=['wdr_tournament_id'])

def check_wdd_ids():
    """
    Where we have WDR ids, we can use the WDR to double-check WDD ids
    """
    for p in Player.objects.filter(wdr_player_id__isnull=False).all():
        bg = WDRBackground(p.wdr_player_id)
        wdd_id = bg.wdd_id()
        if p.wdd_player_id and wdd_id and (p.wdd_player_id != wdd_id):
            # We have a different WDD id
            print(f'{p.name} ({p.id}) has WDD id {p.wdd_player_id} here but {wdd_id} in the WDR')
        elif (not p.wdd_player_id) and wdd_id:
            printf(f'{p.name} ({p.id}) has no WDD here but {wdd_id} in the WDR')

def upcoming_rounds(num_days=45, include_unpublished=False):
    """
    Print a list of tournament rounds for the next few weeks

    num_days specifies how many days ahead to look
    include_unpublished says whether to include unpublished tournaments
    """
    current_tz = timezone.get_current_timezone()
    today = timezone.now()
    end_date = today + timedelta(days=num_days)
    for r in Round.objects.filter(is_finished=False).filter(start__range=[today, end_date]):
        if include_unpublished or r.tournament.is_published:
            print(f'{r.start.astimezone(current_tz)} {r}')
