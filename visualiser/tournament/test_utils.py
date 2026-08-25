# Diplomacy Tournament Visualiser
# Copyright (C) 2026 Chris Brand <chris.carter.brand@gmail.com>
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

from datetime import timedelta
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone as django_timezone

from tournament.diplomacy import GameSet, GreatPower
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               Award, AwardRecipient, CentreCount, DrawSecrecy,
                               Game, GamePlayer, Round,
                               RoundPlayer, Tournament, TournamentAward,
                               TournamentPlayer)
from tournament.players import Player, PlayerEventRanking, WDDPlayer
from tournament.utils import (archive_tournaments, map_to_backstabbr_power,
                              add_wdr_tournament_ids,
                              add_missing_player_wdr_ids,
                              check_wdd_player_ids,
                              clean_duplicate_player,
                              find_tournaments_missing_wdd_ids,
                              find_tournaments_missing_wdr_ids,
                              find_players_missing_wdd_ids,
                              find_users_without_players,
                              nuke_invalid_email,
                              player_emails,
                              populate_missed_years,
                              upcoming_rounds,
                              _power_award_to_gameplayers)


class UtilsTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    def _write_wdr_tournament_mapping_csv(self, rows):
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        try:
            tmp.write('id,tournament_wdd_id,tournament_name\n')
            for row in rows:
                tmp.write(f"{row['id']},{row['tournament_wdd_id']},{row['tournament_name']}\n")
            return tmp.name
        finally:
            tmp.close()

    def test_map_to_backstabbr_power(self):
        from tournament.diplomacy import GreatPower

        gp = GreatPower.objects.get(abbreviation='A')
        power = map_to_backstabbr_power(gp)
        self.assertEqual(power[0], 'A')

    def test_map_to_backstabbr_power_invalid(self):
        fake_power = SimpleNamespace(abbreviation='Z')
        self.assertRaises(ValueError, map_to_backstabbr_power, fake_power)

    def test_player_emails(self):
        today = django_timezone.now().date()
        t = Tournament.objects.create(name='util-email-test',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        p1 = Player.objects.create(first_name='Uma',
                                   last_name='UtilsOne',
                                   email='uma1@example.com')
        p2 = Player.objects.create(first_name='Uri',
                                   last_name='UtilsTwo',
                                   email='uri2@example.com')
        TournamentPlayer.objects.create(player=p1, tournament=t)
        TournamentPlayer.objects.create(player=p2, tournament=t)

        emails = player_emails(t)
        self.assertCountEqual(emails, ['uma1@example.com', 'uri2@example.com'])
        # Cleanup
        t.delete()
        p1.delete()
        p2.delete()

    def test_nuke_invalid_email(self):
        p = Player.objects.create(first_name='Nina',
                                  last_name='Nuked',
                                  email='bad@example.com')
        nuke_invalid_email('bad@example.com')
        p.refresh_from_db()
        self.assertEqual(p.email, '')
        # Cleanup
        p.delete()

    def test_nuke_invalid_email_missing_player_raises(self):
        self.assertRaises(Player.DoesNotExist,
                          nuke_invalid_email,
                          'missing@example.com')

    @patch('builtins.print')
    def test_archive_tournaments(self, mock_print):
        today = django_timezone.now().date()
        t_archived = Tournament.objects.create(name='util-archive-target',
                                               start_date=today - timedelta(days=2),
                                               end_date=today - timedelta(days=1),
                                               round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                               tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                               draw_secrecy=DrawSecrecy.SECRET,
                                               is_published=True,
                                               editable=True)
        t_unpublished = Tournament.objects.create(name='util-archive-unpub',
                                                  start_date=today - timedelta(days=2),
                                                  end_date=today - timedelta(days=1),
                                                  round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                                  tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                  draw_secrecy=DrawSecrecy.SECRET,
                                                  is_published=False,
                                                  editable=True)
        t_future = Tournament.objects.create(name='util-archive-future',
                                             start_date=today,
                                             end_date=today + timedelta(days=5),
                                             round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                             tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                             draw_secrecy=DrawSecrecy.SECRET,
                                             is_published=True,
                                             editable=True)

        archive_tournaments(dry_run=False)

        mock_print.assert_called_with(f'Archiving util-archive-target {today.year}')

        t_archived.refresh_from_db()
        t_unpublished.refresh_from_db()
        t_future.refresh_from_db()
        self.assertFalse(t_archived.editable)
        self.assertTrue(t_unpublished.editable)
        self.assertTrue(t_future.editable)
        # Cleanup
        t_archived.delete()
        t_unpublished.delete()
        t_future.delete()

    @patch('builtins.print')
    def test_archive_tournaments_dry_run(self, mock_print):
        today = django_timezone.now().date()
        t = Tournament.objects.create(name='util-archive-dry-run',
                                      start_date=today - timedelta(days=2),
                                      end_date=today - timedelta(days=1),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET,
                                      is_published=True,
                                      editable=True)

        archive_tournaments(dry_run=True)

        mock_print.assert_called_with(f'Archiving util-archive-dry-run {today.year}')

        t.refresh_from_db()
        self.assertTrue(t.editable)
        # Cleanup
        t.delete()

    def test_power_award_to_gameplayers(self):
        today = django_timezone.now().date()
        t = Tournament.objects.create(name='util-award-gps',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        r = Round.objects.create(tournament=t,
                                 scoring_system=R_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 is_finished=False,
                                 start=django_timezone.now())
        a_set = GameSet.objects.first()
        g = Game.objects.create(name='U1',
                                the_round=r,
                    the_set=a_set,
                                started_at=r.start)
        power = GreatPower.objects.get(abbreviation='A')
        award = Award.objects.create(name='Best Austria Util',
                                     description='Best Austria for util test',
                                     power=power)
        p = Player.objects.create(first_name='Amy',
                                  last_name='Awarded')
        tp = TournamentPlayer.objects.create(player=p, tournament=t)
        tournament_award = TournamentAward.objects.create(tournament=t, award=award)
        AwardRecipient.objects.create(tournament_award=tournament_award, tournament_player=tp)
        RoundPlayer.objects.create(player=p, the_round=r)
        gp = GamePlayer.objects.create(player=p,
                                       game=g,
                                       power=power,
                                       score=1.5)

        gps = _power_award_to_gameplayers(t, award)
        self.assertEqual(gps, [gp])
        # Cleanup
        t.delete()
        award.delete()
        p.delete()

    def test_upcoming_rounds_published_only(self):
        now = django_timezone.now()
        t_pub = Tournament.objects.create(name='util-round-pub',
                                          start_date=now.date(),
                                          end_date=now.date(),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET,
                                          is_published=True)
        t_unpub = Tournament.objects.create(name='util-round-unpub',
                                            start_date=now.date(),
                                            end_date=now.date(),
                                            round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                            tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                            draw_secrecy=DrawSecrecy.SECRET,
                                            is_published=False)
        Round.objects.create(tournament=t_pub,
                             scoring_system=R_SCORING_SYSTEMS[0].name,
                             dias=True,
                             is_finished=False,
                             start=now + timedelta(days=1))
        Round.objects.create(tournament=t_unpub,
                             scoring_system=R_SCORING_SYSTEMS[0].name,
                             dias=True,
                             is_finished=False,
                             start=now + timedelta(days=1))

        with patch('builtins.print') as mock_print:
            upcoming_rounds(num_days=2, include_unpublished=False)
        self.assertEqual(mock_print.call_count, 1)
        # Cleanup
        t_pub.delete()
        t_unpub.delete()

    def test_upcoming_rounds_include_unpublished(self):
        now = django_timezone.now()
        t_pub = Tournament.objects.create(name='util-round-pub-all',
                                          start_date=now.date(),
                                          end_date=now.date(),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET,
                                          is_published=True)
        t_unpub = Tournament.objects.create(name='util-round-unpub-all',
                                            start_date=now.date(),
                                            end_date=now.date(),
                                            round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                            tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                            draw_secrecy=DrawSecrecy.SECRET,
                                            is_published=False)
        Round.objects.create(tournament=t_pub,
                             scoring_system=R_SCORING_SYSTEMS[0].name,
                             dias=True,
                             is_finished=False,
                             start=now + timedelta(days=1))
        Round.objects.create(tournament=t_unpub,
                             scoring_system=R_SCORING_SYSTEMS[0].name,
                             dias=True,
                             is_finished=False,
                             start=now + timedelta(days=1))

        with patch('builtins.print') as mock_print:
            upcoming_rounds(num_days=2, include_unpublished=True)
        self.assertEqual(mock_print.call_count, 2)
        # Cleanup
        t_pub.delete()
        t_unpub.delete()

    def test_find_players_missing_wdd_ids(self):
        now = django_timezone.now()
        t = Tournament.objects.create(name='util-find-missing-wdd',
                                      start_date=now.date(),
                                      end_date=now.date(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET,
                                      is_published=True,
                                      wdd_tournament_id=12345)
        r = Round.objects.create(tournament=t,
                                 scoring_system=R_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 is_finished=False,
                                 start=now)
        p_missing = Player.objects.create(first_name='Mia',
                                          last_name='MissingWdd')
        p_has_wdd = Player.objects.create(first_name='Wade',
                                          last_name='WithWdd')
        p_no_round = Player.objects.create(first_name='Rita',
                                           last_name='RegisteredOnly')
        TournamentPlayer.objects.create(player=p_missing, tournament=t)
        TournamentPlayer.objects.create(player=p_has_wdd, tournament=t)
        TournamentPlayer.objects.create(player=p_no_round, tournament=t)
        RoundPlayer.objects.create(player=p_missing, the_round=r)
        RoundPlayer.objects.create(player=p_has_wdd, the_round=r)
        WDDPlayer.objects.create(wdd_player_id=987654, player=p_has_wdd)

        with patch('builtins.print') as mock_print:
            find_players_missing_wdd_ids()
        self.assertEqual(mock_print.call_count, 1)
        self.assertEqual(str(mock_print.call_args_list[0].args[0]), str(p_missing))
        # Cleanup
        t.delete()
        p_missing.delete()
        p_has_wdd.delete()
        p_no_round.delete()

    def test_find_users_without_players(self):
        u1 = User.objects.create_user(username='player')
        u2 = User.objects.create_user(username='non-player')
        u3 = User.objects.create_user(username='inactive')
        p1 = Player.objects.create(first_name='Uma',
                                   last_name='UtilsOne',
                                   email='uma1@example.com')
        p2 = Player.objects.create(first_name='Uri',
                                   last_name='UtilsTwo',
                                   email='uri2@example.com')
        p3 = Player.objects.create(first_name='Uri',
                                   last_name='UtilsThree',
                                   email='ursula3@example.com')
        p1.user = u1
        p1.save()
        p3.user = u3
        p3.save()

        with patch('builtins.print') as mock_print:
            find_users_without_players()
        self.assertEqual(mock_print.call_count, 1)
        self.assertEqual(str(mock_print.call_args_list[0].args[0]), str(u2))
        # Cleanup
        p3.delete()
        p2.delete()
        p1.delete()
        u3.delete()
        u2.delete()
        u1.delete()

    @patch('builtins.print')
    @patch('tournament.utils.wdr_tournament_as_json')
    def test_add_missing_player_wdr_ids_sets_matching_player_id(self, mock_wdr_json, mock_print):
        now = django_timezone.now()
        t = Tournament.objects.create(name='util-missing-wdr',
                                      start_date=now.date(),
                                      end_date=now.date(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET,
                                      is_published=True,
                                      wdr_tournament_id=321)
        p_match = Player.objects.create(first_name='Match',
                                        last_name='Player')
        p_zero = Player.objects.create(first_name='Zero',
                                       last_name='Player')
        TournamentPlayer.objects.create(player=p_match, tournament=t, score=12.5)
        TournamentPlayer.objects.create(player=p_zero, tournament=t, score=0.0)
        mock_wdr_json.return_value = {
            'tournament_classifications': [
                {
                    'player_id': 111,
                    'player_full_name': 'Match Player',
                    'player_score': 12.5,
                    'player_rank': 1,
                },
                {
                    'player_id': 222,
                    'player_full_name': 'Zero Player',
                    'player_score': 0.0,
                    'player_rank': 2,
                },
            ]
        }

        add_missing_player_wdr_ids(dry_run=False)

        mock_print.assert_called_with(f'Adding WDR id 111 to Match Player (from util-missing-wdr {now.year})')

        p_match.refresh_from_db()
        p_zero.refresh_from_db()
        self.assertEqual(p_match.wdr_player_id, 111)
        self.assertIsNone(p_zero.wdr_player_id)
        # Cleanup
        t.delete()
        p_match.delete()
        p_zero.delete()

    @patch('builtins.print')
    def test_add_wdr_tournament_ids_updates_tournament_and_event_rankings(self, mock_print):
        today = django_timezone.now().date()
        t = Tournament.objects.create(name='util-add-wdr-tournament-id',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET,
                                      wdd_tournament_id=2222,
                                      wdr_tournament_id=None)
        p = Player.objects.create(first_name='Tori',
                                  last_name='TournamentId')
        ptr = PlayerEventRanking.objects.create(player=p,
                                                event_name='util-add-wdr-id-event',
                                                date=today,
                                                wdd_tournament_id=2222,
                                                wdr_tournament_id=None)
        csv_file = self._write_wdr_tournament_mapping_csv([
            {'id': 7777, 'tournament_wdd_id': 2222, 'tournament_name': 'util-add-wdr-tournament-id'},
            {'id': 8888, 'tournament_wdd_id': -1, 'tournament_name': 'ignored-row'},
        ])

        try:
            add_wdr_tournament_ids(csv_file, dry_run=False)
            mock_print.assert_any_call(f'Setting wdr_tournament_id for util-add-wdr-tournament-id {today.year} to 7777')
            mock_print.assert_any_call(f'Setting wdr_tournament_id for Tori TournamentId was unranked at util-add-wdr-id-event in {today.year} to 7777')
            t.refresh_from_db()
            ptr.refresh_from_db()
            self.assertEqual(7777, t.wdr_tournament_id)
            self.assertEqual(7777, ptr.wdr_tournament_id)
        finally:
            os.unlink(csv_file)
            t.delete()
            p.delete()

    @patch('builtins.print')
    def test_add_wdr_tournament_ids_dry_run_does_not_update(self, mock_print):
        today = django_timezone.now().date()
        t = Tournament.objects.create(name='util-add-wdr-tournament-id-dry',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET,
                                      wdd_tournament_id=3333,
                                      wdr_tournament_id=None)
        p = Player.objects.create(first_name='Dora',
                                  last_name='DryRun')
        ptr = PlayerEventRanking.objects.create(player=p,
                                                event_name='util-add-wdr-id-event-dry',
                                                date=today,
                                                wdd_tournament_id=3333,
                                                wdr_tournament_id=None)
        csv_file = self._write_wdr_tournament_mapping_csv([
            {'id': 9999, 'tournament_wdd_id': 3333, 'tournament_name': 'util-add-wdr-tournament-id-dry'},
        ])

        try:
            add_wdr_tournament_ids(csv_file, dry_run=True)
            mock_print.assert_any_call(f'Setting wdr_tournament_id for util-add-wdr-tournament-id-dry {today.year} to 9999')
            mock_print.assert_any_call(f'Setting wdr_tournament_id for Dora DryRun was unranked at util-add-wdr-id-event-dry in {today.year} to 9999')
            t.refresh_from_db()
            ptr.refresh_from_db()
            self.assertIsNone(t.wdr_tournament_id)
            self.assertIsNone(ptr.wdr_tournament_id)
        finally:
            os.unlink(csv_file)
            t.delete()
            p.delete()

    def test_find_tournaments_missing_wdd_ids_finished_only(self):
        today = django_timezone.now().date()
        t_finished_missing = Tournament.objects.create(name='util-missing-wdd-finished',
                                                       start_date=today,
                                                       end_date=today,
                                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                       draw_secrecy=DrawSecrecy.SECRET,
                                                       is_finished=True,
                                                       wdd_tournament_id=None)
        t_unfinished_missing = Tournament.objects.create(name='util-missing-wdd-unfinished',
                                                         start_date=today,
                                                         end_date=today,
                                                         round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                                         tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                         draw_secrecy=DrawSecrecy.SECRET,
                                                         is_finished=False,
                                                         wdd_tournament_id=None)
        Tournament.objects.create(name='util-has-wdd-finished',
                                  start_date=today,
                                  end_date=today,
                                  round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                  tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                  draw_secrecy=DrawSecrecy.SECRET,
                                  is_finished=True,
                                  wdd_tournament_id=999)

        with patch('builtins.print') as mock_print:
            find_tournaments_missing_wdd_ids()

        self.assertEqual(mock_print.call_count, 1)
        self.assertEqual(str(mock_print.call_args_list[0].args[0]), str(t_finished_missing))
        # Cleanup
        t_finished_missing.delete()
        t_unfinished_missing.delete()

    def test_find_tournaments_missing_wdr_ids_finished_only(self):
        today = django_timezone.now().date()
        t_finished_missing = Tournament.objects.create(name='util-missing-wdr-finished',
                                                       start_date=today,
                                                       end_date=today,
                                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                       draw_secrecy=DrawSecrecy.SECRET,
                                                       is_finished=True,
                                                       wdr_tournament_id=None)
        t_unfinished_missing = Tournament.objects.create(name='util-missing-wdr-unfinished',
                                                         start_date=today,
                                                         end_date=today,
                                                         round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                                         tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                         draw_secrecy=DrawSecrecy.SECRET,
                                                         is_finished=False,
                                                         wdr_tournament_id=None)
        Tournament.objects.create(name='util-has-wdr-finished',
                                  start_date=today,
                                  end_date=today,
                                  round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                  tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                  draw_secrecy=DrawSecrecy.SECRET,
                                  is_finished=True,
                                  wdr_tournament_id=999)

        with patch('builtins.print') as mock_print:
            find_tournaments_missing_wdr_ids()

        self.assertEqual(mock_print.call_count, 1)
        self.assertEqual(str(mock_print.call_args_list[0].args[0]), str(t_finished_missing))
        # Cleanup
        t_finished_missing.delete()
        t_unfinished_missing.delete()

    @patch('builtins.print')
    @patch('tournament.utils._sc_counts_to_cc')
    @patch('tournament.utils._bs_ownerships_to_sco')
    def test_populate_missed_years_fills_missing_year(self, mock_to_sco, mock_to_cc, mock_print):
        now = django_timezone.now()
        t = Tournament.objects.create(name='util-populate-years',
                                      start_date=now.date(),
                                      end_date=now.date(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        r = Round.objects.create(tournament=t,
                                 scoring_system=R_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 is_finished=False,
                                 start=now)
        g = Game.objects.create(name='PopulateYearsGame',
                                the_round=r,
                                the_set=GameSet.objects.first(),
                                started_at=r.start,
                                external_url='https://www.backstabbr.com/game/test')
        for power in GreatPower.objects.order_by()[:7]:
            CentreCount.objects.create(power=power,
                                       game=g,
                                       year=1901,
                                       count=3)

        bg = SimpleNamespace(
            year=1903,
            sc_ownership=[('PAR', 'F')],
            turn_details=lambda season, year: ({'A': 3}, None, {'PAR': 'F'})
        )

        with patch.object(g, 'backstabbr_game', return_value=bg):
            with patch.object(g, 'create_or_update_sc_counts_from_ownerships') as mock_update:
                populate_missed_years(g, dry_run=False)

        mock_print.assert_called_with('Reading results for 1902')
        mock_to_sco.assert_called_once_with(g, 1902, {'PAR': 'F'})
        mock_update.assert_called_once_with(1902)
        mock_to_cc.assert_not_called()
        # Cleanup
        t.delete()

    def test_populate_missed_years_dry_run_skips_updates(self):
        now = django_timezone.now()
        t = Tournament.objects.create(name='util-populate-years-dry',
                                      start_date=now.date(),
                                      end_date=now.date(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        r = Round.objects.create(tournament=t,
                                 scoring_system=R_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 is_finished=False,
                                 start=now)
        g = Game.objects.create(name='PopulateYearsDryRunGame',
                                the_round=r,
                                the_set=GameSet.objects.first(),
                                started_at=r.start,
                                external_url='https://www.backstabbr.com/game/test2')
        bg = SimpleNamespace(year=1902)

        with patch.object(g, 'backstabbr_game', return_value=bg):
            with patch('builtins.print') as mock_print:
                populate_missed_years(g, dry_run=True)

        mock_print.assert_called_with('Reading results for 1901')
        # Cleanup
        t.delete()

    @patch('tournament.utils.add_missing_wdd_player_ids')
    def test_check_wdd_player_ids(self, mock_add_missing):
        check_wdd_player_ids()
        mock_add_missing.assert_called_once_with(dry_run=True)

    def test_clean_duplicate_player_first_name_mismatch(self):
        keep_player = Player.objects.create(first_name='Alex',
                                            last_name='Merge')
        del_player = Player.objects.create(first_name='Blake',
                                           last_name='Merge')

        with patch('builtins.print') as mock_print:
            clean_duplicate_player(del_player, keep_player, dry_run=True)
        mock_print.assert_called_once_with("Player first names don't match!")
        # Cleanup
        keep_player.delete()
        del_player.delete()

    def test_clean_duplicate_player_del_player_email_guard(self):
        keep_player = Player.objects.create(first_name='Casey',
                                            last_name='Merge',
                                            email='keep@example.com')
        del_player = Player.objects.create(first_name='Casey',
                                           last_name='Merge',
                                           email='del@example.com')

        with patch('builtins.print') as mock_print:
            clean_duplicate_player(del_player, keep_player, dry_run=True)
        mock_print.assert_called_once_with('Player to delete has an email address!')
        # Cleanup
        keep_player.delete()
        del_player.delete()

    def test_clean_duplicate_player_wdd_id_guard(self):
        keep_player = Player.objects.create(first_name='Robin',
                                            last_name='Merge')
        del_player = Player.objects.create(first_name='Robin',
                                           last_name='Merge')
        WDDPlayer.objects.create(wdd_player_id=777001, player=del_player)

        with patch('builtins.print') as mock_print:
            clean_duplicate_player(del_player, keep_player, dry_run=True)
        mock_print.assert_called_once_with('Player to delete has a WDD player id!')
        # Cleanup
        keep_player.delete()
        del_player.delete()

    def test_clean_duplicate_player_backstabbr_username_guard(self):
        keep_player = Player.objects.create(first_name='Taylor',
                                            last_name='Merge',
                                            backstabbr_username='')
        del_player = Player.objects.create(first_name='Taylor',
                                           last_name='Merge',
                                           backstabbr_username='delete-me')

        with patch('builtins.print') as mock_print:
            clean_duplicate_player(del_player, keep_player, dry_run=True)
        mock_print.assert_called_once_with('Player to delete has a backstabbr username!')
        # Cleanup
        keep_player.delete()
        del_player.delete()

    def test_clean_duplicate_player_backstabbr_profile_url_guard(self):
        keep_player = Player.objects.create(first_name='Jordan',
                                            last_name='Merge',
                                            backstabbr_profile_url='')
        del_player = Player.objects.create(first_name='Jordan',
                                           last_name='Merge',
                                           backstabbr_profile_url='https://backstabbr.com/u/delete-me')

        with patch('builtins.print') as mock_print:
            clean_duplicate_player(del_player, keep_player, dry_run=True)
        mock_print.assert_called_once_with('Player to delete has a backstabbr profile URL!')
        # Cleanup
        keep_player.delete()
        del_player.delete()

    def test_clean_duplicate_player_user_account_guard(self):
        keep_player = Player.objects.create(first_name='Morgan',
                                            last_name='Merge')
        user = User.objects.create_user(username='duplicate-clean-user')
        del_player = Player.objects.create(first_name='Morgan',
                                           last_name='Merge',
                                           user=user)

        with patch('builtins.print') as mock_print:
            clean_duplicate_player(del_player, keep_player, dry_run=True)
        mock_print.assert_called_once_with('Player to delete has an account!')
        # Cleanup
        keep_player.delete()
        del_player.delete()
        user.delete()

    def test_clean_duplicate_player_moves_related_rows_when_not_dry_run(self):
        now = django_timezone.now()
        keep_player = Player.objects.create(first_name='Sam',
                                            last_name='Merge',
                                            email='same@example.com')
        del_player = Player.objects.create(first_name='Sam',
                                           last_name='Merge',
                                           email='same@example.com')
        t = Tournament.objects.create(name='util-clean-duplicate',
                                      start_date=now.date(),
                                      end_date=now.date(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        r = Round.objects.create(tournament=t,
                                 scoring_system=R_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 is_finished=False,
                                 start=now)
        g = Game.objects.create(name='DuplicateMoveGame',
                                the_round=r,
                                the_set=GameSet.objects.first(),
                                started_at=r.start)
        tp = TournamentPlayer.objects.create(player=del_player, tournament=t)
        rp = RoundPlayer.objects.create(player=del_player, the_round=r)
        gp = GamePlayer.objects.create(player=del_player,
                                       game=g,
                                       power=GreatPower.objects.get(abbreviation='A'))

        with patch('builtins.print') as mock_print:
            clean_duplicate_player(del_player, keep_player, dry_run=False)

        tp.refresh_from_db()
        rp.refresh_from_db()
        gp.refresh_from_db()
        self.assertEqual(tp.player, keep_player)
        self.assertEqual(rp.player, keep_player)
        self.assertEqual(gp.player, keep_player)
        self.assertTrue(any('ready to delete from the admin' in c.args[0] for c in mock_print.call_args_list))
        # Cleanup
        t.delete()
        keep_player.delete()
        del_player.delete()

    def test_clean_duplicate_player_last_name_mismatch(self):
        keep_player = Player.objects.create(first_name='Alex',
                                            last_name='Keeper')
        del_player = Player.objects.create(first_name='Alex',
                                           last_name='Different')

        with patch('builtins.print') as mock_print:
            clean_duplicate_player(del_player, keep_player, dry_run=True)
        mock_print.assert_called_once_with("Player last names don't match!")
        # Cleanup
        keep_player.delete()
        del_player.delete()

    def test_clean_duplicate_player_dry_run_no_issues(self):
        keep_player = Player.objects.create(first_name='Jamie',
                                            last_name='Merge',
                                            email='same@example.com')
        del_player = Player.objects.create(first_name='Jamie',
                                           last_name='Merge',
                                           email='same@example.com')

        with patch('builtins.print') as mock_print:
            clean_duplicate_player(del_player, keep_player, dry_run=True)
        mock_print.assert_called_once_with('No issues found')
        # Cleanup
        keep_player.delete()
        del_player.delete()
