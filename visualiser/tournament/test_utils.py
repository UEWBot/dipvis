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
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone as django_timezone

from tournament.diplomacy import GameSet, GreatPower
from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               Award, DrawSecrecy, Game, GamePlayer, Round,
                               RoundPlayer, Tournament, TournamentPlayer)
from tournament.players import Player, WDDPlayer
from tournament.utils import (archive_tournaments, map_to_backstabbr_power,
                              check_wdd_player_ids,
                              clean_duplicate_player,
                              find_players_missing_wdd_ids,
                              nuke_invalid_email,
                              player_emails,
                              upcoming_rounds,
                              _power_award_to_gameplayers)


class UtilsTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

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

    def test_archive_tournaments(self):
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

    def test_archive_tournaments_dry_run(self):
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
        tp.awards.add(award)
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